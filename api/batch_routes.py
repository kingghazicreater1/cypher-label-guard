# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Batch Ingestion & Dynamic Criteria Processing Engine (1,000+ Items)
# ==============================================================================

import asyncio
import csv
import io
import os
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Response
import logging
from pydantic import BaseModel, Field

from core.context import ExecutionContext
from core.orchestrator import orchestrator
from db.database import SessionLocal
from db.models import User, JobRecord, AuditLogEntry
from api.auth_routes import get_optional_current_user, get_current_user
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter(prefix="/api/v2/batch", tags=["Batch Labeling & Dynamic Criteria Engine"])

# Ephemeral Volatile In-Memory Batch Registry (Zero-Retention compliant)
BATCH_REGISTRY: Dict[str, Dict[str, Any]] = {}
logger = logging.getLogger("CYPHER_LABEL_GUARD.Batch")

# Finished batches are evicted after this many seconds to prevent unbounded memory growth.
BATCH_TTL_SECONDS = int(os.getenv("BATCH_TTL_SECONDS", "3600"))


def _evict_stale_batches() -> None:
    now = time.time()
    for bid in [
        k for k, v in BATCH_REGISTRY.items()
        if v.get("status") != "PROCESSING" and now - v.get("end_timestamp", now) > BATCH_TTL_SECONDS
    ]:
        BATCH_REGISTRY.pop(bid, None)


def _get_owned_batch(batch_id: str, user: User) -> Dict[str, Any]:
    """Return the batch only if it belongs to the caller (admins may see all)."""
    b = BATCH_REGISTRY.get(batch_id)
    if b is None or (b.get("owner_id") != user.id and user.role != "Administrator"):
        # Same response for missing and foreign batches so IDs cannot be probed.
        raise HTTPException(status_code=404, detail="Batch job not found.")
    return b


class CriterionItem(BaseModel):
    name: str = Field(..., description="Heading name, e.g. Color, Price Tier, Quality, Defective?")
    type: str = Field(default="Enum", description="Enum, Scale, Range, Boolean, Free Text")
    range: Optional[str] = Field(default="", description="Range or options, e.g. Red, Blue, Green or 1-10")


class BatchParseRequest(BaseModel):
    csv_text: str = Field(..., description="Raw CSV text content")


class BatchStartRequest(BaseModel):
    name: str = Field(default="1,000 Products Catalog Batch", description="Human-readable batch job name")
    csv_text: str = Field(..., description="Raw CSV content")
    target_column: str = Field(..., description="Column header to analyze with Dynamic Criteria")
    criteria: List[CriterionItem] = Field(..., description="Dynamic criteria headings to evaluate")
    depth_tier: str = Field(default="Fast", description="Fast (2s), Standard (8s), Deep (20s)")
    modality: str = Field(default="TEXT", description="TEXT, VISION, AUDIO, VIDEO")


