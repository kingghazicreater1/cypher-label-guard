// ==============================================================================
// CypherLabelGuard v2.0 — Frontend Backend Bridge & Real-Time Telemetry Client
// ==============================================================================

// Configurable per environment (VITE_API_URL); falls back to the local dev backend.
const ENV_API_URL = (import.meta as any).env?.VITE_API_URL as string | undefined;
import { getStoredToken } from "./auth-token";

export const API_BASE_URL = (ENV_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
export const WS_BASE_URL = `${API_BASE_URL.replace(/^http/i, "ws")}/ws/parliament`;

/** Neutral placeholder shown when a job has no stored image (zero-retention means originals are not kept). */
export const NO_IMAGE_PLACEHOLDER =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    "<svg xmlns='http://www.w3.org/2000/svg' width='800' height='480'><rect width='100%' height='100%' fill='#18181b'/><text x='50%' y='50%' fill='#a1a1aa' font-family='sans-serif' font-size='20' text-anchor='middle'>Original image not retained (zero-retention)</text></svg>"
  );

/** HTTP error that keeps the status code so pollers can tell permanent failures from transient ones. */
export class ApiHttpError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiHttpError";
    this.status = status;
  }
}

/** True when retrying can never succeed (auth lost, resource gone). */
export function isPermanentPollError(err: unknown): boolean {
  return err instanceof ApiHttpError && [400, 401, 403, 404, 410].includes(err.status);
}

export interface CriterionItem {
  name: string;
  type: "Enum" | "Scale" | "Range" | "Boolean" | "Free Text" | string;
  range?: string | undefined;
}

export interface CriterionResult {
  name: string;
  type: string;
  value: string | number;
  confidence: number;
  agreement: string;
  range?: string;
  votes?: Record<string, any>;
  anomaly?: boolean;
  anomaly_reason?: string;
}


export interface CriteriaTemplate {
  id: string;
  name: string;
  description: string;
  criteria: CriterionItem[];
}

export interface InferenceParams {
  text?: string | undefined;
  modality?: "TEXT" | "VISION" | "AUDIO" | "VIDEO" | undefined;
  media_url?: string | undefined;
  image_data?: string | undefined;
  audio_data?: string | undefined;
  video_data?: string | undefined;
  depth_tier?: "Fast" | "Standard" | "Deep" | undefined;
  tenant_id?: string | undefined;
  folder_name?: string | undefined;
  criteria?: CriterionItem[] | undefined;
}

export interface GridTile {
  api: string;
  dimension: string;
  vote: string;
  confidence: number;
  color: "GREEN" | "YELLOW" | "RED";
  latency_ms: number;
  seat?: number;
  is_dissent?: boolean;
}

export interface InferenceResult {
  success: boolean;
  data: {
    version: string;
    trace_id: string;
    session_id: string;
    tenant_id: string;
    modality: string;
    depth_tier: string;
    consensus: {
      decision: string;
      label: string;
      affirmative_votes: number;
      total_votes_cast: number;
      threshold_rule: string;
      confidence?: number;
    };
    criteria_results?: CriterionResult[];
    overall_criteria_confidence?: number;
    audit: {
      lineage_depth: number;
      lineage_verified: boolean;
      final_hash: string;
    };
    security: {
      zero_retention_armed: boolean;
      ram_only_verified: boolean;
      echo_cancelled: boolean;
    };
  };
  parliament_grid: GridTile[];
  prove_it_trace_id: string;
  trace_id?: string;
  job_id?: string;
  job_number?: string;
  criteria_results?: CriterionResult[];
  overall_criteria_confidence?: number;
  anomaly_detected?: boolean;
  summary: {

    total_votes_cast: number;
    flags: Record<string, any>;
    lineage_valid: boolean;
    latest_lineage_hash: string;
    is_purged: boolean;
    latency_ms?: number;
    cost_credits?: number;
    job_name?: string;
    modality?: string;
  };
}

