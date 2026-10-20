# campusKubo

This document records the features and design notes that are currently present in this repository, and briefly lists design proposals that are not implemented here.

### Project Overview & Problem Statement
- **Project**: campusKubo — Boarding & Bedspace Finder for Students
- **Problem statement**: Provide a lightweight web application to discover and reserve student boarding/bedspace, and tools for property managers to list and manage properties.

**What this repository currently implements**
- UI: built with Flet — views, components, and navigation are implemented under `app/views` and `app/components`.
- Search & Browse: browse and search listings with filters and images; the live-search UX was implemented to update results in-place and preserve focus while typing.
- Accounts & RBAC: user accounts and role-based access controls exist (roles include visitor, tenant, PM, admin). Session handling and `SessionState` helpers are implemented.
- Reservations: basic reservation data model and reservation flows exist (models and services under `app/models` and `app/services`).
- Soft-delete: user/listing soft-delete support (a `deleted_at` column/migration exists in `app/storage`).
- Login UX: email format validation was added to the login flow; account lockout logic was adjusted (short-duration lockout) and the UI disables the login button with a countdown while locked out.
- Branding: a reusable `Logo` component was added at `app/components/logo.py` and used in primary navbars.
- Tests & docs: a unit test suite exists under `tests/` (tests were run during development), and documentation artifacts were added: `docs/SRS.md`, `docs/README_EMERGING_TECH.md`, `docs/campuskubo_schema.json`, `docs/ARCHITECTURE.md`, and `docs/architecture.puml`.

**Design proposals / not implemented in this repository**
- Real-time updates (WebSocket server) — design notes exist, but no operational WebSocket server is included.
- AI-assisted inference (text summary, classification) — design guidance and fallback strategies are described, but no cloud-hosted AI integration or packaged on-device model is included in the repository.
- Offline-first sync, cloud sync, and edge device inference — these are listed as future enhancements or design notes and are not implemented here.

---

### Scope Table
| Feature | Status | Notes |
|---|---|---|
| Browse & search listings | Implemented | Live in-place updates; consider adding debounce for production
| Listings CRUD | Implemented (basic) | Admin/PM CRUD available in code
| Reservations | Implemented (basic) | Reservation model and flows present; payments not integrated
| RBAC / Session handling | Implemented | `SessionState` and role checks used by views
| Email input validation | Implemented | Login validates presence of `@` and `.`
| Login lockout + cooldown UI | Implemented | Short-duration lockout with disabled login button and countdown UI
| Real-time updates | Not implemented (design only) | diagrams and notes included as a proposal
| AI-assisted features | Not implemented (design only) | Design and fallback patterns provided in docs

---

### Architecture (what's in the repo)
```
+------------------------+        +---------------------+
|        Flet UI         |        |   Background Jobs   |
|  (Tabs: Overview,... ) |        |  (seed/init tasks)  |
+-----------+------------+        +----------+----------+
            |                                |
            v                                v
+------------------------+        +---------------------+
|      Service Layer     |        |  Session Manager    |
| auth / user / property |<------>| in-memory sessions  |
+-----------+------------+        +----------+----------+
            |                                |
            v                                v
+------------------------------------------------------+
|                    Storage Layer                     |
| SQLite (raw sqlite3 layer), bootstrapped via dotenv cfg |
+---------------------+--------------------------------+
                      |
                      v
            +-------------------+
            | External Features |
            | (Email console,   |
            | analytics widgets)|
            +-------------------+
```
---

### Data Model and Schema

**Data Model**
```
User (id, email, full_name, password_hash, role, ...)
  ├─< Property (id, manager_id, title, nightly_rate, status, approval_status, amenities JSON)
  │     └─< PropertyImage (id, property_id, file_path, is_primary)
  ├─< Reservation (id, property_id, tenant_id, manager_id, status, start_date, end_date)
  │     └─ Notification (id, user_id, title, body, type, is_read)
  └─< AuditLog (id, actor_id, action, entity, metadata_json)
SystemSetting / TwoFactorChallenge / PasswordResetRequest store security state scoped per user.
```

