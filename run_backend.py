# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Main Application Entrypoint: Starts the FastAPI & WebSocket Server
# ==============================================================================

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn

# Ensure project root is in sys.path
root_path = Path(__file__).resolve().parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))


def main():
    print("=" * 70)
    print("[*] CypherLabelGuard -- CORE EDITION v2.0 BACKEND")
    print("=" * 70)
    print(" * Total Features: 38 Plugins loaded across 6 Categories")
    print(" * Parliamentary Voting: 32-Vote Engine (4 APIs x 8 Dimensions)")
    print(" * Security Architecture: Zero-Retention & SHA-256 Lineage Hash Chain")
    print(" * Network Pools: 500 Managed Connections (125 per provider)")
    print(" * Real-Time Gateway: WebSockets on /ws/parliament")
    print(" * REST API: http://127.0.0.1:8000/docs")
    print("=" * 70)

    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