export interface ProveItDossier {
  session_id: string;
  trace_id: string;
  tenant_id: string;
  depth_tier: string;
  total_votes: number;
  consensus_label?: string | undefined;
  affirmative_votes?: number | undefined;
  vote_breakdown: Array<{
    api: string;
    dimension: string;
    vote: string;
    confidence: number;
    reasoning: string;
    latency_ms: number;
    timestamp: number;
  }>;
  lineage_ledger: Array<{
    index: number;
    step_name: string;
    previous_hash: string;
    payload_hash: string;
    current_hash: string;
    timestamp: number;
  }>;
  lineage_unbroken: boolean;
  attributed_tokens: Array<{ token: string; attribution_score: number }>;
  entropy_score: number;
  fidelity_score: number;
  deterministic_state_hash: string;
}

/**
 * Executes a full 38-feature multi-modal inference pass on the backend.
 */
export async function runInference(params: InferenceParams): Promise<InferenceResult> {
  const resp = await fetch(`${API_BASE_URL}/api/v2/infer`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text: params.text || "",
      modality: params.modality || "TEXT",
      media_url: params.media_url,
      image_data: params.image_data,
      audio_data: params.audio_data,
      video_data: params.video_data,
      depth_tier: params.depth_tier || "Standard",
      tenant_id: params.tenant_id || "default_tenant",
      criteria: params.criteria,
    }),
  });

  if (!resp.ok) {
    const errorText = await resp.text();
    let detailMsg = errorText;
    try {
      const parsed = JSON.parse(errorText);
      if (parsed.detail) {
        detailMsg = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
      }
    } catch {
      // Keep raw errorText if not JSON
    }
    throw new Error(`Inference failed (${resp.status}): ${detailMsg}`);
  }

  return await resp.json();
}

/**
 * Retrieves pre-configured dynamic criteria templates.
 */
export async function getCriteriaTemplates(): Promise<CriteriaTemplate[]> {
  try {
    const resp = await fetch(`${API_BASE_URL}/api/v2/criteria/templates`);
    if (!resp.ok) return [];
    const json = await resp.json();
    return json.templates || [];
  } catch {
    return [];
  }
}

/**
 * Retrieves the complete 1-click forensic Prove-It audit dossier.
 */
export async function getProveItDossier(traceId: string): Promise<ProveItDossier> {
  const resp = await fetch(`${API_BASE_URL}/api/v2/prove-it/${traceId}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch Prove-It dossier for Trace ${traceId}`);
  }
  const result = await resp.json();
  return result.dossier;
}

/**
 * Triggers the emergency Feature 21 Panic Salt Flush.
 */