**Schema (JSON)**
```
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "campusKubo Data Model Schema",
  "description": "Comprehensive JSON Schema describing the primary data entities used by campusKubo.",
  "type": "object",
  "properties": {
    "users": {
      "type": "array",
      "items": { "$ref": "#/definitions/user" }
    },
    "listings": {
      "type": "array",
      "items": { "$ref": "#/definitions/listing" }
    },
    "reservations": {
      "type": "array",
      "items": { "$ref": "#/definitions/reservation" }
    },
    "activity_logs": {
      "type": "array",
      "items": { "$ref": "#/definitions/activity_log" }
    },
    "login_attempts": {
      "type": "array",
      "items": { "$ref": "#/definitions/login_attempt" }
    },
    "settings": {
      "type": "object",
      "additionalProperties": { "$ref": "#/definitions/setting" }
    }
  },
  "required": ["users", "listings"],
  "definitions": {
    "user": {
      "type": "object",
      "required": ["id", "email", "password_hash", "role", "created_at"],
      "properties": {
        "id": { "type": "integer", "minimum": 1 },
        "email": { "type": "string", "format": "email" },
        "password_hash": { "type": "string" },
        "role": { "type": "string", "enum": ["visitor", "tenant", "pm", "admin"] },
        "full_name": { "type": "string" },
        "deleted_at": { "type": ["string", "null"], "format": "date-time" },
        "created_at": { "type": "string", "format": "date-time" },
        "last_activity": { "type": ["string", "null"], "format": "date-time" },
        "profile_photo_url": { "type": "string", "format": "uri" }
      },
      "additionalProperties": false
    },

    "listing": {
      "type": "object",
      "required": ["id", "owner_id", "title", "address", "price", "status", "created_at"],
      "properties": {
        "id": { "type": "integer", "minimum": 1 },
        "owner_id": { "type": "integer", "minimum": 1 },
        "title": { "type": "string", "minLength": 1 },
        "address": { "type": "string" },
        "description": { "type": "string" },
        "price": { "type": "number", "minimum": 0 },
        "amenities": { "type": "array", "items": { "type": "string" }, "default": [] },
        "image_urls": { "type": "array", "items": { "type": "string", "format": "uri" }, "default": [] },
        "status": { "type": "string", "enum": ["draft", "pending", "approved", "rejected", "archived"] },
        "availability_status": { "type": "string", "enum": ["Available", "Reserved", "Unavailable"], "default": "Available" },
        "lodging_details": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "updated_at": { "type": ["string", "null"], "format": "date-time" }
      },
      "additionalProperties": false
    },

    "reservation": {
      "type": "object",
      "required": ["id", "listing_id", "user_id", "start_date", "end_date", "status", "created_at"],
      "properties": {
        "id": { "type": "integer", "minimum": 1 },
        "listing_id": { "type": "integer", "minimum": 1 },
        "user_id": { "type": "integer", "minimum": 1 },
        "start_date": { "type": "string", "format": "date" },
        "end_date": { "type": "string", "format": "date" },
        "status": { "type": "string", "enum": ["pending", "confirmed", "cancelled", "completed"] },
        "created_at": { "type": "string", "format": "date-time" },
        "notes": { "type": "string" }
      },
      "additionalProperties": false
    },

    "activity_log": {
      "type": "object",
      "required": ["id", "actor_id", "action", "created_at"],
      "properties": {
        "id": { "type": "integer", "minimum": 1 },
        "actor_id": { "type": ["integer", "null"] },
        "action": { "type": "string" },
        "metadata": { "type": ["object", "null"], "additionalProperties": true },
        "created_at": { "type": "string", "format": "date-time" }
      },
      "additionalProperties": false
    },

    "login_attempt": {
      "type": "object",
      "required": ["id", "user_email", "success", "attempt_time"],
      "properties": {
        "id": { "type": "integer", "minimum": 1 },
        "user_email": { "type": "string", "format": "email" },
        "success": { "type": "boolean" },
        "attempt_time": { "type": "string", "format": "date-time" },
        "ip_address": { "type": "string" },
        "user_agent": { "type": "string" }
      },
      "additionalProperties": false
    },

    "setting": {
      "type": "object",
      "required": ["key", "value", "updated_at"],
      "properties": {
        "key": { "type": "string" },
        "value": { "type": ["string", "number", "boolean", "object", "array", "null"] },
        "updated_at": { "type": "string", "format": "date-time" }
      },
      "additionalProperties": false
    }
  }
}

```
---

### Setup & Run Instructions
- Prerequisites: Python 3.11+ recommended. Windows / macOS / Linux supported. A virtual environment is strongly recommended.

Windows (PowerShell):
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app/main.py
```

Windows (cmd.exe):
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python app/main.py
```

macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

<i>Note: If using experimental AI features that call external APIs, add credentials to environment variables (e.g., `OPENAI_API_KEY`) or a local `.env` file and restart the app.</i>

---

### Testing Summary
- Test runner: `pytest` is used for unit tests located under `tests/`.
- Run tests:
```bash
pip install -r requirements.txt
pytest -q
```
Coverage notes: The repo contains unit tests for core services and views. Emerging features (real-time server, AI models) include only integration stubs by default — add integration tests against the simulated server or mock external APIs when enabling those features.

---

### Emerging Tech Explanation & Integration
This section enumerates the experimental / emerging features we can add, the rationale for choosing them, their integration approach, and limitations.

- **Data visualization** (interactive charts)
  - Why: Surface trends (bookings over time, occupancy rates, popular neighborhoods) for admin insight.
  - Integration: Use client-side charting via Flet components or embed small interactive charts (Plotly/Altair static images as fallback). Wire charts to aggregated data endpoints or in-memory events for near-real-time updates.
  - Limitations: Real-time charts need efficient aggregation; heavy datasets may require pre-aggregation or pagination.

