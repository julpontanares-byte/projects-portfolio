# FocusBreaker — Changelog

All notable changes to this project will be documented in this file.

## Add core modules, UI components, integration tests, and development scripts
- **Timestamp:** 2026-05-13
- **Author:** Enimedez
- **Branch:** main
- **Commit:** "chore: Add core modules, UI components, integration tests, dev scripts, and assets; update .gitignore"
- **What:** Added core focus-mode logic (scheduler, escape hatch, hot reload), UI components (achievements modal, session dialogs, streak celebration), integration and unit tests (conftest, integration suite, unit tests), development scripts (`dev.py`), and asset files (fonts, images). Local runtime artifacts (DB), large media, archived code, and draft documentation were intentionally excluded and listed in `.gitignore` for cleaner repository.
- **Files added (staged):**
  - `.gitignore`
  - `dev.py`
  - `main.py`
  - `assets/` (fonts, images)
  - `focusbreaker/core/__init__.py`
  - `focusbreaker/core/escape_hatch.py`
  - `focusbreaker/core/hot_reload.py`
  - `focusbreaker/core/scheduler.py`
  - `focusbreaker/data/__init__.py`
  - `focusbreaker/system/__init__.py`
  - `focusbreaker/ui/__init__.py`
  - `focusbreaker/ui/achievements_modal.py`
  - `focusbreaker/ui/floating_session.py`
  - `focusbreaker/ui/session_end_dialog.py`
  - `focusbreaker/ui/session_view.py`
  - `focusbreaker/ui/setup_dialog.py`
  - `focusbreaker/ui/streak_celebration.py`
  - `tests/conftest.py`
  - `tests/integration/`
  - `tests/ui/`
  - `tests/unit/test_escape_hatch.py`
  - `tests/unit/test_scheduler.py`

## Break Windows & Tray
- **Timestamp:** 2026-05-13
- **Author:** Tercero
- **Branch:** michelle/phase-3-ui
- **Commit:** "Add break windows, tray icon, and splash screen"
- **What:** Implemented break windows for all three modes (small pop-up for normal, full-screen for strict/focused) with media display integration. Built system tray icon with context menu and quick actions. Implemented loading splash screen with progress indication. Comprehensive UI tests for all interactive components.
- **Files:**
  - focusbreaker/ui/break_window.py
  - focusbreaker/ui/tray_icon.py
  - focusbreaker/ui/splash_screen.py

## Dialogs & Windows
- **Timestamp:** 2026-05-13
- **Author:** Tercero
- **Branch:** michelle/phase-3-ui
- **Commit:** "Add main window, task dialog, settings, and analytics"
- **What:** Completed main window with session manager integration and settings quick access. Implemented task creation/edit dialog with mode selection and break configuration. Built settings preferences dialog. Implemented analytics/history view for session tracking and statistics display.
- **Files:**
  - focusbreaker/ui/task_dialog.py
  - focusbreaker/ui/settings_dialog.py
  - focusbreaker/ui/analytics_dialog.py

## Core Logic Tests
- **Timestamp:** 2026-05-12
- **Author:** Agnote
- **Branch:** rovilyn/phase-2-core-logic
- **Commit:** "Add core logic tests and finalize input blocking"
- **What:** Completed comprehensive unit test suite for all core logic systems. Tests validate timer accuracy, mode rule enforcement, session transitions, streak tracking logic, and input blocker functionality. All tests pass with clean error handling.
- **Files:**
  - tests/unit/test_timer.py
  - tests/unit/test_mode_controller.py
  - tests/unit/test_session_manager.py
  - tests/unit/test_streak_manager.py
  - tests/unit/test_input_blocker.py

## Session & Streak Management
- **Timestamp:** 2026-05-12
- **Author:** Agnote
- **Branch:** rovilyn/phase-2-core-logic
- **Commit:** "Implement session manager, streak tracking, and input blocker"
- **What:** Implemented session manager with complete lifecycle management (creation, work, break, completion) and mode-based break scheduling. Built streak tracking system with milestone detection and reward calculation. Implemented input blocker for keyboard/mouse control during focus periods with escape hatch emergency exit support.
- **Files:**
  - focusbreaker/core/session_manager.py
  - focusbreaker/core/streak_manager.py
  - focusbreaker/system/input_blocker.py

