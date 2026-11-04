# Workspace Security & Autonomous Execution Policy

## 1. Autonomous Scope (No Repeated Permission Prompts)
The agent is authorized to execute autonomous actions within this workspace (`c:\Users\Friends\Desktop\CypherLabelGuard`) without asking for repetitive permissions on mundane development tasks:
- **Code & File Operations:** Creating, reading, editing, and refactoring project files in `api/`, `frontend/`, `db/`, `plugins/`, and `tests/`.
- **Local Tool Execution:** Running terminal commands in PowerShell (`python`, `npm`, `npx`, `vite`, `pytest`, `git status/add/commit`).
- **Local Database Operations:** Querying, creating tables, and running migrations on local SQLite (`cypher_label_guard.db`).
- **Browser & UI Verification:** Running headless browser captures and local test scripts to verify UI and API health.

## 2. Laptop Security Boundary (Restricted to Project Only)
- The agent **MUST NOT** access, read, write, or execute commands on any directory outside of `c:\Users\Friends\Desktop\CypherLabelGuard`.
- Personal directories, downloads, desktop files outside this project, and Windows system folders are strictly off-limits.
- All scratchpads and test outputs must reside inside `scratch/` or the project root.

## 3. Important Decisions (MUST ALWAYS Ask User for Confirmation)
The agent **MUST PAUSE AND EXPLICITLY ASK THE USER** for approval before proceeding with:
1. **Financial & Live Payments:**
   - Setting live Stripe production credentials or initiating real-money credit card charges.
2. **Destructive Database Actions:**
   - Dropping database tables or purging persistent customer job history.
3. **Destructive Git Actions:**
   - Force-pushing (`git push --force`) or deleting branches.
4. **Architectural & External Service Integration:**
   - Signing up for external paid cloud providers or third-party paid APIs.
   - Any modifications to the 4 Sacred Core Layer files in `core/`.
