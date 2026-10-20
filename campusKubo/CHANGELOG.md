# campusKubo - Changelog

All notable changes to this project will be documented in this file.

---
## [2.5.7] - 2025-12-16 (Pontanares)

### Changed
- `app/views/home_view.py` — removed search bar and filter controls; added shuffle mode for the featured grid.
- `app/views/browse_view.py` — updated browse list layout to display 4 items per row in the grid.
- `app/components/sidebar.py` — added sidebar navigation component.
- Layout adjustments across Home and Browse views to accommodate the new sidebar.
- Minor UI consistency and spacing refinements related to the new grid and navigation changes.


--- 
## [2.5.6] - 2025-12-16 (Pontanares)

### Changed
- Refactored and updated core UI components and forms for improved consistency and usability.
- **SignupForm** & **SignupView** — enhanced registration flow with role selection (Tenant / Property Manager), real-time password validation with visual feedback, Terms & Privacy links, loading indicators, and SnackBars.
- **LoginForm** — improved email/password validation, role-based navigation, and error handling.
- **Navbar** & **Logo** — updated layout, responsive behavior, back button handling, and branding improvements.
- **SearchFilter** & **AdvancedFilter** — refined multi-select property filters with dynamic search and live updates; supports amenities, room type, price range, and availability.
- **Listing** & **Footer** components — updated property card layout, styling, and footer links.
- **PasswordNotification** — enhanced visual feedback and dynamic updates during password input.
- Shared **COLORS** palette — centralized and standardized reusable colors, borders, and typography for consistent UI styling.




---
## [2.5.5] - 2025-12-16 (Enimedez)

### Changed
- Updated `README.md` to correct setup/test commands, clarify persistence (raw `sqlite3`), list test locations, and version bump to 2.5.5.
- `app/main.py` — startup and routing adjustments.
- `app/models/user.py` — user model updates (profile / verification fields).
- `app/services/admin_service.py`, `app/services/auth_service.py`, `app/services/notification_service.py`, `app/services/reservation_service.py` — service fixes and behavior sync.
- `app/state/session_state.py` — session handling and RBAC improvements.
- `app/storage/db.py`, `app/storage/file_storage.py` — PRAGMA hardening, migrations, and file storage path fixes.
- Updated tests under `app/tests/` to reflect behavior and API changes.

### Added
- `app/config/secrets.py` — runtime secret key helper.
- `app/storage/.env.example` — example environment variables for local setup.

---
## [2.5.4] - 2025-12-13 (Enimedez)

### Changed
- Updated README.md Setup & run section, removed credentials table, and version bump to v2.5.4.
- Removed Code_Documentation.md file from docs/CS 319/ containing redundant project information.

---

## [2.5.3] - 2025-12-13 (Agnote)

### Added
- Added updated documentation refinements to README.md and CHANGELOG.md for consistency and clarity.
- Added missing metadata alignment across documentation files.

### Changed
- Updated README.md version to reflect documentation updates and version bump to v2.5.3.
- Improved formatting, spacing, and section hierarchy in CHANGELOG.md for better readability.
- Standardized markdown structure and terminology across all documentation files.

### Fixed
- Fixed duplicated version entries in the changelog.
- Corrected inconsistent indentation and bullet formatting in older entries.

---

## [2.5.2] - 2025-12-11 (Tercero)

### Removed
- Removed multiple legacy documentation files from `docs/` to declutter the repository, including architecture, security, payments, system settings, and various implementation and status reports.
- Removed `docs/architecture.puml` and `docs/campuskubo_schema.json`.
- Removed unused sample images from `assets/uploads/` (`angel-luciano--hWwL0n3_As-unsplash.jpg`) and `assets/uploads/profile_photos/` (`profile_2.png`, `profile_3.png`, `profile_5.png`).

### Changed
- Updated `README.md` version to reflect documentation consolidation and repository cleanup in v2.5.2.

### Added
- Added `docs/README.md` as a consolidated documentation for the project.

---

## [2.5.1] - 2025-12-08 (Pontanares)

### Added
- **Configuration**
  - `app/config/colors.py` — Centralized color palette configuration for consistent theming across the application.
