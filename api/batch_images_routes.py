# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Batch Image Inspection: 10-50 photos -> folder -> parallel Parliament -> report
# ==============================================================================

import asyncio
import csv
import io
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.auth_routes import get_current_user, get_optional_current_user
from core.context import ExecutionContext
from core.orchestrator import orchestrator
from db.database import SessionLocal, get_db
from db.models import AuditLogEntry, FolderRecord, JobRecord, User

router = APIRouter(prefix="/api/v2/batch/images", tags=["Batch Image Inspection"])

MAX_IMAGES_PER_BATCH = 50
MAX_BYTES_PER_IMAGE = 12 * 1024 * 1024  # decoded-size guard (data URL length is checked)

# How many photos run through the full 32-vote Parliament at the same time.
# Each photo triggers many provider calls, so this (not the 500-slot pool) is the
# real throughput limiter. Tune with BATCH_IMAGE_CONCURRENCY in .env.
IMAGE_CONCURRENCY = max(1, int(os.getenv("BATCH_IMAGE_CONCURRENCY", "20")))

CREDIT_COST = {"Fast": 1, "Standard": 5, "Deep": 20}

IMAGE_BATCH_REGISTRY: Dict[str, Dict[str, Any]] = {}
IMAGE_BATCH_TTL_SECONDS = 3600


def _evict_stale_image_batches() -> None:
    """Evicts completed/failed image batches older than TTL to bound RAM usage."""
    now = time.time()
    stale = [
        bid for bid, b in list(IMAGE_BATCH_REGISTRY.items())
        if b.get("status") in ("COMPLETED", "FAILED")
        and (now - b.get("start_ts", now)) > IMAGE_BATCH_TTL_SECONDS
    ]
    for bid in stale:
        IMAGE_BATCH_REGISTRY.pop(bid, None)


def _sanitize_csv_cell(val: Any) -> Any:
    """Prevents CSV formula injection in spreadsheet applications."""
    if isinstance(val, str) and val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
        # Allow plain negative numbers like "-12.5"
        if val[0] == "-" and val[1:].replace(".", "", 1).isdigit():
            return val
        return f"'{val}"
    return val


class BatchImageItem(BaseModel):
    name: Optional[str] = Field(default="photo.jpg", max_length=500)
    data: Optional[str] = Field(default=None, description="Image as data URL (data:image/...;base64,...)")
    image_data: Optional[str] = Field(default=None, description="Image as data URL fallback")


class CriterionIn(BaseModel):
    name: Optional[str] = Field(default="Item Attribute", max_length=255)
    type: Optional[str] = Field(default="Free Text")
    range: Optional[str] = Field(default="")


class ImageBatchRequest(BaseModel):
    name: Optional[str] = Field(default="Image Batch", max_length=500)
    folder_name: Optional[str] = Field(default="General Workspace", max_length=500)
    depth_tier: Optional[str] = Field(default="Standard")
    criteria: Optional[List[CriterionIn]] = Field(default_factory=list)
    images: Optional[List[BatchImageItem]] = Field(default_factory=list)