# ------------------------------------------------------------------------------
# 1. Parse CSV and Return Column Schema & Sample Preview
# ------------------------------------------------------------------------------
@router.post("/parse")
async def parse_csv_batch(req: BatchParseRequest):
    """
    Parses an incoming CSV string and returns detected column headers,
    row count, and the first 5 sample rows for column mapping.
    """
    _evict_stale_batches()
    try:
        reader = csv.DictReader(io.StringIO(req.csv_text.strip()))
        headers = reader.fieldnames or []
        rows = list(reader)
        if not rows:
            raise HTTPException(status_code=400, detail="CSV file appears to be empty or missing data rows.")

        return {
            "success": True,
            "total_rows": len(rows),
            "headers": headers,
            "preview": rows[:5],
            "detected_candidates": [h for h in headers if any(k in h.lower() for k in ["desc", "name", "title", "text", "clause", "content", "msg"])],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


# ------------------------------------------------------------------------------
# 2. Pre-Built Sample Datasets Generator for Instant 1-Click SMB Testing
# ------------------------------------------------------------------------------
@router.get("/sample/{sample_type}")
async def get_sample_dataset(sample_type: str):
    """
    Returns realistic pre-built CSV datasets for SMB onboarding:
    - 'ecommerce': 1,000 retail products catalog (SKU, Title, Category, Price, Description)
    - 'legal': 500 commercial contract clauses (Clause ID, Title, Clause Text, Jurisdiction)
    - 'moderation': 500 social media comments & reviews (Comment ID, User, Comment Text)
    """
    output = io.StringIO()
    
    if sample_type == "ecommerce":
        writer = csv.DictWriter(output, fieldnames=["SKU", "Product_Title", "Category", "Catalog_Price", "Product_Description"])
        writer.writeheader()
        
        colors = ["Bold Red", "Navy Blue", "Forest Green", "Obsidian Black", "Pure White"]
        materials = ["Italian Leather", "Breathable Mesh", "Anodized Aluminum", "Organic Cotton", "Carbon Fiber"]
        categories = ["Footwear", "Apparel", "Electronics", "Accessories", "Luggage"]
        
        for i in range(1, 1001):
            c = colors[i % len(colors)]
            m = materials[i % len(materials)]
            cat = categories[i % len(categories)]
            price = 4500 + (i * 35) % 85000
            has_defect = (i % 23 == 0)
            defect_phrase = "Minor seam irregularity on inner lining" if has_defect else "Zero defect found, pristine finish"
            
            writer.writerow({
                "SKU": f"AVG-{10000 + i}",
                "Product_Title": f"{m} {cat} #{i} in {c}",
                "Category": cat,
                "Catalog_Price": f"PKR {price:,}",
                "Product_Description": f"Authentic {m} {cat} crafted in {c}. Valued at PKR {price:,}. Quality inspect: {defect_phrase}.",
            })
            
    elif sample_type == "legal":
        writer = csv.DictWriter(output, fieldnames=["Clause_ID", "Section", "Title", "Clause_Text"])
        writer.writeheader()
        
        risks = [
            ("Indemnity", "Vendor shall unconditionally indemnify Customer against all third-party claims without liability ceiling or financial cap."),
            ("Limitation of Liability", "Neither party aggregate liability under this agreement shall exceed PKR 5,000,000 in the aggregate."),
            ("Governing Law", "This contract shall be construed in accordance with the Laws of Pakistan, with exclusive jurisdiction in Lahore."),
            ("Termination", "Either party may terminate upon 30 days written notice without penalty or liquidated damages."),
        ]
        
        for i in range(1, 501):
            r_title, r_text = risks[i % len(risks)]
            writer.writerow({
                "Clause_ID": f"SEC-{200 + i}",
                "Section": f"§ {4 + (i % 12)}.{i % 5 + 1}",
                "Title": f"{r_title} Clause",
                "Clause_Text": f"{r_text} (Reference identifier: CLAUSE-PK-{i:04d}).",
            })
            
    else:
        writer = csv.DictWriter(output, fieldnames=["ID", "User_Handle", "Timestamp", "Message_Text"])
        writer.writeheader()
        templates = [
            "Outstanding service and immediate delivery, very pleased with quality!",
            "Neutral inquiry regarding return policy and warranty conditions.",
            "Warning: Severe delay in fulfillment, requesting immediate escalation.",
            "Safe standard transaction completed with full verification clearance.",
        ]
        for i in range(1, 501):
            writer.writerow({
                "ID": f"MSG-{i:05d}",
                "User_Handle": f"@user_{i}",
                "Timestamp": f"2026-10-15T04:{i%60:02d}:00Z",
                "Message_Text": templates[i % len(templates)],
            })

    csv_data = output.getvalue()
    return {
        "success": True,
        "sample_type": sample_type,
        "row_count": csv_data.count("\n") - 1,
        "csv_text": csv_data,
    }


# ------------------------------------------------------------------------------
# 3. Start Asynchronous Multi-Model Batch Inference (1,000 Items)
# ------------------------------------------------------------------------------
async def _execute_batch_job(
    batch_id: str,
    name: str,
    rows: List[Dict[str, str]],
    target_column: str,
    criteria: List[Dict[str, Any]],
    depth_tier: str,
    user_id: Optional[str] = None,
):
    """
    Background asynchronous worker executing parliamentary voting across batch rows.
    Uses concurrency semaphores to maintain optimal throughput without rate-limit throttling.
    """
    batch_state = BATCH_REGISTRY[batch_id]
    total = len(rows)
    semaphore = asyncio.Semaphore(10)  # 10 parallel pipeline passes
    
    ordered_rows: List[Optional[Dict[str, Any]]] = [None] * total
    completed_count = 0
    running_conf_sum = 0.0

    async def _process_single_row(idx: int, row_data: Dict[str, str]):
        nonlocal running_conf_sum, completed_count
        async with semaphore:
            text_val = str(row_data.get(target_column, ""))
            
            effective_depth = depth_tier

            ctx = ExecutionContext(
                tenant_id=f"user_{user_id}" if user_id else "batch_tenant",
                depth_tier=effective_depth,
                input_payload={
                    "text": text_val,
                    "criteria": criteria,
                    "batch_row_index": idx,
                },
            )
            
            try:
                final_ctx = await orchestrator.run_pipeline(ctx)
                crit_results = final_ctx.metadata.get("criteria_results", [])
                overall_conf = final_ctx.metadata.get("overall_criteria_confidence", 0.0)
                
                # Clone original row and append dynamic criteria output columns
                augmented_row = dict(row_data)
                for cr in crit_results:
                    c_name = cr.get("name", "Field")
                    augmented_row[c_name] = str(cr.get("value", ""))
                    augmented_row[f"{c_name}_Confidence"] = f"{cr.get('confidence', 0.0)}%"
                    augmented_row[f"{c_name}_Agreement"] = str(cr.get("agreement", ""))
                
                augmented_row["Overall_Confidence"] = f"{overall_conf}%"
                augmented_row["Parliament_Decision"] = final_ctx.metadata.get("parliament_decision", "CONFIRMED")
                augmented_row["Lineage_Hash"] = final_ctx.metadata.get("final_lineage_hash", "")[:16]
                
                running_conf_sum += overall_conf
                ordered_rows[idx] = augmented_row
                completed_count += 1
                
                batch_state["completed_rows"] = completed_count
                batch_state["progress_pct"] = round((completed_count / total) * 100.0, 1)
                batch_state["overall_confidence"] = round(running_conf_sum / completed_count, 1)
                batch_state["current_item"] = f"Row #{idx + 1}: {text_val[:35]}..."
            except Exception as row_err:
                augmented_row = dict(row_data)
                logger.warning("Batch %s row %s failed: %s", batch_id, idx, type(row_err).__name__)
                augmented_row["Overall_Confidence"] = "0.0%"
                augmented_row["Parliament_Decision"] = "ERROR_UNVERIFIED"
                ordered_rows[idx] = augmented_row
                completed_count += 1
                batch_state["failed_rows"] = batch_state.get("failed_rows", 0) + 1
                batch_state["completed_rows"] = completed_count
                batch_state["progress_pct"] = round((completed_count / total) * 100.0, 1)

    tasks = [_process_single_row(i, row) for i, row in enumerate(rows)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    worker_crashed = any(isinstance(r, BaseException) for r in results)

    labeled_rows = [r for r in ordered_rows if r is not None]
    failed = batch_state.get("failed_rows", 0)
    batch_state["status"] = "FAILED" if (worker_crashed or failed >= total) else "COMPLETED"
    batch_state["labeled_rows"] = labeled_rows
    batch_state["end_timestamp"] = time.time()
    batch_state["elapsed_seconds"] = round(time.time() - batch_state["start_timestamp"], 1)

    # Persist job record to database and reconcile credits
    try:
        db = SessionLocal()
        user = db.query(User).filter(User.id == user_id).first() if user_id else None
        target_uid = user.id if user else None
        if target_uid:
            charged_rows = max(0, total - failed)
            if user and getattr(user, "credits_balance", None) is not None:
                user.credits_balance = max(0, user.credits_balance - charged_rows)
            job_rec = JobRecord(
                user_id=target_uid,
                job_number=f"{int(time.time() * 1000) % 900000 + 100000}-{uuid.uuid4().hex[:4]}",
                name=f"{name} ({total} items)",
                modality="CSV Batch",
                status="Completed",
                progress=100,
                labels_count=total,
                cost=f"${charged_rows * 0.001:.2f}",
                consensus_label="CONFIRMED" if batch_state["status"] == "COMPLETED" and not failed else "PARTIAL_UNVERIFIED",
                affirmative_votes=0,
                trace_id=batch_id,
            )
            db.add(job_rec)
            db.add(AuditLogEntry(
                user_id=target_uid,
                action="BATCH_JOB_COMPLETED",
                details=f"Batch '{name}' completed: {total} items labeled with dynamic criteria.",
            ))
            db.commit()
        db.close()
    except Exception as persist_err:
        logger.error("Batch %s persistence failed: %s", batch_id, type(persist_err).__name__)


@router.post("/start")
async def start_batch_processing(
    req: BatchStartRequest,
    user: User = Depends(get_current_user),
):
    """
    Initializes a multi-model background batch run over up to 1,000+ CSV items.
    """
    try:
        reader = csv.DictReader(io.StringIO(req.csv_text.strip()))
        rows = list(reader)
        if not rows:
            raise HTTPException(status_code=400, detail="Provided CSV contains no data rows.")
        if len(rows) > 5000:
            raise HTTPException(status_code=400, detail=f"CSV batch exceeds maximum of 5,000 rows (got {len(rows)}).")
        if getattr(user, "credits_balance", 1) <= 0:
            raise HTTPException(status_code=402, detail="Payment Required: Insufficient credits balance to start CSV batch.")

        if req.target_column not in (reader.fieldnames or []):
            raise HTTPException(status_code=400, detail=f"Target column '{req.target_column}' not found in CSV headers.")

        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        criteria_dicts = [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in req.criteria]

        BATCH_REGISTRY[batch_id] = {
            "batch_id": batch_id,
            "owner_id": user.id,
            "name": req.name,
            "status": "PROCESSING",
            "total_rows": len(rows),
            "completed_rows": 0,
            "failed_rows": 0,
            "progress_pct": 0.0,
            "target_column": req.target_column,
            "criteria": criteria_dicts,
            "overall_confidence": 0.0,
            "current_item": "Initializing Parliament workers...",
            "start_timestamp": time.time(),
            "elapsed_seconds": 0.0,
            "original_headers": reader.fieldnames or [],
            "labeled_rows": [],
        }

        # Launch non-blocking background worker
        asyncio.create_task(
            _execute_batch_job(
                batch_id=batch_id,
                name=req.name,
                rows=rows,
                target_column=req.target_column,
                criteria=criteria_dicts,
                depth_tier=req.depth_tier,
                user_id=user.id,
            )
        )

        return {
            "success": True,
            "batch_id": batch_id,
            "name": req.name,
            "total_rows": len(rows),
            "status": "PROCESSING",
            "message": f"Parliament workers spawned. Processing {len(rows)} items across {len(req.criteria)} dynamic headings.",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch: {str(e)}")


# ------------------------------------------------------------------------------
# 4. Check Batch Status & Progress
# ------------------------------------------------------------------------------
@router.get("/status/{batch_id}")
async def get_batch_status(batch_id: str, user: User = Depends(get_current_user)):
    """
    Polls real-time progress of an active or completed batch labeling run.
    """
    b = _get_owned_batch(batch_id, user)
    preview_items = b["labeled_rows"][:5] if b["labeled_rows"] else []
    
    elapsed = round(time.time() - b["start_timestamp"], 1) if b["status"] == "PROCESSING" else b.get("elapsed_seconds", 0.0)

    return {
        "success": True,
        "batch_id": batch_id,
        "name": b["name"],
        "status": b["status"],
        "total_rows": b["total_rows"],
        "completed_rows": b["completed_rows"],
        "failed_rows": b.get("failed_rows", 0),
        "progress_pct": b["progress_pct"],
        "overall_confidence": b["overall_confidence"],
        "current_item": b.get("current_item", ""),
        "elapsed_seconds": elapsed,
        "preview_items": preview_items,
    }


# ------------------------------------------------------------------------------
# 5. Download Completed Labeled CSV
# ------------------------------------------------------------------------------
@router.get("/download/{batch_id}")
async def download_labeled_csv(batch_id: str, user: User = Depends(get_current_user)):
    """
    Exports the finalized CSV file with all original columns plus
    the newly generated confidence-scored Dynamic Criteria columns.
    """
    b = _get_owned_batch(batch_id, user)
    rows = b.get("labeled_rows", [])
    if not rows:
        raise HTTPException(status_code=400, detail="Batch is still processing or has no rows available.")

    fieldnames = list(rows[0].keys())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    csv_data = output.getvalue()
    safe_name = b["name"].lower().replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_labeled_{b['total_rows']}_items.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
