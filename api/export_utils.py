"""Shared export helpers (CSV formula sanitization, column aliasing, Store vs Audit mode, and 1-product-per-page Catalog PDF)."""

import csv
import io
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape


def normalize_heading_key(name: str) -> str:
    """Normalizes a criterion heading for resilient alias matching."""
    return re.sub(r"[^a-z0-9]", "", (name or "").strip().lower())


def unwrap_query_param(val: Any, default: Any = None) -> Any:
    """Extracts the raw default when a FastAPI Query() parameter is invoked directly outside ASGI."""
    if val is not None and type(val).__module__.startswith("fastapi") and hasattr(val, "default"):
        return val.default
    return default if val is None else val


def sanitize_csv_cell(val: Any) -> Any:
    """Neutralizes spreadsheet formula injection (=, +, -, @, tab, CR) while keeping negative numbers intact."""
    if isinstance(val, str) and val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
        if val[0] == "-" and val[1:].replace(".", "", 1).isdigit():
            return val
        return f"'{val}"
    return val


def parse_column_aliases(aliases_raw: Optional[str]) -> Dict[str, str]:
    """Parses a JSON object mapping original headings -> user display headings."""
    if not aliases_raw or not aliases_raw.strip():
        return {}
    try:
        parsed = json.loads(aliases_raw)
    except Exception:
        return {}
    if not isinstance(parsed, dict):
        return {}

    cleaned: Dict[str, str] = {}
    for k, v in parsed.items():
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        ks = k.strip()
        vs = v.strip()[:80]
        if ks and vs:
            cleaned[ks] = vs
            cleaned[ks.lower()] = vs
            norm = normalize_heading_key(ks)
            if norm and norm not in cleaned:
                cleaned[norm] = vs
    return cleaned


def default_price_col_label(name: str) -> str:
    """Flags unannotated price-like columns as AI estimates unless currency is configured or parenthesized."""
    if re.search(r"price|cost|mrp|amount|rate", name, re.IGNORECASE) and not re.search(r"\(.*\)", name):
        cur = os.getenv("REPORT_PRICE_CURRENCY", "").strip().upper()
        return f"{name} ({cur}, AI estimate)" if cur else f"{name} (AI estimate, currency not specified)"
    return name


def resolve_display_heading(
    original_name: str,
    aliases: Optional[Dict[str, str]] = None,
    *,
    apply_price_note: bool = True,
    used_labels: Optional[set] = None,
) -> str:
    """Resolves user-customized heading alias, falling back cleanly to default/price-annotated heading."""
    base = (original_name or "").strip()
    label = ""
    if aliases:
        label = (
            aliases.get(base)
            or aliases.get(base.lower())
            or aliases.get(normalize_heading_key(base))
            or ""
        )
    if not label:
        label = default_price_col_label(base) if apply_price_note else base

    if used_labels is not None:
        candidate = label or "Column"
        idx = 2
        while candidate in used_labels:
            candidate = f"{label} ({idx})"
            idx += 1
        used_labels.add(candidate)
        return candidate
    return label


def render_csv_text(headers: List[str], rows: List[Dict[str, Any]]) -> str:
    """Serializes sanitized CSV text with explicit column order."""
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    sanitized = [{k: sanitize_csv_cell(v) for k, v in r.items()} for r in rows]
    writer.writerows(sanitized)
    return out.getvalue()


def _tier_for_status(decision: str, confidence: Any, anomaly: bool = False) -> Tuple[str, str, str, str]:
    """Returns (label_text, bg_hex, text_hex, border_hex) using ReportLab-safe ASCII text."""
    dec = (decision or "").strip().upper()
    try:
        conf_val = float(confidence)
    except (TypeError, ValueError):
        conf_val = 0.0

    if anomaly or dec in ("REJECTED", "FAILED", "HUMAN_REVIEW", "DEFECT") or conf_val == 0.0:
        tag = dec or "HUMAN_REVIEW"
        return (f"REVIEW REQUIRED ({tag})", "#fee2e2", "#991b1b", "#dc2626")
    if dec == "PARTIAL" or (50.0 <= conf_val < 90.0):
        return (f"CHECK NEEDED ({dec or 'PARTIAL'})", "#fef3c7", "#92400e", "#d97706")
    if dec == "CONFIRMED" or conf_val >= 90.0:
        return (f"VERIFIED ({dec or 'CONFIRMED'})", "#dcfce7", "#166534", "#16a34a")
    return (f"REVIEW NEEDED ({dec or 'UNVERIFIED'})", "#fee2e2", "#991b1b", "#dc2626")