export async function triggerPanicFlush(reason: string = "User initiated emergency flush"): Promise<any> {
  const resp = await fetch(`${API_BASE_URL}/api/v2/panic-flush`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
  return await resp.json();
}

/**
 * Checks system health and circuit breaker statuses.
 */
export async function getSystemHealth(): Promise<any> {
  const resp = await fetch(`${API_BASE_URL}/api/v2/health`);
  return await resp.json();
}

/**
 * Retrieves the latest parliament consensus and 4x8 grid state.
 */
export async function getLatestParliamentState(): Promise<any> {
  const resp = await fetch(`${API_BASE_URL}/api/v2/parliament/latest`, { headers: getAuthHeaders() });
  if (!resp.ok) return { success: false };
  return await resp.json();
}

/**
 * Subscribes to live WebSocket telemetry events from the backend orchestrator.
 */
export function subscribeParliamentStream(
  onEvent: (event: any) => void,
  onStatusChange?: (connected: boolean) => void
): () => void {
  let ws: WebSocket | null = null;
  let stopped = false;
  let heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let attempt = 0;

  const clearHeartbeat = () => {
    if (heartbeatInterval) clearInterval(heartbeatInterval);
    heartbeatInterval = null;
  };

  function scheduleReconnect() {
    if (stopped || reconnectTimer) return;
    // Exponential backoff: 2s, 4s, 8s ... capped at 30s.
    const delay = Math.min(30_000, 2_000 * 2 ** Math.min(attempt, 4));
    attempt += 1;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, delay);
  }

  function connect() {
    if (stopped) return;
    const token = getStoredToken();
    if (!token) {
      // Not signed in yet: nothing to subscribe to, try again later.
      onStatusChange?.(false);
      scheduleReconnect();
      return;
    }
    try {
      const socket = new WebSocket(WS_BASE_URL);
      ws = socket;

      socket.onopen = () => {
        // The session token travels in the first message, never in the URL.
        socket.send(JSON.stringify({ action: "AUTH", token }));
        clearHeartbeat();
        heartbeatInterval = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: "PING" }));
          }
        }, 15000);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data?.event === "CONNECTED") {
            attempt = 0;
            onStatusChange?.(true);
          }
          onEvent(data);
        } catch {
          // ignore non-json
        }
      };

      socket.onclose = () => {
        if (ws === socket) ws = null;
        onStatusChange?.(false);
        clearHeartbeat();
        scheduleReconnect();
      };

      socket.onerror = () => {
        socket.close();
      };
    } catch {
      onStatusChange?.(false);
      scheduleReconnect();
    }
  }

  connect();

  return () => {
    stopped = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    reconnectTimer = null;
    clearHeartbeat();
    ws?.close();
  };
}

// ----------------------------------------------------------------------------
// Commercial Billing, Credit Cards, Invoices & History APIs
// ----------------------------------------------------------------------------

export interface CreditCard {
  id: string;
  card_brand: string;
  last4: string;
  exp_month: number;
  exp_year: number;
  cardholder_name: string;
  is_default: boolean;
  created_at?: string;
}

export interface BillingSummary {
  success: boolean;
  subscription: {
    plan_name: string;
    monthly_price: number;
    status: string;
    current_period_end?: string;
  };
  credits_balance: number;
  credits_value_usd: number;
  default_card: CreditCard | null;
  total_cards: number;
  stripe_configured: boolean;
  stripe_publishable_key?: string;
}

export interface InvoiceItem {
  id: string;
  invoice_number: string;
  description: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  action: string;
  details: string;
  ip_address: string;
  created_at: string;
}

export function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function getBillingSummary(): Promise<BillingSummary> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/summary`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load billing summary");
  return res.json();
}

export async function getCards(): Promise<CreditCard[]> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/cards`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load cards");
  const data = await res.json();
  return data.cards || [];
}

export async function addCreditCard(card: {
  card_number: string;
  exp_month: number;
  exp_year: number;
  cvc: string;
  cardholder_name: string;
  make_default?: boolean;
}): Promise<CreditCard> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/cards`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(card),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to add card" }));
    throw new Error(err.detail || "Failed to add card");
  }
  const data = await res.json();
  return data.card;
}

export async function deleteCreditCard(cardId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/cards/${cardId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to delete card");
}

export async function setDefaultCreditCard(cardId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/cards/${cardId}/default`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to set default card");
}

export async function changeSubscriptionPlan(planName: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/subscription`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ plan_name: planName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to update subscription plan" }));
    throw new Error(err.detail || "Failed to update subscription plan");
  }
  return res.json();
}

export async function purchaseTokenCredits(amount: number): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/credits/purchase`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ credit_amount: amount }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to purchase credits" }));
    throw new Error(err.detail || "Failed to purchase credits");
  }
  return res.json();
}

