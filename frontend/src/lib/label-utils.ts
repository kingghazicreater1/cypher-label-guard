import { useEffect, useState } from "react";
import { NO_IMAGE_PLACEHOLDER } from "./api";

export type HeadingAliasMap = Record<string, string>;

export type StatusTier = "green" | "amber" | "red";

export interface TierStyle {
  tier: StatusTier;
  badgeText: string;
  shortTag: string;
  borderClass: string;
  bgClass: string;
  badgeClass: string;
  dotClass: string;
  hexBorder: string;
  hexBg: string;
  hexText: string;
}

const ALIAS_STORAGE_KEY = "clg_column_aliases_v1";
const ALIAS_EVENT = "clg:column-aliases-updated";

export const STORE_ALIAS_PRESETS: Record<string, string> = {
  "name of product": "Product Title",
  "product name": "Product Title",
  "item name / title": "Product Title",
  "color of main product": "Color",
  color: "Color",
  "estimate price": "Price (PKR)",
  "estimated price": "Price (PKR)",
  price: "Price (PKR)",
  "why you should by it ?": "Selling Point",
  "why you should buy it": "Selling Point",
  "selling point": "Selling Point",
  "short description": "Short Detail",
  "detailed description": "Description",
  "describe in 50 words": "50-Word Detail",
  "description in 50 words": "50-Word Detail",
};

export function normalizeHeadingKey(name: string): string {
  return (name || "").trim().toLowerCase().replace(/[^a-z0-9]/g, "");
}