def build_catalog_pdf_bytes(
    *,
    title: str,
    subtitle: str,
    items: List[Dict[str, Any]],
    layout: str = "catalog",
    aliases: Optional[Dict[str, str]] = None,
    decision_legend: Optional[Dict[str, str]] = None,
    apply_price_note: bool = False,
) -> bytes:
    """
    Builds either:
    - layout='catalog': Portrait A4, strictly 1 product per page, bold custom headings, full untruncated content,
      color-coded status pills, and audit footer (Trace ID / Confidence / Lineage).
    - layout='table': Landscape A4 multi-product audit matrix with safe column widths and wrapped text.
    Zero-Retention compliant: operates strictly on extracted text labels without storing raw customer images.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    styles = getSampleStyleSheet()

    if layout == "table":
        doc = SimpleDocTemplate(
            buf, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
        )
        head_style = ParagraphStyle("tbl_hd", parent=styles["BodyText"], fontSize=7, leading=9, textColor=colors.white, wordWrap="CJK")
        cell_style = ParagraphStyle("tbl_cl", parent=styles["BodyText"], fontSize=7, leading=9, wordWrap="CJK")

        # Collect distinct criterion columns in appearance order
        seen_norms: List[str] = []
        col_originals: List[str] = []
        for it in items:
            for c in it.get("criteria") or []:
                orig = (c.get("name") or "").strip()
                norm = normalize_heading_key(orig)
                if orig and norm not in seen_norms:
                    seen_norms.append(norm)
                    col_originals.append(orig)

        used_labels: set = set()
        col_labels = [
            resolve_display_heading(orig, aliases, apply_price_note=apply_price_note, used_labels=used_labels)
            for orig in col_originals
        ]

        els: List[Any] = [
            Paragraph(f"CypherLabelGuard - {xml_escape(title)}", styles["Title"]),
            Paragraph(xml_escape(subtitle), styles["Normal"]),
            Spacer(1, 6),
        ]
        if decision_legend:
            legend_txt = " &nbsp;|&nbsp; ".join(
                f"<b>{xml_escape(str(k))}</b> = {xml_escape(str(v))}" for k, v in decision_legend.items()
            )
            els.extend([Paragraph(f"<b>Decision Guide:</b> {legend_txt}", styles["BodyText"]), Spacer(1, 8)])

        head = ["Product / Photo", "Decision", "Votes", "Conf %"] + col_labels + ["Lineage"]
        data = [[Paragraph(xml_escape(h), head_style) for h in head]]

        def _cell(val: Any, limit: int = 180) -> Paragraph:
            txt = str(val if val is not None else "")
            if len(txt) > limit:
                txt = txt[: limit - 3] + "..."
            return Paragraph(xml_escape(txt or "-"), cell_style)

        for it in items:
            crit_by_norm = {normalize_heading_key(c.get("name") or ""): c.get("value", "") for c in (it.get("criteria") or [])}
            row_cells = [
                _cell(it.get("name", ""), 48),
                _cell(it.get("decision") or it.get("status", ""), 18),
                _cell(it.get("votes", ""), 10),
                _cell(it.get("overall_confidence", ""), 8),
            ]
            for norm in seen_norms:
                row_cells.append(_cell(crit_by_norm.get(norm, ""), 160))
            row_cells.append(_cell((it.get("lineage_hash") or it.get("trace_id") or "")[:14], 16))
            data.append(row_cells)

        fixed = [88, 68, 34, 34, 61]
        usable = 794 - sum(fixed)
        per_crit = max(55, int(usable / max(1, len(col_labels))))
        col_widths = fixed[:4] + [per_crit] * len(col_labels) + [fixed[4]]

        tbl = Table(data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#064e3b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        els.append(tbl)
        doc.build(els)
        return buf.getvalue()

    # Default layout='catalog': Portrait A4, 1 Product Per Page, Full Untruncated Copy
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=38, rightMargin=38, topMargin=34, bottomMargin=32
    )
    brand_style = ParagraphStyle("cat_brand", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#047857"), fontName="Helvetica-Bold")
    meta_sub_style = ParagraphStyle("cat_sub", parent=styles["Normal"], fontSize=8.5, leading=11, textColor=colors.HexColor("#64748b"))
    title_style = ParagraphStyle("cat_prod_title", parent=styles["Heading1"], fontSize=16, leading=20, textColor=colors.HexColor("#0f172a"), fontName="Helvetica-Bold", spaceAfter=2)
    pill_style_cache: Dict[str, ParagraphStyle] = {}
    key_style = ParagraphStyle("cat_key", parent=styles["BodyText"], fontSize=9.5, leading=13, textColor=colors.HexColor("#0f172a"), fontName="Helvetica-Bold", wordWrap="CJK")
    key_conf_style = ParagraphStyle("cat_key_conf", parent=styles["Normal"], fontSize=7.5, leading=10, textColor=colors.HexColor("#64748b"))
    val_style = ParagraphStyle("cat_val", parent=styles["BodyText"], fontSize=10, leading=14.5, textColor=colors.HexColor("#1e293b"), wordWrap="CJK")
    err_style = ParagraphStyle("cat_err", parent=styles["BodyText"], fontSize=9.5, leading=13, textColor=colors.HexColor("#991b1b"))
    footer_style = ParagraphStyle("cat_foot", parent=styles["Normal"], fontSize=7.5, leading=10, textColor=colors.HexColor("#64748b"))

    def _pill_style(hex_color: str) -> ParagraphStyle:
        if hex_color not in pill_style_cache:
            pill_style_cache[hex_color] = ParagraphStyle(
                f"pill_{hex_color}", parent=styles["Normal"], fontSize=8.5, leading=11,
                fontName="Helvetica-Bold", textColor=colors.HexColor(hex_color), alignment=2,
            )
        return pill_style_cache[hex_color]

    els = []
    total_items = len(items)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for idx, it in enumerate(items):
        prod_name = str(it.get("name") or f"Product {idx + 1}")
        folder_name = str(it.get("folder") or "Default")
        job_id = str(it.get("job_id") or "").strip()
        decision = str(it.get("decision") or it.get("status") or "COMPLETED")
        overall_conf = it.get("overall_confidence", "")
        votes = str(it.get("votes") or "").strip()
        trace_id = str(it.get("trace_id") or "").strip()
        lineage = str(it.get("lineage_hash") or "").strip()
        error_msg = str(it.get("error") or "").strip()

        badge_text, bg_hex, fg_hex, border_hex = _tier_for_status(
            decision, overall_conf, bool(it.get("anomaly_detected", False))
        )

        # Page header bar
        top_left = [
            Paragraph("CYPHERLABELGUARD &nbsp;|&nbsp; PRODUCT LABEL CATALOG", brand_style),
            Paragraph(xml_escape(title) + (f" &nbsp;&bull;&nbsp; {xml_escape(subtitle)}" if subtitle else ""), meta_sub_style),
        ]
        top_right = Paragraph(f"Page {idx + 1} of {total_items}", ParagraphStyle("pg", parent=meta_sub_style, alignment=2))
        top_tbl = Table([[top_left, top_right]], colWidths=[410, 109])
        top_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#e2e8f0")),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ]))
        els.append(top_tbl)
        els.append(Spacer(1, 10))

        # Product banner with color-coded readiness pill
        sub_parts = [f"Collection: {folder_name}"]
        if job_id:
            sub_parts.append(f"Job: {job_id}")
        banner_left = [
            Paragraph(xml_escape(prod_name), title_style),
            Paragraph(xml_escape("  |  ".join(sub_parts)), meta_sub_style),
        ]
        pill_tbl = Table(
            [[Paragraph(xml_escape(badge_text), _pill_style(fg_hex))]],
            colWidths=[165],
        )
        pill_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(bg_hex)),
            ("BOX", (0, 0), (0, 0), 0.9, colors.HexColor(border_hex)),
            ("TOPPADDING", (0, 0), (0, 0), 5),
            ("BOTTOMPADDING", (0, 0), (0, 0), 5),
            ("LEFTPADDING", (0, 0), (0, 0), 8),
            ("RIGHTPADDING", (0, 0), (0, 0), 8),
        ]))
        header_row = Table([[banner_left, pill_tbl]], colWidths=[350, 169])
        header_row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        els.append(header_row)
        els.append(Spacer(1, 12))

        if error_msg and str(it.get("status", "")).upper() == "FAILED":
            err_box = Table(
                [[Paragraph(f"<b>Processing Failed (Credits Not Charged):</b> {xml_escape(error_msg)}", err_style)]],
                colWidths=[519],
            )
            err_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fee2e2")),
                ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#dc2626")),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]))
            els.append(err_box)
        else:
            criteria_list = it.get("criteria") or []
            if not criteria_list:
                els.append(Paragraph("No structured labels recorded for this item.", meta_sub_style))
            else:
                used_page_labels: set = set()
                card_rows: List[List[Any]] = []
                row_styles: List[Tuple[Any, ...]] = [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ]
                for r_idx, c in enumerate(criteria_list):
                    orig_h = (c.get("name") or "").strip() or f"Field {r_idx + 1}"
                    disp_h = resolve_display_heading(
                        orig_h, aliases, apply_price_note=apply_price_note, used_labels=used_page_labels
                    )
                    val_txt = str(c.get("value") if c.get("value") not in (None, "") else "-")
                    c_conf = c.get("confidence", "")
                    c_anom = bool(c.get("anomaly", False))
                    try:
                        c_conf_num: Optional[float] = float(c_conf) if str(c_conf).strip() != "" else None
                    except (TypeError, ValueError):
                        c_conf_num = None
                    c_dec = (
                        "REJECTED"
                        if c_anom
                        else (
                            "CONFIRMED"
                            if (c_conf_num is not None and c_conf_num >= 90.0)
                            else ("PARTIAL" if (c_conf_num is not None and c_conf_num >= 50.0) else "HUMAN_REVIEW")
                        )
                    )
                    _, c_bg, c_fg, c_border = _tier_for_status(c_dec, c_conf_num, c_anom)
                    conf_tag = f"{c_conf_num:.0f}% match" if c_conf_num is not None else ""
                    key_flowables: List[Any] = [Paragraph(xml_escape(disp_h), key_style)]
                    if conf_tag:
                        key_flowables.append(
                            Paragraph(
                                f'<font color="{c_fg}"><b>{xml_escape(conf_tag)}</b></font>',
                                key_conf_style,
                            )
                        )
                    # Convert newlines cleanly inside full untruncated paragraphs
                    val_html = "<br/>".join(xml_escape(line) for line in val_txt.splitlines()) or "-"
                    card_rows.append([key_flowables, Paragraph(val_html, val_style)])
                    row_styles.append(("LINEBEFORE", (0, r_idx), (0, r_idx), 3.0, colors.HexColor(c_border)))
                    if c_anom or bg_hex == "#fee2e2":
                        row_styles.append(("BACKGROUND", (1, r_idx), (1, r_idx), colors.HexColor("#fffbfb")))
                    elif r_idx % 2 == 1:
                        row_styles.append(("BACKGROUND", (1, r_idx), (1, r_idx), colors.HexColor("#ffffff")))

                card_tbl = Table(card_rows, colWidths=[152, 367])
                card_tbl.setStyle(TableStyle(row_styles))
                els.append(card_tbl)

        # Compact audit footer
        els.append(Spacer(1, 14))
        foot_parts = [f"Generated: {generated_at}"]
        if overall_conf != "":
            foot_parts.append(f"Overall Confidence: {overall_conf}%")
        if votes:
            foot_parts.append(f"Votes: {votes}")
        if trace_id:
            foot_parts.append(f"Trace ID: {trace_id}")
        if lineage:
            foot_parts.append(f"Lineage: {lineage[:20]}")
        foot_parts.append("Zero-Retention Verified")
        foot_tbl = Table(
            [[Paragraph(xml_escape("  |  ".join(foot_parts)), footer_style)]],
            colWidths=[519],
        )
        foot_tbl.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
        ]))
        els.append(foot_tbl)

        if idx < total_items - 1:
            els.append(PageBreak())

    doc.build(els)
    return buf.getvalue()