- **Views**
  - `app/views/property_details_view.py` — Property details page implementation.

### Changed
- **Database** (`app/storage/db.py`)
  - Modified database operations and schema adjustments.
- **UI/UX Improvements**
  - Updated `app/views/browse_view.py` — Enhanced browsing interface and layout.
  - Updated `app/views/property_details_view.py` — Refined property details page UI.
  - Updated `app/views/home_view.py` — Applied new color palette from centralized configuration.
  - Updated `app/views/login_view.py` — Refreshed login page styling with new color scheme.
  - Updated `app/views/signup_view.py` — Updated signup page design with consistent color palette.
- **Theming**
  - Implemented centralized color palette system across multiple views for consistent branding.
---
## [2.5.0] - 2025-12-08 (Enimedez)

### Added
- Bulk add of UI components and views for the user-facing app; see `app/components/` and `app/views/`.
- Database improvements and seeding behavior: `app/storage/db.py` and `app/storage/seed_data.py` were extended to support additional features and richer demo data.

### Changed
- Updated README and documentation to reflect the new files and seeded demo data.


---

## [1.5.0] - 2025-12-08 (Enimedez)

### Added
- `app/main.py` — Major update pushed: refactored application entry point and startup flow.

### Changed
- Updated `README.md` version to `v1.5.0` to reflect the main.py push and release.

---

## [0.4.1] - 2025-12-07 (Pontanares)

### Added
- **Views & UX**
  - `app/views/home_view.py` — Implemented home view with featured listings and calls-to-action.
  - `app/views/listing_detail_view.py`, `app/views/listing_detail_extended_view.py` — Added listing detail pages with image gallery and contact/reservation actions.
  - `app/views/login_view.py`, `app/views/signup_view.py` — Implemented authentication views with improved validation flows and redirects.

### Changed
- **UX Improvements**
  - Implemented enhanced user experience and validation across login/signup flows and listing interactions.

---

## [2.5.0] - 2025-12-08 (Enimedez)

### Added
- Bulk add of UI components and views for the user-facing app; see `app/components/` and `app/views/`.
- Database improvements and seeding behavior: `app/storage/db.py` and `app/storage/seed_data.py` were extended to support additional features and richer demo data.

### Changed
- Updated README and documentation to reflect the new files and seeded demo data.


---

## [1.5.0] - 2025-12-08 (Enimedez)

### Added
- `app/main.py` — Major update pushed: refactored application entry point and startup flow.

### Changed
- Updated `README.md` version to `v1.5.0` to reflect the main.py push and release.

---

## [0.4.1] - 2025-12-07 (Pontanares)

### Added
- **Views & UX**
  - `app/views/home_view.py` — Implemented home view with featured listings and calls-to-action.
  - `app/views/listing_detail_view.py`, `app/views/listing_detail_extended_view.py` — Added listing detail pages with image gallery and contact/reservation actions.
  - `app/views/login_view.py`, `app/views/signup_view.py` — Implemented authentication views with improved validation flows and redirects.

### Changed
- **UX Improvements**
  - Implemented enhanced user experience and validation across login/signup flows and listing interactions.

---

## [0.4.0] - 2025-12-07 (Pontanares)

### Added
- **UI Components**
  - `app/components/footer.py` — Implemented footer component with branding and contact information.
  - `app/components/navbar.py` — Created navbar component for site-wide navigation (login/register links).
  - `app/components/login_form.py` — Developed `LoginForm` with validation and user feedback.
  - `app/components/signup_form.py` — Added `SignupForm` with role selection and live password validation.
  - `app/components/reservation_form.py` — Introduced `ReservationForm` for booking listings with date selection.
  - `app/components/advanced_filters.py` — Built `AdvancedFilters` supporting multi-criteria property search.
  - `app/components/searchbar.py` — Added `SearchBar` for keyword and location-based queries.
  - `app/components/search_filter.py` — Implemented `SearchFilter` for quick access filter options.
  - `app/components/signup_banner.py` — Added `SignupBanner` to promote account creation on the homepage.
  - `app/components/listing_card.py` — Updated `ListingCard` to display property details, images, price, and action buttons.

