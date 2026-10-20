**Software Requirements Specification (SRS) — campusKubo**

Last updated: 2025-12-09

Purpose
-------
This SRS captures the functional and non-functional requirements for campusKubo — a boarding/bedspace listing and reservation platform for students. It also documents a concise security appendix covering threat modeling (STRIDE), input validation, password hashing parameters, session controls, logging & monitoring, error handling, and mitigations against common OWASP Top 10 risks relevant to this project.

**1. Functional Requirements**
- **User registration & authentication**: Users can sign up (email + password) and sign in. Roles supported: Visitor (not signed in), Tenant, Property Manager (PM), Admin.
- **Role-based access control (RBAC)**: Pages and API endpoints enforce permissions (Admin, PM, Tenant) so unauthorized users receive a 403 view.
- **Browse listings**: Search and filter listings (location, price range, room type, amenities, availability). Results update live while typing with debounce.
- **Listing detail view**: Users can view a listing detail page with images and booking/reservation actions (reserve only when signed in).
- **Property management (PM)**: PMs can create/edit/delete their listings and manage reservations for their properties.
- **Tenant dashboard**: Tenants can manage profile, view and cancel reservations, save listings, and message PMs.
- **Admin dashboard**: Admins can view platform statistics, manage users, and moderate listings/reports.
- **Reservations & payments (placeholder)**: Reservation workflow exists; payment integration is stubbed or integrated with external provider (scope depends on deployment plan).
- **Notifications**: In-app notifications for reservations, messages, and admin actions.
- **Data persistence**: SQLite (development) with schema migrations; soft-delete for important records (users, listings) to support recovery.

**2. Non-Functional Requirements**
- **Availability**: Target uptime 99% during business hours; use local WAL mode for SQLite and plan for migration to PostgreSQL for production.
- **Performance**: Search responses <200ms for cached queries; use debounce (300ms) on live search to limit DB load.
- **Scalability**: Design for migration to client-server DB and stateless web tier (session store) when scaling beyond single-host.
- **Usability**: Responsive UI; quick live search, clear error messages (non-sensitive), role-appropriate navigation.
- **Maintainability**: Modular code structure (`views/`, `services/`, `storage/`, `components/`) and tests covering core services. Use clear docstrings and SRS for future developers.
- **Security**: Strong password hashing, session timeout and renewal, RBAC enforcement, input validation, and logging/monitoring with no sensitive data leakage.

**3. Threat Model (STRIDE)**
The table below lists primary threats and recommended mitigations.

STRIDE Summary

S - Spoofing
- Threat: Attacker impersonates a legitimate user to access resources.
- Mitigations: Secure authentication; hashed passwords with Argon2; optional MFA; strong password policy and rate limiting on login; session tokens tied to user and short inactivity timeout.

T - Tampering
- Threat: Modification of data in transit or in storage (e.g., tampered listing details).
- Mitigations: Use parameterized queries to avoid SQL injection; enable DB integrity checks; sign or validate critical data server-side; use TLS in production.

R - Repudiation
- Threat: Users deny actions (e.g., cancellation) because no audit trail exists.
- Mitigations: Log critical actions (create/update/delete reservations, logins, admin actions) with timestamps and user IDs.

I - Information disclosure
- Threat: Sensitive data leakage (passwords, PII) in logs, errors, or API responses.
- Mitigations: Never log raw passwords; redact PII from logs; sanitize stack traces before display; follow the least privilege for data access.

D - Denial of Service
- Threat: Excessive resource consumption (e.g., aggressive live-search requests).
- Mitigations: Debounce live-search (300ms), rate limit endpoints, use connection / query timeouts, and limit results page size.

E - Elevation of Privilege
- Threat: Non-admin user gains admin privileges via insecure checks.
- Mitigations: Centralized RBAC (`SessionState.require_role()`), server-side permission checks on every protected operation, tests to validate role boundaries.

Notes: STRIDE analysis should be revisited for production changes (e.g., adding payment gateway, third-party integrations).

**4. Input Validation & Sanitization Strategy**
- Always validate input on server-side regardless of client validation.
- Use a whitelist approach: accept only expected fields and types. For example, accept numeric types for `price`, bounded ranges for `price_max` and `slider` values, and enumerations for `role`, `status`, `availability`.
- Sanitize strings used for HTML output to prevent XSS. Escape content in templates or use UI framework sanitized text components.
- Use parameterized SQL queries everywhere (already used in `storage/db.py`) to prevent SQL injection.
- Validate file uploads (images): check MIME type, extension whitelist, maximum size, scan for malware, and store outside webroot or with randomized filenames.