export function loadHeadingAliases(): HeadingAliasMap {
  try {
    const raw = localStorage.getItem(ALIAS_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

export function saveHeadingAliases(next: HeadingAliasMap): void {
  const cleaned: HeadingAliasMap = {};
  for (const [k, v] of Object.entries(next || {})) {
    const ks = String(k || "").trim();
    const vs = String(v || "").trim().slice(0, 80);
    if (ks && vs && vs !== ks) {
      cleaned[ks] = vs;
    }
  }
  try {
    localStorage.setItem(ALIAS_STORAGE_KEY, JSON.stringify(cleaned));
    window.dispatchEvent(new CustomEvent<HeadingAliasMap>(ALIAS_EVENT, { detail: cleaned }));
  } catch {
    // Ignore storage quota errors cleanly
  }
}

export function useHeadingAliases(): [HeadingAliasMap, (next: HeadingAliasMap) => void] {
  const [aliases, setAliasesState] = useState<HeadingAliasMap>(() => loadHeadingAliases());

  useEffect(() => {
    const onCustom = (ev: Event) => {
      const detail = (ev as CustomEvent<HeadingAliasMap>).detail;
      setAliasesState(detail || loadHeadingAliases());
    };
    const onStorage = (ev: StorageEvent) => {
      if (ev.key === ALIAS_STORAGE_KEY) {
        setAliasesState(loadHeadingAliases());
      }
    };
    window.addEventListener(ALIAS_EVENT, onCustom);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(ALIAS_EVENT, onCustom);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const updateAliases = (next: HeadingAliasMap) => {
    saveHeadingAliases(next);
    setAliasesState(loadHeadingAliases());
  };

  return [aliases, updateAliases];
}

export function getDisplayHeading(originalName: string, aliases?: HeadingAliasMap): string {
  const raw = (originalName || "").trim();
  if (!raw || !aliases) return raw;
  if (aliases[raw]) return aliases[raw];
  const lower = raw.toLowerCase();
  for (const [k, v] of Object.entries(aliases)) {
    if (k.trim().toLowerCase() === lower && v) return v;
  }
  const norm = normalizeHeadingKey(raw);
  if (norm) {
    for (const [k, v] of Object.entries(aliases)) {
      if (normalizeHeadingKey(k) === norm && v) return v;
    }
  }
  return raw;
}

export function suggestStoreAlias(originalName: string): string | null {
  const norm = normalizeHeadingKey(originalName);
  for (const [k, v] of Object.entries(STORE_ALIAS_PRESETS)) {
    if (normalizeHeadingKey(k) === norm) return v;
  }
  return null;
}

export function serializeAliasesParam(aliases?: HeadingAliasMap): string | undefined {
  if (!aliases) return undefined;
  const entries = Object.entries(aliases).filter(([k, v]) => k.trim() && v.trim());
  if (entries.length === 0) return undefined;
  return JSON.stringify(Object.fromEntries(entries));
}

const TIER_STYLES: Record<StatusTier, TierStyle> = {
  green: {
    tier: "green",
    badgeText: "Verified · Ready to Copy",
    shortTag: "Verified",
    borderClass: "border-emerald-500/45",
    bgClass: "bg-emerald-500/[0.06]",
    badgeClass: "border-emerald-500/40 bg-emerald-500/15 text-emerald-300",
    dotClass: "bg-emerald-400",
    hexBorder: "#10b981",
    hexBg: "#ecfdf5",
    hexText: "#065f46",
  },
  amber: {
    tier: "amber",
    badgeText: "Check Needed",
    shortTag: "Verify",
    borderClass: "border-amber-500/50",
    bgClass: "bg-amber-500/[0.06]",
    badgeClass: "border-amber-500/40 bg-amber-500/15 text-amber-300",
    dotClass: "bg-amber-400",
    hexBorder: "#d97706",
    hexBg: "#fffbeb",
    hexText: "#92400e",
  },
  red: {
    tier: "red",
    badgeText: "Review Required",
    shortTag: "Review",
    borderClass: "border-rose-500/60",
    bgClass: "bg-rose-500/[0.07]",
    badgeClass: "border-rose-500/50 bg-rose-500/15 text-rose-300",
    dotClass: "bg-rose-500",
    hexBorder: "#e11d48",
    hexBg: "#fff1f2",
    hexText: "#9f1239",
  },
};

export function getCriterionTier(input: {
  confidence?: number | string | undefined;
  anomaly?: boolean | undefined;
  decision?: string | undefined;
  value?: any;
}): TierStyle {
  const dec = String(input.decision || "").trim().toUpperCase();
  const hasConf =
    input.confidence !== undefined &&
    input.confidence !== null &&
    String(input.confidence).trim() !== "";
  const confNum = hasConf ? Number(input.confidence) : 0;
  const valStr = String(input.value ?? "").toUpperCase();

  if (
    Boolean(input.anomaly) ||
    dec === "REJECTED" ||
    dec === "FAILED" ||
    dec === "HUMAN_REVIEW" ||
    dec === "DEFECT" ||
    valStr.includes("REJECT") ||
    valStr.includes("[UNVERIFIED") ||
    (hasConf && Number(confNum) === 0) ||
    (hasConf && confNum < 50)
  ) {
    return TIER_STYLES.red;
  }
  if (dec === "PARTIAL" || (hasConf && confNum >= 50 && confNum < 90)) {
    return TIER_STYLES.amber;
  }
  if (dec === "CONFIRMED" || (hasConf && confNum >= 90)) {
    return TIER_STYLES.green;
  }
  return TIER_STYLES.amber;
}

export function getProductTier(item: {
  status?: string | undefined;
  decision?: string | undefined;
  overall_confidence?: number | string | undefined;
  overall_criteria_confidence?: number | string | undefined;
  anomaly_detected?: boolean | undefined;
  criteria_results?: Array<{ confidence?: any; anomaly?: boolean | undefined; value?: any }> | undefined;
}): TierStyle {
  const statusUpper = String(item.status || "").trim().toUpperCase();
  const decUpper = String(item.decision || "").trim().toUpperCase();
  if (
    Boolean(item.anomaly_detected) ||
    statusUpper === "FAILED" ||
    decUpper === "FAILED" ||
    decUpper === "REJECTED" ||
    decUpper === "HUMAN_REVIEW"
  ) {
    return TIER_STYLES.red;
  }

  const rawConf = item.overall_confidence ?? item.overall_criteria_confidence;
  const hasConf = rawConf !== undefined && rawConf !== null && String(rawConf).trim() !== "";
  const confNum = hasConf ? Number(rawConf) : undefined;
  const hasRowAnomaly = (item.criteria_results || []).some(
    (c) => Boolean(c.anomaly) || (c.confidence !== undefined && Number(c.confidence) === 0)
  );
  if (hasRowAnomaly) {
    return TIER_STYLES.red;
  }
  return getCriterionTier({
    confidence: confNum,
    anomaly: Boolean(item.anomaly_detected),
    decision: decUpper || (statusUpper === "COMPLETED" ? "CONFIRMED" : statusUpper),
  });
}

export async function copyTextToClipboard(text: string): Promise<boolean> {
  const val = String(text ?? "");
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(val);
      return true;
    }
  } catch {
    // Fallback below
  }
  try {
    const el = document.createElement("textarea");
    el.value = val;
    el.setAttribute("readonly", "");
    el.style.position = "fixed";
    el.style.left = "-9999px";
    document.body.appendChild(el);
    el.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(el);
    return ok;
  } catch {
    return false;
  }
}

export function formatProductCopyBlock(
  fields: Array<{ heading: string; value: any }>,
  aliases?: HeadingAliasMap
): string {
  return fields
    .map((f) => {
      const val = String(f.value ?? "").trim();
      if (!val || val === "—") return "";
      const heading = getDisplayHeading(f.heading, aliases);
      return `${heading}: ${val}`;
    })
    .filter(Boolean)
    .join("\n");
}

function isUsableImageUrl(url?: string | null): url is string {
  if (!url || typeof url !== "string") return false;
  if (url === NO_IMAGE_PLACEHOLDER) return false;
  return url.startsWith("data:image/") || url.startsWith("http://") || url.startsWith("https://") || url.startsWith("blob:") || url.startsWith("/");
}

export function storeLocalThumbnail(key: string, dataUrl: string): void {
  if (!key || !isUsableImageUrl(dataUrl)) return;
  try {
    sessionStorage.setItem(`avg_img_${key}`, dataUrl);
  } catch {
    // Ignore storage quota overflow gracefully
  }
}

export function getLocalThumbnail(
  primaryNameOrKey?: string | null | undefined,
  fallbackUrl?: string | null | undefined,
  secondaryKey?: string | null | undefined
): string | null {
  if (isUsableImageUrl(fallbackUrl)) return fallbackUrl;
  try {
    if (secondaryKey) {
      const bySecondary = sessionStorage.getItem(`avg_img_${secondaryKey}`);
      if (isUsableImageUrl(bySecondary)) return bySecondary;
    }
    if (primaryNameOrKey) {
      const byPrimary = sessionStorage.getItem(`avg_img_${primaryNameOrKey}`);
      if (isUsableImageUrl(byPrimary)) return byPrimary;
    }
  } catch {
    // Ignore storage errors
  }
  return null;
}

export interface PrintableCatalogItem {
  name: string;
  folder?: string | undefined;
  thumbnailUrl?: string | null | undefined;
  status?: string | undefined;
  decision?: string | undefined;
  overall_confidence?: number | string | undefined;
  votes?: string | undefined;
  trace_id?: string | undefined;
  lineage_hash?: string | undefined;
  anomaly_detected?: boolean | undefined;
  error?: string | undefined;
  criteria: Array<{
    name: string;
    value: any;
    confidence?: number | string | undefined;
    anomaly?: boolean | undefined;
  }>;
}

function escapeHtml(text: string): string {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** Opens a 1-Product-Per-Page Photo Catalog print preview using browser-side thumbnails (Zero-Retention compliant). */
export function openPrintablePhotoCatalog(
  items: PrintableCatalogItem[],
  aliases: HeadingAliasMap = {},
  docTitle = "CypherLabelGuard Product Catalog"
): boolean {
  if (!items || items.length === 0) return false;
  const win = window.open("", "_blank", "width=980,height=820");
  if (!win) return false;

  const pagesHtml = items
    .map((item, idx) => {
      const prodTier = getProductTier({
        status: item.status,
        decision: item.decision,
        overall_confidence: item.overall_confidence,
        anomaly_detected: item.anomaly_detected,
        criteria_results: item.criteria,
      });
      const thumb = getLocalThumbnail(item.name, item.thumbnailUrl);
      const thumbHtml = thumb
        ? `<div class="photo-wrap"><img src="${escapeHtml(thumb)}" alt="${escapeHtml(item.name)}" /></div>`
        : `<div class="photo-empty">Original image purged on server (Zero-Retention Privacy Active)</div>`;

      const rowsHtml = item.error && String(item.status || "").toUpperCase() === "FAILED"
        ? `<div class="err-box"><strong>Processing Failed (Not Billed):</strong> ${escapeHtml(item.error)}</div>`
        : `<table class="spec-table">${item.criteria
            .map((c) => {
              const disp = getDisplayHeading(c.name, aliases);
              const cTier = getCriterionTier({ confidence: c.confidence, anomaly: c.anomaly, value: c.value });
              const cNum = c.confidence !== undefined && c.confidence !== "" ? `${Number(c.confidence).toFixed(0)}%` : "";
              const val = String(c.value ?? "").trim() || "—";
              return `<tr>
                <td class="col-k" style="border-left: 4px solid ${cTier.hexBorder}">
                  <div class="k-title">${escapeHtml(disp)}</div>
                  ${cNum ? `<div class="k-meta" style="color:${cTier.hexText}">${escapeHtml(cNum)} match</div>` : ""}
                </td>
                <td class="col-v">${escapeHtml(val).replace(/\n/g, "<br/>")}</td>
              </tr>`;
            })
            .join("")}</table>`;

      return `<section class="catalog-page">
        <header class="page-head">
          <div>
            <div class="brand">CYPHERLABELGUARD · PRODUCT CATALOG</div>
            <h1>${escapeHtml(item.name)}</h1>
            <div class="sub">Collection: ${escapeHtml(item.folder || "General Workspace")} &bull; Page ${idx + 1} of ${items.length}</div>
          </div>
          <div class="pill" style="background:${prodTier.hexBg};color:${prodTier.hexText};border-color:${prodTier.hexBorder}">
            ${escapeHtml(prodTier.badgeText)}
          </div>
        </header>
        ${thumbHtml}
        ${rowsHtml}
        <footer class="page-foot">
          ${item.overall_confidence !== undefined && item.overall_confidence !== "" ? `Confidence: ${escapeHtml(String(item.overall_confidence))}% &bull; ` : ""}
          ${item.votes ? `Votes: ${escapeHtml(item.votes)} &bull; ` : ""}
          ${item.trace_id ? `Trace ID: ${escapeHtml(item.trace_id)} &bull; ` : ""}
          Zero-Retention Verified
        </footer>
      </section>`;
    })
    .join("");

  const html = `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(docTitle)}</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #0f172a; background: #f1f5f9; }
    .toolbar { position: sticky; top: 0; background: #0f172a; color: #fff; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; z-index: 10; }
    .toolbar button { background: #10b981; color: #052e16; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 700; cursor: pointer; }
    .catalog-page { width: 210mm; min-height: 277mm; margin: 18px auto; background: #fff; padding: 14mm 16mm; border-radius: 8px; box-shadow: 0 4px 18px rgba(15,23,42,.08); display: flex; flex-direction: column; gap: 14px; page-break-after: always; }
    .catalog-page:last-child { page-break-after: auto; }
    .page-head { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; gap: 16px; }
    .brand { font-size: 10px; font-weight: 800; letter-spacing: .08em; color: #047857; margin-bottom: 4px; }
    h1 { margin: 0; font-size: 20px; line-height: 1.25; color: #0f172a; word-break: break-word; }
    .sub { font-size: 12px; color: #64748b; margin-top: 3px; }
    .pill { border: 1.5px solid; border-radius: 999px; padding: 5px 12px; font-size: 11px; font-weight: 700; white-space: nowrap; }
    .photo-wrap { text-align: center; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
    .photo-wrap img { max-width: 100%; max-height: 230px; object-fit: contain; border-radius: 4px; }
    .photo-empty { text-align: center; padding: 24px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; font-size: 12px; color: #64748b; }
    .spec-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .spec-table td { border: 1px solid #e2e8f0; padding: 9px 11px; vertical-align: top; }
    .col-k { width: 32%; background: #f8fafc; }
    .k-title { font-weight: 700; color: #0f172a; }
    .k-meta { font-size: 10.5px; font-weight: 600; margin-top: 2px; }
    .col-v { width: 68%; color: #1e293b; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
    .err-box { border: 1.5px solid #e11d48; background: #fff1f2; color: #9f1239; padding: 12px; border-radius: 8px; font-size: 13px; }
    .page-foot { margin-top: auto; border-top: 1px solid #e2e8f0; padding-top: 8px; font-size: 10.5px; color: #64748b; }
    @media print {
      body { background: #fff; }
      .toolbar { display: none; }
      .catalog-page { width: auto; min-height: auto; margin: 0; padding: 8mm 10mm; box-shadow: none; border-radius: 0; }
    }
  </style>
</head>
<body>
  <div class="toolbar">
    <span><strong>${escapeHtml(docTitle)}</strong> &mdash; ${items.length} Product${items.length === 1 ? "" : "s"} (1 Page Each)</span>
    <button onclick="window.print()">Print / Save PDF</button>
  </div>
  ${pagesHtml}
</body>
</html>`;

  win.document.open();
  win.document.write(html);
  win.document.close();
  return true;
}
