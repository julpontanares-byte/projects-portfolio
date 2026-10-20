# campusKubo — Boarding & Bedspace Finder

CampusKubo is a Flet (Python + Flutter rendering) experience that helps Rinconada students quickly find boarding houses while giving property managers and administrators the tools they need to operate safely. The build in this repository delivers three complete role-based portals (Tenant, Manager, Admin), persistent SQLite storage, role-aware RBAC, analytics, and an AI-assisted recommendation widget that surfaces the best listings for each tenant.

---

## Why it exists

- **Students** need a trusted directory that exposes price, amenities, and availability without travelling to every barangay.
- **Property managers** need a lightweight back office to upload listings, toggle availability, and answer reservation requests.
- **Admins** need screening controls so only verified listings go live and platform health can be monitored.

---

## Core capabilities

- **Secure onboarding** — Argon2 password hashing, password policy enforcement, lockout, and optional 2FA scaffolding.
- **Tenant workspace** — advanced filtering, reservation workflow with automatic capacity updates, and notification center.
- **Manager workspace** — listing creation/editing, amenity + capacity management, and pending status view.
- **Admin workspace** — listing approvals, RBAC controls, user disablement, and security/audit logging.
- **Emerging tech add-ons** — interactive insight cards and charts for bookings/revenue/occupancy.
- **Persistence + logging** — SQLite3 via a raw `sqlite3` layer, audit log for privileged actions, WAL journaling and PRAGMA hardening, plus seeded demo data on first launch.

---

## Tech stack

| Layer | Choice |
| --- | --- |
| UI | [Flet 0.28.3](https://flet.dev/) (desktop + web rendering) |
| Language | Python 3.11 |
| Persistence | SQLite3 |
| Security | Argon2 via `passlib`, `itsdangerous` tokens, session manager |
| Tests | Pytest (8 test cases: 3 unit + 5 integration/functional) |

---

## Project map

```
app/
├── main.py               # Flet entrypoint + navigation scaffolding
├── config/               # Settings loader (.env) and runtime directories
├── models/               # Data models and domain entities (SQLite-backed)
├── services/             # Domain logic (auth, property, reservation, AI recs, insights)
├── state/                # In-memory session + view models
├── storage/              # Engine bootstrap + seeding helpers
├── utils/                # Security helpers (hashing, OTP, tokens)
├── tests/                # Pytest suites (unit + integration)
── assets/               # Static uploads
── docs/                 # Reports, test matrices
```

---

## Setup & run

```bash
git clone <repo-url>
cd campusKubo-final
python -m venv .venv
.venv\Scripts\activate      # use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cd app
cp .env.example .env         # adjust secrets if needed
python main.py               # launches the Flet desktop
```

> Tip: when running command-line utilities (tests, scripts), execute them from the repository root and reference modules inside the `app/` directory.

---

## Running the automated tests

```bash
cd campusKubo-final
.venv\Scripts\activate
python -m pytest app/tests
```

The suite contains:

- User service coverage (password hashing, policy enforcement, RBAC helpers).
- Property search filtering edge cases.
- Authentication flow (happy path + audit logging).
- Reservation lifecycle (creation, cancellation, availability sync).

Manual exploratory tests, coverage notes, and integration scenarios live in `docs/MANUAL_TEST_PLAN.md`.

---

## Documentation bundle

`app/docs/PROJECT_REPORT.md` contains:

- Project overview & scope decisions
- Threat model + mitigations (OWASP-focused)
- Architecture + ERD diagrams (ASCII)
- Data model + configuration reference
- Emerging tech rationale + limitations
- Testing summary + metrics
- Risk register, future work, and team contribution matrix
- Individual reflection snippets per member

Additional files:

- `MANUAL_TEST_PLAN.md` — step-by-step manual verification checklist
- `ARCHITECTURE.drawio.png` (optional) — add if you export the diagram from the text spec

---

## How to Contribute

To keep our `main` branch stable and organized, please follow this Git workflow:

### 1. Fork the Repository
Click the **Fork** button at the top-right of this repository to create your own copy.

### 2. Clone Your Fork
```bash
git clone https://github.com/<your-username>/campusKubo-Boarding-Bedspace-Finder-for-Students.git
cd campusKubo-Boarding-Bedspace-Finder-for-Students
```

### 3. Add Upstream Remote
```bash
git remote add upstream https://github.com/ferenimedez-stab/campusKubo-Boarding-Bedspace-Finder-for-Students.git
```

### 4. Create a Feature Branch
Always create a new branch for each feature or fix:
```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - for new features (e.g., `feature/search-filter`)
- `fix/` - for bug fixes (e.g., `fix/login-error`)
- `docs/` - for documentation (e.g., `docs/update-readme`)

### 5. Make Your Changes
- Implement your feature, bug fix, or documentation update
- Write clear, descriptive commit messages
- Test your changes before committing

### 6. Commit Your Changes
```bash
git add .
git commit -m "Add search filter by price feature"
```

### 7. Keep Your Branch Updated
Before pushing, sync with upstream:
```bash
git fetch upstream
git rebase upstream/main
```

### 8. Push Your Branch
```bash
git push origin feature/your-feature-name
```

### 9. Open a Pull Request
1. Go to your fork on GitHub
2. Click **New Pull Request**
3. Set base repository to `ferenimedez-stab/campusKubo-Boarding-Bedspace-Finder-for-Students.git`
4. Set base branch to `main` and compare branch to your feature branch
5. Add a clear title and description of your changes
6. Submit the PR

### 10. Review & Merge
- Team members will review your PR
- Address any requested changes
- Once approved, it will be merged into `main`

### Important Notes
- **Never push directly to `main`**
- Keep your fork synced regularly:
```bash
git remote add upstream https://github.com/ferenimedez-stab/campusKubo-Boarding-Bedspace-Finder-for-Students.git
git checkout main
git pull upstream main
git push origin main
```
- Write meaningful commit messages
- Test your code before creating a PR
- Follow the existing code style and structure

---

## Testing

Run tests using:
```bash
cd app
python -m pytest tests/
```

Minimum testing requirements:
- At least 3 unit tests for core logic
- At least 2 functional/integration tests
- Manual exploratory test checklist in documentation

---

## License

This project is developed for academic purposes as part of CCCS 106 (Application Development and Emerging Technologies), CS 319 (Information Assurance and Security), and CS 3110 (Software Engineering) joint collaboration.

---

## Acknowledgements

- Developed by **BoardGirls** team
- Built with [Flet Framework](https://flet.dev/)
- Inspired by student accommodation platforms
- Special thanks to our instructors and collaborators
- Some parts are AI-assisted

---

## Support

For questions or issues:
1. Check existing issues in the repository
2. Create a new issue with a clear description
3. Contact the team through the course channels

---

**Last Updated**: December 16, 2025

**Version**: v2.5.7