export async function getInvoices(): Promise<InvoiceItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/invoices`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load invoices");
  const data = await res.json();
  return data.invoices || [];
}

export interface DashboardAnalyticsResponse {
  success: boolean;
  period: string;
  ref_date: string;
  total_jobs: number;
  total_labels: number;
  prev_labels: number;
  labels_change: string;
  accuracy_pct: string;
  passed_jobs: number;
  avg_processing_time: string;
  total_cost: string;
  time_series: Array<{ time: string; labels: number; previous: number }>;
  cost_breakdown: Array<{ name: string; cost: string; percent: string; color: string }>;
  modality_breakdown: Record<string, number>;
}

export async function getDashboardAnalytics(period = "Today", folder?: string): Promise<DashboardAnalyticsResponse> {
  const params = new URLSearchParams({ period });
  if (folder && folder !== "All") params.append("folder", folder);
  const res = await fetch(`${API_BASE_URL}/api/v2/history/analytics?${params.toString()}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load dashboard analytics");
  return res.json();
}

export async function getJobHistory(folder?: string): Promise<any[] & { folders?: string[] }> {
  const url = folder && folder !== "All"
    ? `${API_BASE_URL}/api/v2/history/jobs?folder=${encodeURIComponent(folder)}`
    : `${API_BASE_URL}/api/v2/history/jobs`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to load job history");
  const data = await res.json();
  const list: any = data.jobs || [];
  list.folders = data.folders || ["General Workspace"];
  return list;
}

export async function getFolders(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v2/history/folders`, { headers: getAuthHeaders() });
    if (!res.ok) return ["General Workspace"];
    const data = await res.json();
    return data.folders || ["General Workspace"];
  } catch {
    return ["General Workspace"];
  }
}

export async function createFolder(name: string): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v2/history/folders`, {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) return [name, "General Workspace"];
    const data = await res.json();
    return data.folders || [name, "General Workspace"];
  } catch {
    return [name, "General Workspace"];
  }
}

export async function getSingleJob(jobId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v2/history/jobs/${encodeURIComponent(jobId)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.job || null;
  } catch {
    return null;
  }
}

export async function getAuditLogs(limit: number = 200): Promise<AuditLogItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/v2/history/audit-logs?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load audit logs");
  const data = await res.json();
  return data.audit_logs || [];
}

// ----------------------------------------------------------------------------
// Batch CSV/Excel Ingestion Engine APIs (1,000+ Items)
// ----------------------------------------------------------------------------

export interface BatchStartParams {
  name: string;
  csv_text: string;
  target_column: string;
  criteria: CriterionItem[];
  depth_tier?: "Fast" | "Standard" | "Deep";
}

export interface BatchStatusResponse {
  success: boolean;
  batch_id: string;
  name: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED";
  total_rows: number;
  completed_rows: number;
  failed_rows?: number;
  progress_pct: number;
  overall_confidence: number;
  current_item: string;
  elapsed_seconds: number;
  preview_items: Array<Record<string, any>>;
}

export async function parseCsvBatch(csvText: string): Promise<{
  success: boolean;
  total_rows: number;
  headers: string[];
  preview: Array<Record<string, string>>;
  detected_candidates: string[];
}> {
  const res = await fetch(`${API_BASE_URL}/api/v2/batch/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ csv_text: csvText }),
  });
  if (!res.ok) throw new Error("Failed to parse CSV file");
  return res.json();
}

export async function getSampleDataset(sampleType: "ecommerce" | "legal" | "moderation" = "ecommerce"): Promise<{
  success: boolean;
  sample_type: string;
  row_count: number;
  csv_text: string;
}> {
  const res = await fetch(`${API_BASE_URL}/api/v2/batch/sample/${sampleType}`);
  if (!res.ok) throw new Error("Failed to generate sample dataset");
  return res.json();
}

export async function startBatchJob(params: BatchStartParams): Promise<{
  success: boolean;
  batch_id: string;
  name: string;
  total_rows: number;
  status: string;
  message: string;
}> {
  const res = await fetch(`${API_BASE_URL}/api/v2/batch/start`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error("Failed to start batch job");
  return res.json();
}

export async function getBatchStatus(batchId: string): Promise<BatchStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v2/batch/status/${batchId}`, { headers: getAuthHeaders() });
  if (!res.ok) throw new ApiHttpError("Failed to get batch status", res.status);
  return res.json();
}