**5. Password Hashing Algorithm & Parameters**
- Algorithm: Argon2id (preferred) with Argon2 library where available; fallback to SHA-256 only for legacy compatibility in development (but do not use SHA-256 in production).
- Example recommended Argon2 parameters for modern hardware (2025 baseline):
  - time_cost = 3
  - memory_cost = 65536 KB (64 MB)
  - parallelism = 4

Justification: These parameters provide a balance between CPU/memory hardness and server throughput. Memory-hard hashing increases cost for GPU/ASIC attackers. Choose final parameters based on your production server capacity and expected authentication load. Re-evaluate periodically.

Migration note: When migrating a SHA-256 legacy user, re-hash on next successful login with Argon2.

**6. Session Management Controls**
- Session lifetime: inactivity timeout configurable — for development earlier versions used 60 minutes; tuneable via `SESSION_TIMEOUT_MINUTES`. For interactive UI consider 30 minutes default for production, shorter for high-risk flows.
- Renewal: Update session activity timestamp on authenticated actions (already implemented by `SessionState._update_last_activity()`), and refresh session time on explicit user actions.
- Logout: Provide explicit logout which clears session server-side entries.
- Session storage: For single-host use `page.session` (Flet). For multi-host or production, store sessions in a shared store (Redis) and use secure session cookies.
- Cookie flags (if using Flask or HTTP): Use `Secure`, `HttpOnly`, `SameSite=Strict` or `Lax` depending on your cross-site needs. Always set `Secure` in TLS environments.

**7. Logging & Monitoring Scope**
- Log events (audit): logins (success/failure), user creation/deletion, listing create/edit/delete, reservations create/cancel, admin actions, and payment events.
- Avoid logging sensitive data: never log raw passwords, full payment card details, or personal identifiers beyond what’s necessary for audit.
- Log format: structured JSON logs (timestamp, level, event, user_id, ip, request_id) to ease ingestion.
- Monitoring: set up alerting for repeated failed logins, high error rates (5xx), slow database queries, or high memory/cpu.
- Retention: follow privacy laws — keep audit logs for the minimum required period and/or archive them securely.

**8. Error Handling & Sensitive Data Leakage**
- Return user-friendly error messages to clients that do not disclose internal state or stack traces.
- On server-side, capture stack traces and write to secure logs with restricted access for debugging.
- Validation errors: return field-level messages without exposing raw SQL or internal identifiers.
- On authentication failure, respond with a generic message like "Incorrect email or password" to avoid username enumeration.

**9. Defenses Against Relevant OWASP Top 10 (selected items)**
- A1: Broken Access Control — enforce RBAC in `main.py` route handler and re-check permissions in service layer. Use role checks on all sensitive operations (delete user, admin endpoints, PM-only actions).
- A2: Cryptographic Failures — use TLS in production; use Argon2id for password storage; do not store plaintext credentials.
- A3: Injection — use parameterized queries (sqlite3 `?` placeholders) everywhere in `storage/db.py` (already done).
- A5: Security Misconfiguration — avoid debug or verbose error responses in production; set secure default headers and cookie flags; configure DB with WAL and PRAGMAs for integrity.
- A6: Vulnerable and Outdated Components — keep dependencies (Flet, Argon2) up-to-date and track CVEs.
- A7: Identification and Authentication Failures — implement rate-limiting on login attempts, lockouts, and optional MFA for critical roles (admins/PMs).
- A8: Software and Data Integrity Failures — validate uploads, sign important data if needed, perform DB migrations safely with schema checks.
- A9: Security Logging and Monitoring Failures — produce meaningful audit logs and alerts for suspicious behavior.
- A10: Server-Side Request Forgery (SSRF) — restrict outbound network calls (e.g., image fetching or geocoding) and validate target URLs.

Architectural notes and recommendations
-------------------------------------
- For production deployments, replace SQLite with a client/server DB (PostgreSQL) and use a shared session store (Redis) plus reverse proxy (NGINX) to set TLS and headers.
- Add centralized configuration for security parameters (Argon2 settings, session timeout, lockout duration) via environment variables.
- Add a `security.md` with operational runbooks for incident response and a privacy/data retention policy.

Appendix: Quick checklist for deployment
- Ensure TLS termination at edge (Let’s Encrypt or managed TLS).
- Set cookie `Secure` and `HttpOnly` flags when using HTTP cookies.
- Configure Argon2 parameters suitable to server capacity.
- Enable logging to a centralized, access-controlled system.
- Add monitoring/alerting for repeated login failures and anomalous traffic.

Contact / Ownership
- Owners: Team BoardGirls
