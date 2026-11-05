# 🛡️ CypherLabelGuard — CORE EDITION v2.0 (Backend)

An enterprise-grade, privacy-first, zero-retention AI consensus, categorization, and forensic auditing engine.

---

## 📊 System Overview
* **Total Features:** 38 Modular Plugins across 6 Categories (A through F)
* **Sub-Features:** Deeply integrated sub-agents, tiers, and quarantine mechanics
* **Voting Mechanics:** 32-Vote Parliament ($4 \text{ APIs} \times 8 \text{ Dimensions}$)
  * $\ge 28$ Votes: **Confirmed**
  * $17 - 27$ Votes: **Stalemate** (decay-weighted resolution)
  * $\le 16$ Votes: **Human Review Required**
* **Network Highways:** 500 Managed Connections ($125 \times 4$) with Circuit Breakers (3 fails = 30s cooldown)
* **Privacy & Security:** Volatile RAM-only, Zero-Retention Purge, Echo Cancellation, SHA-256 Chained Lineage Ledger
* **Architecture:** 4 Sacred Files (`core/`) and Plugin-First Discovery (`manifest.yaml`)

---

## 🔒 The 4 Sacred Core Files (Never Broken)
1. [`core/base_feature.py`](core/base_feature.py): Mother of all 38 plugins. Standardizes `async def execute(self, context: ExecutionContext) -> ExecutionContext`.
2. [`core/context.py`](core/context.py): Immutable Context Bus with copy-on-write `.evolve()`, SHA-256 lineage hash chain, and `.purge()` zero-retention destructor.
3. [`core/registry.py`](core/registry.py): Central directory dynamically discovering all plugins, reading `manifest.yaml`, and validating toggles.
4. [`core/orchestrator.py`](core/orchestrator.py): Pipeline Conductor running Golden Flow stages, 30s cooldown circuit breaker, and 3-tier graceful degradation.

---

## 📁 Modular Directory Layout

```
CypherLabelGuard/
├── core/                                # 🔒 THE 4 SACRED FILES
│   ├── base_feature.py
│   ├── context.py
│   ├── registry.py
│   └── orchestrator.py
│
├── config/                              # Declarative Configurations
│   ├── registry.yaml                    # Toggles for all 38 features
│   ├── parliament_rules.yaml            # 4 APIs x 8 Dimensions = 32 votes
│   └── connections.yaml                 # 500 connection pool & latency limits
│
├── features/                            # PLUGINS (Each with manifest.yaml)
│   ├── cat_a_inference/                 # Features 01 - 10 (Accuracy & Consensus)
│   ├── cat_b_speed/                     # Features 11 - 17 (Speed & Throughput)
│   ├── cat_c_privacy/                   # Features 18 - 23 (Zero-Retention & Security)
│   ├── cat_d_drift/                     # Features 24 - 27 (Drift & Humility)
│   ├── cat_e_output/                    # Features 28 - 33 (UI Output & Prove It)
│   └── cat_f_multimodal/                # Features 34 - 38 (Multi-Modal Ingestion)
│
├── sandbox/                             # Rule 4: Sandbox Qualification Harness
│   └── verifier.py
│
├── api/                                 # FastAPI Backend & WebSocket Telemetry Gateway
│   └── server.py
│
├── tests/                               # Comprehensive Unit & Integration Test Suites
│   ├── test_core_sacred.py
│   └── test_api_server.py
│
└── run_backend.py                       # One-click Server Starter
```

---

## 🚀 How to Run the Backend

To start the backend server:

```powershell
python run_backend.py
```

* Swagger API Documentation: `http://127.0.0.1:8000/docs`
* Live WebSocket Telemetry: `ws://127.0.0.1:8000/ws/parliament`

---

## 🔌 Frontend Integration API Contracts

When connecting your frontend, use these endpoints:

### 1. Execute Inference Pass
* **Method:** `POST /api/v2/infer`
* **Request Payload:**
```json
{
  "text": "Suspicious login attempt with revoked credentials.",
  "modality": "TEXT",
  "depth_tier": "Standard",
  "tenant_id": "org_101"
}
```
* **Response Payload:** Returns Unified JSON envelope, 32-vote parliament decisions, the 4×8 grid color tiles (Green, Yellow, Red), and `prove_it_trace_id`.

### 2. Live 4×8 Parliament Dashboard (WebSocket)
* **Endpoint:** `ws://127.0.0.1:8000/ws/parliament`
* **Behavior:** Streams real-time pipeline events and the 32 interactive tiles live as each vote arrives.

### 3. "Prove It" Forensic Audit Button
* **Method:** `GET /api/v2/prove-it/{trace_id}`
* **Response Payload:** Returns full transparent breakdown: all 32 individual votes, token attribution, prompt hashes, and the unbroken SHA-256 audit chain.

### 4. Emergency Panic Flush
* **Method:** `POST /api/v2/panic-flush`
* **Behavior:** Immediately purges cryptographic salts, clears RAM buffers, and wipes volatile memory.