/** Downloads the labeled CSV with the caller's credentials (the endpoint is no longer public). */
export async function downloadBatchCsv(batchId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v2/batch/download/${batchId}`, { headers: getAuthHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "CSV download failed" }));
    throw new ApiHttpError(typeof err.detail === "string" ? err.detail : "CSV download failed", res.status);
  }
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `labeled_${batchId}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ----------------------------------------------------------------------------
// Batch Image Inspection (10-50 photos -> folder -> parallel Parliament)
// ----------------------------------------------------------------------------

export const MAX_BATCH_IMAGES = 50;

export interface ImageBatchItem {
  index: number;
  name: string;
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";
  decision?: string;
  votes?: string;
  overall_confidence?: number;
  criteria_results?: CriterionResult[];
  lineage_hash?: string;
  trace_id?: string;
  seconds?: number;
  error?: string;
}

export interface ImageBatchStatus {
  success: boolean;
  batch_id: string;
  name: string;
  folder_name: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED";
  total: number;
  done: number;
  failed: number;
  progress_pct: number;
  concurrency: number;
  credits_charged: number;
  elapsed_seconds: number;
  items: ImageBatchItem[];
}

/** Downscale to max 1280px JPEG so 50 photos upload fast and vision calls stay cheap. */
export function fileToResizedDataUrl(file: File, maxSide = 1280, quality = 0.85): Promise<string> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(img.width * scale);
      canvas.height = Math.round(img.height * scale);
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        URL.revokeObjectURL(url);
        reject(new Error(`Cannot process ${file.name}`));
        return;
      }
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL("image/jpeg", quality));
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error(`'${file.name}' is not a readable image`));
    };
    img.src = url;
  });
}

export async function startImageBatch(params: {
  name: string;
  folder_name: string;
  depth_tier: string;
  criteria: CriterionItem[];
  images: { name: string; data: string }[];
}): Promise<{ batch_id: string; total: number; folder_name: string; concurrency: number; max_credits: number }> {
  const res = await fetch(`${API_BASE_URL}/api/v2/batch/images/start`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to start image batch" }));
    let msg = "Failed to start image batch";
    if (typeof err.detail === "string") {
      msg = err.detail;
    } else if (Array.isArray(err.detail) && err.detail.length > 0) {
      msg = err.detail.map((e: any) => `${e.loc?.slice(1).join('.') || 'field'}: ${e.msg}`).join(', ');
    } else if (err.message) {
      msg = err.message;
    }
    throw new Error(msg);
  }
  return res.json();
}