def _public_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Item view without the heavy image payload. Uses list copy to avoid concurrent mutation."""
    return {k: v for k, v in list(item.items()) if k != "image_data"}


async def _run_batch(batch_id: str, user_id: str, user_email: str, depth: str, criteria: List[Dict[str, Any]]):
    state = IMAGE_BATCH_REGISTRY[batch_id]
    # Auto-pacing: spaces provider calls under each provider's rate limit so the batch
    # finishes completely (slower) instead of losing votes to HTTP 429.
    from core.provider_pacer import activate_for_current_task, pacing_enabled
    state["paced"] = activate_for_current_task()
    # On free tier, enforce strictly serialized (concurrency=1) queue to prevent burst flooding
    # 40+ simultaneous LLM calls which trips the 75s feature timeout circuit breaker.
    eff_concurrency = 1 if pacing_enabled() else max(1, int(os.getenv("BATCH_IMAGE_CONCURRENCY", "20")))
    state["concurrency"] = eff_concurrency
    sem = asyncio.Semaphore(eff_concurrency)
    cost_each = CREDIT_COST.get(depth, 5)
    effective_depth = depth
    if depth == "Fast" and (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")):
        effective_depth = "Standard"

    async def _one(item: Dict[str, Any]):
        async with sem:
            item["status"] = "RUNNING"
            started = time.time()
            try:
                ctx = ExecutionContext(
                    tenant_id=f"user_{user_id}",
                    depth_tier=effective_depth,
                    input_payload={
                        "text": item["name"],
                        "modality": "VISION",
                        "image": item["image_data"],
                        "criteria": criteria,
                    },
                )
                final = await orchestrator.run_pipeline(ctx)
                crit = final.metadata.get("criteria_results") or []
                bad = (not crit) or any((not c.get("value")) or c.get("value") == "PROVIDER_UNAVAILABLE" for c in crit)
                if bad:
                    # Honest failure: never invent labels when providers did not answer.
                    item["status"] = "FAILED"
                    item["error"] = "Parliament returned no valid consensus (providers unavailable or rate limited)."
                else:
                    unified = final.metadata.get("unified_output", {}) or {}
                    consensus = unified.get("consensus", {}) or {}
                    overall_conf = float(final.metadata.get("overall_criteria_confidence") or 0.0)
                    has_anomaly = any(c.get("anomaly", False) for c in crit)

                    if has_anomaly or (overall_conf > 0 and overall_conf < 50.0):
                        computed_decision = "REJECTED"
                    elif overall_conf >= 90.0:
                        computed_decision = "CONFIRMED"
                    elif overall_conf >= 70.0:
                        computed_decision = "PARTIAL"
                    else:
                        cand_label = consensus.get("label") or "UNKNOWN"
                        computed_decision = "CONFIRMED" if "UNKNOWN" in cand_label else cand_label

                    item["status"] = "COMPLETED"
                    item["criteria_results"] = crit
                    item["overall_confidence"] = overall_conf
                    item["decision"] = computed_decision
                    item["votes"] = f"{consensus.get('affirmative_votes', 0)}/32"
                    item["trace_id"] = final.trace_id
                    item["lineage_hash"] = (final.metadata.get("final_lineage_hash") or "")[:16]
            except Exception as exc:  # noqa: BLE001
                item["status"] = "FAILED"
                item["error"] = f"{type(exc).__name__}: {exc}"[:300]
            finally:
                item["seconds"] = round(time.time() - started, 1)
                state["done"] += 1
                if item["status"] == "FAILED":
                    state["failed"] += 1
                state["progress_pct"] = round(state["done"] / state["total"] * 100.0, 1)

    await asyncio.gather(*[_one(it) for it in state["items"]])

    # Persist results + reconcile pre-authorized credits (refund any failed photos).
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        completed = [i for i in state["items"] if i["status"] == "COMPLETED"]
        actual_charge = cost_each * len(completed)
        precharged = state.get("precharged_credits", cost_each * state["total"])
        refund = max(0, precharged - actual_charge)
        if user:
            if refund > 0:
                user.credits_balance += refund
            state["credits_charged"] = actual_charge
            for idx_c, it in enumerate(completed):
                db.add(JobRecord(
                    user_id=user.id,
                    job_number=f"{int(time.time() * 1000) % 900000 + 100000}-{uuid.uuid4().hex[:4]}",
                    folder_name=state["folder_name"],
                    name=it["name"],
                    modality="Image",
                    status="Completed",
                    progress=100,
                    labels_count=1,
                    cost=f"${cost_each * 0.001:.3f}",
                    consensus_label=it.get("decision", "CONFIRMED"),
                    affirmative_votes=it.get("affirmative_votes", 32 if it.get("decision") == "CONFIRMED" else 0),
                    trace_id=it.get("trace_id"),
                    lineage_hash=it.get("lineage_hash", ""),
                    image_url=None,  # Zero-Retention: Do not persist raw raster data in database
                    criteria_json=json.dumps(it.get("criteria_results")),
                ))
            db.add(AuditLogEntry(
                user_id=user.id,
                action="IMAGE_BATCH_COMPLETED",
                details=f"Batch '{state['name']}' in folder '{state['folder_name']}': "
                        f"{len(completed)}/{state['total']} photos labeled, {state['failed']} failed.",
            ))
            db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        state["persist_error"] = str(exc)[:200]
    finally:
        db.close()

    for it in state["items"]:
        it.pop("image_data", None)  # zero-retention: drop raw pixels from RAM registry
    state["status"] = "COMPLETED" if state["failed"] < state["total"] else "FAILED"
    state["elapsed_seconds"] = round(time.time() - state["start_ts"], 1)


@router.post("/start")
async def start_image_batch(
    req: ImageBatchRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from api.rate_limiter import check_rate_limit, batch_limiter
    check_rate_limit(request, batch_limiter, user_id=user.id if user else None)
    raw_images = req.images or []
    if not raw_images:
        raise HTTPException(status_code=400, detail="Please upload at least 1 image for the batch.")

    if len(raw_images) > MAX_IMAGES_PER_BATCH:
        raise HTTPException(status_code=400, detail=f"A batch accepts at most {MAX_IMAGES_PER_BATCH} photos (got {len(raw_images)}).")

    tier = (req.depth_tier or "Standard").strip().capitalize()
    if tier not in CREDIT_COST:
        tier = "Standard"

    valid_images = []
    for idx, img in enumerate(raw_images):
        img_data = img.data or img.image_data or ""
        img_name = (img.name or f"photo_{idx + 1}.jpg").strip() or f"photo_{idx + 1}.jpg"
        if not img_data.startswith("data:image/"):
            raise HTTPException(status_code=400, detail=f"'{img_name}' is not a valid image data URL.")
        if len(img_data) > MAX_BYTES_PER_IMAGE * 4 // 3:
            raise HTTPException(status_code=413, detail=f"'{img_name}' is larger than 12 MB.")
        valid_images.append({"name": img_name, "data": img_data})

    raw_criteria = req.criteria or []
    valid_criteria = []
    for idx, c in enumerate(raw_criteria):
        c_name = (c.name or "").strip()
        if not c_name:
            continue
        valid_criteria.append({
            "name": c_name,
            "type": c.type or "Free Text",
            "range": c.range or "",
        })
    if not valid_criteria:
        valid_criteria = [{"name": "product name", "type": "Free Text", "range": "Open item name"}]

    needed = CREDIT_COST.get(tier, 5) * len(valid_images)
    rows_updated = db.query(User).filter(
        User.id == user.id,
        User.credits_balance >= needed
    ).update({User.credits_balance: User.credits_balance - needed})
    if rows_updated == 0:
        raise HTTPException(
            status_code=402,
            detail=f"Payment Required: Insufficient balance ({user.credits_balance} credits). Batch of {len(valid_images)} images requires {needed} credits. Please top up your balance."
        )
    db.commit()
    db.refresh(user)

    folder = (req.folder_name or "General Workspace").strip() or "General Workspace"
    if not db.query(FolderRecord).filter(FolderRecord.name == folder).first():
        db.add(FolderRecord(name=folder))
        db.commit()

    batch_name = (req.name or f"{len(valid_images)} Photos Inspection").strip() or f"{len(valid_images)} Photos Inspection"
    batch_id = f"imgbatch_{uuid.uuid4().hex[:12]}"
    _evict_stale_image_batches()

    IMAGE_BATCH_REGISTRY[batch_id] = {
        "batch_id": batch_id,
        "owner_id": user.id,
        "name": batch_name,
        "folder_name": folder,
        "depth_tier": tier,
        "criteria": valid_criteria,
        "status": "PROCESSING",
        "total": len(valid_images),
        "done": 0,
        "failed": 0,
        "progress_pct": 0.0,
        "concurrency": IMAGE_CONCURRENCY,
        "precharged_credits": needed,
        "credits_charged": 0,
        "start_ts": time.time(),
        "elapsed_seconds": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "items": [
            {"index": i, "name": im["name"], "status": "QUEUED", "image_data": im["data"]}
            for i, im in enumerate(valid_images)
        ],
    }
    asyncio.create_task(_run_batch(batch_id, user.id, user.email, tier, valid_criteria))
    return {
        "success": True,
        "batch_id": batch_id,
        "total": len(valid_images),
        "folder_name": folder,
        "concurrency": IMAGE_CONCURRENCY,
        "max_credits": needed,
    }


def _owned(batch_id: str, user: Optional[User]) -> Dict[str, Any]:
    _evict_stale_image_batches()
    state = IMAGE_BATCH_REGISTRY.get(batch_id)
    if not state:
        raise HTTPException(status_code=404, detail="Image batch not found.")
    owner_id = state.get("owner_id")
    if owner_id:
        if user is None:
            allow_guest = os.getenv("ALLOW_GUEST_INFERENCE", "").lower() in ("1", "true", "yes")
            if not allow_guest:
                raise HTTPException(status_code=401, detail="Authentication required to view this image batch.")
        elif owner_id != user.id and getattr(user, "role", "") not in ("Administrator", "admin"):
            raise HTTPException(status_code=403, detail="Access denied: You do not have permission to view this batch.")
    return state


def _eta_seconds(s: Dict[str, Any], elapsed: float) -> Optional[int]:
    """Estimate from the real observed rate. None until at least one item has finished."""
    if s["status"] != "PROCESSING" or s["done"] <= 0:
        return None
    per_item = elapsed / s["done"]
    return int(round(per_item * (s["total"] - s["done"])))


def _progress_message(s: Dict[str, Any], elapsed: float) -> str:
    """Plain, truthful progress text. Does not claim any verification that is not happening."""
    total, done = s["total"], s["done"]
    if s["status"] == "COMPLETED":
        return f"Completed: {total - s['failed']}/{total} items labeled" + (
            f", {s['failed']} could not be processed (credits refunded)." if s["failed"] else "."
        )
    if s["status"] == "FAILED":
        return "This batch could not be processed. Credits were refunded."
    current = min(done + 1, total)
    eta = _eta_seconds(s, elapsed)
    eta_txt = "estimating time remaining..." if eta is None else f"about {max(1, round(eta / 60))} min remaining"
    return f"Processing item {current}/{total} - queued processing, {eta_txt}"


@router.get("/status/{batch_id}")
async def image_batch_status(batch_id: str, user: Optional[User] = Depends(get_optional_current_user)):
    s = _owned(batch_id, user)
    elapsed = round(time.time() - s["start_ts"], 1) if s["status"] == "PROCESSING" else s["elapsed_seconds"]
    return {
        "success": True,
        "batch_id": batch_id,
        "name": s["name"],
        "folder_name": s["folder_name"],
        "status": s["status"],
        "total": s["total"],
        "done": s.get("done", 0),
        "failed": s.get("failed", 0),
        "progress_pct": s.get("progress_pct", 0.0),
        "concurrency": s.get("concurrency", IMAGE_CONCURRENCY),
        "credits_charged": s.get("credits_charged", 0),
        "elapsed_seconds": elapsed,
        "progress_message": _progress_message(s, elapsed),
        "eta_seconds": _eta_seconds(s, elapsed),
        "items": [_public_item(i) for i in list(s.get("items", []))],
    }


def _rows(s: Dict[str, Any]) -> (List[str], List[Dict[str, Any]]):
    crit_names: List[str] = [c["name"] for c in s["criteria"]]
    rows = []
    for it in s["items"]:
        row: Dict[str, Any] = {
            "Photo": it["name"],
            "Folder": s["folder_name"],
            "Status": it["status"],
            "Decision": it.get("decision", ""),
            "Votes": it.get("votes", ""),
            "Overall_Confidence_%": it.get("overall_confidence", ""),
        }
        by_norm = {}
        for c in (it.get("criteria_results") or []):
            k = (c.get("name") or c.get("heading") or "").strip()
            if k:
                by_norm[re.sub(r'[^a-z0-9]', '', k.lower())] = c

        for n in crit_names:
            norm_n = re.sub(r'[^a-z0-9]', '', n.lower())
            c = by_norm.get(norm_n)
            if not c:
                # Loose match fallback
                c = next((v for k, v in by_norm.items() if (k in norm_n or norm_n in k)), {})
            row[n] = c.get("value", "")
            row[f"{n}_Confidence_%"] = c.get("confidence", "")
        row["Lineage_Hash"] = it.get("lineage_hash", "")
        row["Trace_ID"] = it.get("trace_id", "")
        row["Error"] = it.get("error", "")
        rows.append(row)
    return list(rows[0].keys()) if rows else [], rows


@router.get("/report/{batch_id}")
async def image_batch_report(
    batch_id: str,
    format: str = Query("csv", pattern="^(csv|json|pdf)$"),
    user: Optional[User] = Depends(get_optional_current_user),
):
    s = _owned(batch_id, user)
    if s["status"] == "PROCESSING":
        raise HTTPException(status_code=409, detail="Batch is still processing; report is available when it finishes.")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in s["name"]) or "batch"
    headers_fn, rows = _rows(s)

    if format == "json":
        body = json.dumps({
            "batch_id": batch_id,
            "name": s["name"],
            "folder": s["folder_name"],
            "depth_tier": s["depth_tier"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total": s["total"],
            "completed": s["total"] - s["failed"],
            "failed": s["failed"],
            "credits_charged": s["credits_charged"],
            "elapsed_seconds": s["elapsed_seconds"],
            "results": [_public_item(i) for i in s["items"]],
        }, indent=2)
        return Response(body, media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{safe}_audit.json"'})

    if format == "csv":
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=headers_fn)
        w.writeheader()
        sanitized_rows = [
            {k: _sanitize_csv_cell(v) for k, v in r.items()}
            for r in rows
        ]
        w.writerows(sanitized_rows)
        return Response(out.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{safe}_audit.csv"'})

    try:
        from xml.sax.saxutils import escape as _xml_escape
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        raise HTTPException(status_code=501, detail="PDF export needs 'reportlab' (pip install reportlab).")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    st = getSampleStyleSheet()
    cn = [c["name"] for c in s["criteria"]]
    els = [
        Paragraph(f"CypherLabelGuard - Batch Audit Report: {_xml_escape(str(s['name']))}", st["Title"]),
        Paragraph(
            f"Folder: <b>{_xml_escape(str(s['folder_name']))}</b> &nbsp; Depth: <b>{_xml_escape(str(s['depth_tier']))}</b> &nbsp; "
            f"Photos: <b>{s['total']}</b> &nbsp; Completed: <b>{s['total'] - s['failed']}</b> &nbsp; "
            f"Failed: <b>{s['failed']}</b> &nbsp; Credits: <b>{s['credits_charged']}</b> &nbsp; "
            f"Time: <b>{s['elapsed_seconds']}s</b>", st["Normal"]),
        Spacer(1, 10),
    ]
    head = ["Photo", "Status", "Conf %"] + cn + ["Lineage"]
    data = [head]
    for r in rows:
        data.append([
            Paragraph(_xml_escape(str(r["Photo"])[:40]), st["BodyText"]),
            r["Status"],
            str(r["Overall_Confidence_%"]),
            *[Paragraph(_xml_escape(str(r.get(n, ""))[:40]), st["BodyText"]) for n in cn],
            r["Lineage_Hash"],
        ])
    tbl = Table(data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#064e3b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    els.append(tbl)
    failed = [i for i in s["items"] if i["status"] == "FAILED"]
    if failed:
        els += [Spacer(1, 10), Paragraph("Failed photos (not charged):", st["Heading3"])]
        els += [Paragraph(f"{_xml_escape(str(i['name']))}: {_xml_escape(str(i.get('error', '')))}", st["BodyText"]) for i in failed]
    doc.build(els)
    return Response(buf.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{safe}_audit.pdf"'})