---

## [0.3.0] - 2025-12-06 (Enimedez)

### Added
- **Database Module** (`storage/db.py`)
  - Complete SQLite database implementation with migrations
  - User management with secure password hashing
  - User profile updates with email validation
  - Listing management (CRUD operations)
  - Reservation system
  - Password reset tokens
  - Activity logging
  - Reports management
  - Admin utilities
  - Model-compatible adapter functions
  - Foreign key constraints and data integrity

- **Documentation**
  - `docs/CHANGELOG.md` - Version tracking and team contribution guide
  - Simplified versioning format for student team collaboration

### Changed
- **README.md** - Updated with project information and setup instructions

---

## [0.2.0] - 2025-12-02 (Enimedez)

### Added
- **Python Module Placeholders**
  - `.py` placeholder files added to all project folders:
    - **Components (9)**: footer, listing_card, login_form, navbar, notification_banner, reservation_form, search_filter, searchbar, signup_form
    - **Models (4)**: listing, notification, reservation, user
    - **Services (6)**: auth_service, gmaps_service, listing_service, notification_service, reservation_service, user_service
    - **State (2)**: app_state, session_state
    - **Storage (3)**: db, file_storage, seed_data
    - **Views (10)**: admin_dashboard_view, home_view, listing_detail_view, login_view, pm_dashboard_view, pm_profile_view, reservation_view, signup_view, user_profile_view
    - Organized modularity structure for scalable development

---

## [0.1.0] - 2025-12-01 (Enimedez)

### Added
- **Project Structure**
  - Folder structure setup for organized modularity
  - Placeholder `.py` files in all core directories:
    - `app/` - Main application
    - `app/views/` - View/page components
    - `app/components/` - Reusable UI components
    - `app/services/` - Business logic services
    - `app/models/` - Data models
    - `app/state/` - State management
    - `app/storage/` - Data persistence
    - `app/tests/` - Test suite
  - Root configuration files:
    - `README.md` - Project documentation
    - `requirements.txt` - Python dependencies
    - `.gitignore` - Git ignore rules

---

## Version Format

Simple versioning for team project:
- **0.1.0** - First major feature release
- **0.1.1** - Bug fixes and small improvements
- **0.2.0** - Next major feature added
- **0.2.1** - More bug fixes
- And so on...

### Categories

- **Added** - New features and functionality
- **Changed** - Changes in existing functionality
- **Fixed** - Bug fixes and corrections
- **Removed** - Removed features or functionality
- **Deprecated** - Features that will be removed in future versions
- **Security** - Security-related fixes or changes

---

## How to Update This Changelog

When making new commits or releases:

1. **Create a new version section** with date in `YYYY-MM-DD` format
2. **Include your name** in the version line (e.g., `[0.2.1] - 2025-12-10 (YourName)`)
3. **Organize by categories**: Added, Changed, Fixed, Removed
4. **Be specific**: Include file paths and descriptions
5. **Use format**: `[0.X.Y] - YYYY-MM-DD (Developer Name)`

### Example Entry Format

```markdown
## [0.2.1] - 2025-12-10 (Pontanares)

### Added
- **App** (`components and views`)
  - User management with secure password hashing
  - User profile updates with email validation
  - Listing management (CRUD operations)
  - Reservation system
  - Password reset tokens
  - Activity logging
  - Reports management
  - Admin utilities
  - Model-compatible adapter functions
  - Foreign key constraints and data integrity
  - **Components**: footer, listing_card, login_form, navbar, search_filter, searchbar, signup_form
  - **Views**: home_view, listing_detail_view, login_view, signup_view

### Changed
- Updated listing card styling
- Improved search performance

### Fixed
- Search result pagination issue
- Filter validation bug

### Removed
- Legacy search implementation
```

---

**Last Updated**: December 8, 2025
**Repository**: [campusKubo-Boarding-Bedspace-Finder-for-Students](https://github.com/ferenimedez-stab/campusKubo-Boarding-Bedspace-Finder-for-Students)