export async function getImageBatchStatus(batchId: string): Promise<ImageBatchStatus> {
  const res = await fetch(`${API_BASE_URL}/api/v2/batch/images/status/${batchId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new ApiHttpError("Failed to get image batch status", res.status);
  return res.json();
}

export async function downloadImageBatchReport(batchId: string, format: "csv" | "json" | "pdf"): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v2/batch/images/report/${batchId}?format=${format}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Report download failed" }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Report download failed");
  }
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `batch_audit_${batchId}.${format}`;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ----------------------------------------------------------------------------
// BYOK (Bring Your Own Key) & Live Multi-Model Key Validator APIs
// ----------------------------------------------------------------------------

export interface ProviderKeyInfo {
  name: string;
  model_name: string;
  configured: boolean;
  masked_key: string;
  mode: string;
  rpm_tier_limit: string;
  is_free_tier?: boolean;
}

export interface KeysStatusResponse {
  success: boolean;
  configured_providers: number;
  total_providers: number;
  parliament_status: string;
  providers: Record<string, ProviderKeyInfo>;
}

export async function getKeysStatus(): Promise<KeysStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v2/keys/status`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to load key statuses");
  return res.json();
}

export async function updateKeys(keys: {
  groq_key?: string;
  groq_model?: string;
  openai_key?: string;
  openai_model?: string;
  anthropic_key?: string;
  anthropic_model?: string;
  gemini_key?: string;
  gemini_model?: string;
  mistral_key?: string;
  mistral_model?: string;
  openrouter_key?: string;
  openrouter_model?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v2/keys/update`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(keys),
  });
  if (!res.ok) throw new Error("Failed to update API keys");
  return res.json();
}

export async function testProviderKey(provider: string, apiKey?: string, modelName?: string): Promise<{
  success: boolean;
  results: Record<string, { status: string; latency_ms?: number; response?: string; error?: string; message?: string; model?: string }>;
}> {
  const res = await fetch(`${API_BASE_URL}/api/v2/keys/test`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ provider, api_key: apiKey, model_name: modelName }),
  });
  if (!res.ok) throw new Error("Failed to execute key test ping");
  return res.json();
}

// ----------------------------------------------------------------------------
// Generic 4-Seat Key Slots APIs (Key #1 to Key #4)
// ----------------------------------------------------------------------------
export interface KeySlotInfo {
  slot_id: string;
  slot_number: number;
  label: string;
  seat_name: string;
  model_name: string;
  configured: boolean;
  masked_key: string;
  status: "ONLINE" | "UNCONFIGURED";
}

export interface KeySlotsResponse {
  success: boolean;
  slots: KeySlotInfo[];
  configured_slots: number;
  total_slots: number;
}

export async function getKeySlots(): Promise<KeySlotsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v2/keys/slots`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to load key slots");
  return res.json();
}

export async function updateKeySlot(slotId: string, modelName?: string, apiKey?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v2/keys/slots/update`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ slot_id: slotId, model_name: modelName || "", api_key: apiKey || "" }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to update slot" }));
    throw new Error(err.detail || "Failed to update slot");
  }
  return res.json();
}

export async function testKeySlot(slotId: string, modelName?: string, apiKey?: string): Promise<{
  success: boolean;
  slot_id: string;
  result: { status: string; latency_ms?: number; response?: string; error?: string; model?: string; message?: string };
}> {
  const res = await fetch(`${API_BASE_URL}/api/v2/keys/slots/test`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ slot_id: slotId, model_name: modelName, api_key: apiKey }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Test ping failed" }));
    throw new Error(err.detail || "Test ping failed");
  }
  return res.json();
}

// ----------------------------------------------------------------------------
// Commander's Custom Labeling Rate Controller APIs
// ----------------------------------------------------------------------------
export interface CommanderRates {
  base_text_credits: number;
  vision_inspection_credits: number;
  parliament_consensus_credits: number;
  cryptographic_proof_credits: number;
  turbo_speed_credits: number;
}

export async function getCommanderRates(): Promise<CommanderRates> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/rates`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to load commander rates");
  const data = await res.json();
  return data.rates;
}

export async function updateCommanderRates(rates: CommanderRates): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v2/billing/rates`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(rates),
  });
  if (!res.ok) throw new Error("Failed to update commander rates");
  return res.json();
}

// Sign-in is handled exclusively by Clerk (see lib/auth-token.ts). The legacy google / phone /
// password / commander-unlock endpoints no longer exist on the backend.
export async function getCurrentUserProfile(): Promise<{ success: boolean; user: any; subscription: any; credits_balance: number }> {
  const res = await fetch(`${API_BASE_URL}/api/v2/auth/me`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export interface HeadingOption {
  key: string;
  label: string;
  name: string;
  type: 'Enum' | 'Scale' | 'Range' | 'Boolean' | 'Free Text';
  range: string;
}

export interface ClarifyHeadingResult {
  is_ambiguous: boolean;
  ambiguity_reason: string;
  question: string;
  options: HeadingOption[];
}

export async function clarifyHeading(heading: string, modality?: string): Promise<ClarifyHeadingResult | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v2/criteria/clarify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ heading, modality: modality || "IMAGE" }),
    });
    if (!res.ok) return null;
    const json = await res.json();
    return json.data || null;
  } catch (err) {
    console.error("Failed to clarify heading:", err);
    return null;
  }
}