---
### Technical Patterns & Responsibility
- Defensive integration: each external integration uses a wrapper service that handles retries, exponential backoff, circuit breaker (soft failure), and returns a deterministic fallback.
- Feature flags: emergent features gated behind config flags to allow safe rollout and A/B testing.

---

### Team Roles & Contribution Matrix
| member | Role | Primary contributions |
|---|---|---|
| R. Agnote | Backend | API endpoints, database operations, server-side logic, business rules |
| F. Enimedez | FLead Developer | Architecture, full-stack coordination, code review, technical leadership |
| J. Pontanares | Frontend | Interactive features, data visualization, client-side logic, user experience |
| M. Tercero | Backend | API development, database design, authentication, server-side security |

---

### Risk / Constraint Notes & Future Enhancements
- **Risks**:
  - SQLite suits small deployments; moving to PostgreSQL recommended for multi-user concurrency.
  - Background Python threads for UI updates are fragile — migrate to Flet timers or a proper event loop.

- **Constraints**:
  - Local file storage for images lacks durability and CDN performance; add object storage for production.
  - Client devices vary in capability — offline-first features must be carefully scoped.

- **Future Enhancements**:
  - Add a pluggable storage adapter (SQLite → PostgreSQL → Cloud DB)
  - Integrate APIs (Google Calendar for billing reminders, Google Maps for hotspots analyses, Google Mail for authentications)
  - Implement a microservice for real-time events and horizontal scaling
  - Add optional on-device ML models for image tagging or lightweight inference
  - Add analytic pipelines (ETL) for aggregated admin dashboards
---

### Individual Reflections
---
**R. Agnote** — Backend Setting up a tri-role experience also made me speak directly with real renters and managers in and around Rinconada. Listening to their related concerns regarding safety, convenience, and even fatigue allowed me to design the end backend flows, particularly the approval queue and amenity transparency. Flet allowed me to iterate quickly since I did not need to switch languages or frameworks all the time. However, the greatest lesson to me was ensuring that there is consistency in user experience on both desktop and web. In the future, I would like to investigate accessibility audit and test screen-reader compatibility to make the site more inclusive and reasonable to all users.


**F. Enimedez**— Lead Developer As a Lead Developer and project head, my role was to guide the team, set the workflow, and make sure all parts of the project came together smoothly. Looking back, I realize that the structure I provided wasn’t efficient enough. Because of that, our outputs were delayed, people got confused, and we ended up with conflicts in our code. It also didn’t help that coordinating with my team was difficult due to distance. Communicating online isn’t the same as working side by side, and a lot of things get lost along the way.
Through this experience, I learned how important it is to start with a proper meeting before anything else. Aligning expectations, responsibilities, and timelines early on could have prevented a lot of the issues we faced. I also realized the value of having a strong base structure, especially in something as critical as the database. Many of our conflicts came from having different db.py files and inconsistent logic. This experience was challenging, but it taught me how crucial clear workflow, early alignment, and solid foundations are in leading a project. It’s something I’ll carry moving forward.

**J. Pontanares** - Frontend Building the interactive features and data visualizations taught me how critical performance is to user experience. Every millisecond matters when users are browsing room options or viewing analytics dashboards. I focused on lazy loading, efficient DOM manipulation, and smooth animations to keep interactions responsive. Collaborating closely with F. Enimedez on API contracts ensured the frontend and backend stayed in sync, while we also work security requirements that shaped how I handled authentication states and sensitive data display. Next time, I'd establish a comprehensive component library upfront rather than building piecemeal—reusability and consistency would've saved significant refactoring time. I also learned that early user testing reveals UX friction points no amount of solo development catches. Moving forward, I want to dive deeper into accessibility standards and progressive enhancement techniques to ensure our applications serve all users effectively..

**M. Tercero** - Backend Threat modeling anchored our engineering, especially around spoofing and privilege escalation. Argon2 hashing, lockouts, and audit logs were non-negotiables. We also built scaffolding for 2FA and secure password resets even if they are still console-based. I learned the importance of layered defenses—even a Flet app benefits from classic OWASP hygiene.

---

### Acknowledgement
---
AI assistance was of assistance in building this system. It was used in adapting chart examples (PieChart, BarChart, LineChart) from Flet docs, drafting code snippets, report texts, and test files, as well as in debugging. External templates consulted: Flet PieChart, BarChart, LineChart (links below). Nonetheless, all AI-generated outputs were reviewed and validated by the project authors.

Flet PieChart: https://flet.dev/docs/controls/piechart/

Flet BarChart: https://flet.dev/docs/controls/barchart

Flet LineChart: https://flet.dev/docs/controls/linechart