## UI Foundation
- **Timestamp:** 2026-05-12
- **Author:** Enimedez
- **Branch:** main
- **Commit:** "Enhance main window behavior: show, raise, and activate after session; update break notification message"
- **What:** Updated the main window to show, raise, and activate after a session ends, and refined the break notification message.
- **Files:**
  - focusbreaker/main.py
  - focusbreaker/ui/main_window.py

## UI Foundation
- **Timestamp:** 2026-05-12
- **Author:** Enimedez
- **Branch:** main
- **Commit:** "Enhance main window behavior: show, raise, and activate after session; update break notification message"
- **What:** Updated the main window to show, raise, and activate after a session ends, and refined the break notification message.
- **Files:**
  - focusbreaker/main.py
  - focusbreaker/ui/main_window.py

## UI Foundation
- **Timestamp:** 2026-05-12
- **Author:** Tercero
- **Branch:** michelle/phase-3-ui
- **Commit:** "Implement UI styles, components, and start main window"
- **What:** Implemented comprehensive global styling system with theme colors and mode-specific style variants (normal/strict/focused). Built reusable UI components including progress ring, themed dialogs, buttons, and custom widgets. Started main window with layout foundation (sidebar, content area, timer display) and session information display.
- **Files:**
  - focusbreaker/ui/styles.py
  - focusbreaker/ui/components/dialogs.py
  - focusbreaker/ui/components/progress_ring.py
  - focusbreaker/ui/main_window.py

## Display Control & Tests 
- **Timestamp:** 2026-05-12 
- **Author:** Pontanares
- **Branch:** juliet/phase-1-backend
- **Commit:** "Add display control and finalize data layer tests"
- **What:** Implemented display control system with monitor detection and brightness adjustment. Completed comprehensive unit tests for database, audio, and media manager systems. All data persistence operations validated and tested.
- **Files:**
  - focusbreaker/system/display.py
  - tests/unit/test_display.py

## Timer & Mode Controller 
- **Timestamp:** 2026-05-12 
- **Author:** Enimedez
- **Branch:** main
- **Commit:** "Implement timer system and mode controller"
- **What:** Implemented tick-based timer system with time formatting (mm:ss, hh:mm:ss) and pause/resume support. Built mode controller with comprehensive per-mode rules and constraints. Defined break eligibility logic and permission rules (snooze, extend, skip) based on work mode.
- **Files:**
  - focusbreaker/core/timer.py
  - focusbreaker/core/mode_controller.py

## Audio & Media Systems 
- **Timestamp:** 2026-05-12 
- **Author:** Pontanares
- **Branch:** juliet/phase-1-backend
- **Commit:** "Add audio system and media manager"
- **What:** Implemented audio playback system with file detection, format support (WAV, MP3), volume control, and seamless playback integration. Built media manager for asset organization by mode (normal/strict/focused), file caching, and user upload handling.
- **Files:**
  - focusbreaker/system/audio.py
  - focusbreaker/system/media_manager.py

## Database Layer
- **Timestamp:** 2026-05-12 
- **Author:** Pontanares

## Database Layer
- **Timestamp:** 2026-05-12 
- **Author:** Pontanares
- **Branch:** juliet/phase-1-backend
- **Commit:** "Implement database layer with schema and CRUD operations"
- **What:** Implemented SQLite database manager with complete schema definition. Built CRUD operations for Task, WorkSession, Break, Streak, and Settings models. Added connection pooling, migration support, and transaction safety with comprehensive error handling.
- **Files:**
  - focusbreaker/data/db.py

### Initial Repo Setup
- **Timestamp:** 2026-05-12
- **Author:** Enimedez
- **Branch:** main
- **Commit:** "Initial repo setup with config, models, and main entry"
- **What:** Created initial repository structure with application configuration, data model definitions, and main entry point. Established project foundation for all team contributions.
- **Files:** focusbreaker/config.py, focusbreaker/data/models.py, focusbreaker/main.py, pyproject.toml, requirements.txt, CHANGELOG.md

## 2026-05-12 - Initial Development Sprint
---
