# Focus Breaker App v2.0.0 [Main Application Running]
**Last Updated:** 2026-05-12

FocusBreaker is a customizable productivity timer app built with Python and PySide6. Inspired by the Pomodoro technique, it aims to help its user stay in track of the time they spend working by scheduling automated breaks, tracking streaks, and offering different modes (normal, strict, focused) to prevent burnout.

**Current Status**: Main application successfully running with database initialization, asset management, first-time setup, and main window display. UI development in progress.

**Development Approach**: Started with data layer (db/models), then core business logic modules, then centralized configuration in config.py and revised core modules to use config constants, then system integration, now working on completing UI components.

## Features

- **Task Management**: Create tasks with names, durations, and work modes.
- **Three Work Modes**:
  - **Normal Mode**: Flexible with 25-minute work intervals and 5-minute breaks. Includes snooze/skip options.
  - **Strict Mode**: Enforced with 52-minute work intervals, 17-minute breaks, and mandatory cooldowns. Full-screen overlays.
  - **Focused Mode**: Deep work with no breaks until the end, followed by mandatory breaks.
- **Break Media System**: Randomized media playback (videos/images) during breaks, including default media and user uploads.
- **Streak System**: Track session streaks, perfect sessions, and daily consistency with quality scores.
- **Emergency Escape Hatch**: Hidden key combo for emergencies in strict/focused modes (with consequences).
- **Analytics & History**: Session history, visualizations (charts/heatmaps), and statistics dashboard.
- **System Tray Integration**: Background operation with tray menu for quick access.
- **Settings Panel**: Customize timings, audio/visual controls, media management, and advanced options.

## Installation

### Prerequisites
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (for dependency management)

### Setup
1. Clone the repository:
   ```
   git clone https://github.com/ferenimedez-stab/Focus-Breaker.git
   cd Focus-Breaker
   ```

2. Install dependencies:
   ```
   uv sync
   ```

## Usage

### Run as Desktop App
```
python src/main.py
```

### Run as Web App (via Flet)
```
uv run flet run
```

- Start a timer, select a mode, and let FocusBreaker guide your productivity sessions.
- Customize settings via the UI for intervals, media, and notifications.

## Building

### Android APK
```
flet build apk -v
```

### iOS IPA
```
flet build ipa -v
```

### macOS App
```
flet build macos -v
```

### Linux Package
```
flet build linux -v
```

### Windows EXE
```
flet build windows -v
```

For detailed build instructions, see the [Flet Documentation](https://docs.flet.dev/).

## Project Structure

```
focusBreaker/
├── docs/
│   └── specification.md          # Complete feature spec and progress tracking
├── pyproject.toml                # Project configuration and dependencies
├── README.md                     # This file - project overview and setup
├── src/
│   ├── assets/                   # Media files and app assets (pending)
│   │   ├── icon.png
│   │   ├── media/
│   │   └── splash_android.png
│   ├── config.py                 # Centralized configuration settings
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── escape_hatch.py       # Emergency exit system
│   │   ├── mode_controller.py    # Work mode management
│   │   ├── scheduler.py          # Break scheduling logic
│   │   ├── session_manager.py    # Session lifecycle management
│   │   ├── streak_manager.py     # Streak calculations and tracking
│   │   └── timer.py              # Enhanced timer implementation
│   ├── data/                     # Data layer
│   │   ├── __init__.py
│   │   ├── db.py                 # Database operations and analytics
│   │   └── models.py             # Data models and schemas
│   ├── main.py                   # Application entry point with full initialization
│   ├── requirements.txt          # Python dependencies
│   ├── system/                   # System integrations
│   │   ├── audio.py              # Audio playback and controls
│   │   ├── display.py            # Screen brightness and overlays
│   │   └── input_blocker.py      # Input blocking for strict mode
│   ├── tests/                    # Test suite
│   │   ├── __init__.py
│   │   ├── test_escape_hatch.py
│   │   ├── test_mode_controller.py
│   │   ├── test_scheduler.py
│   │   ├── test_session_manager.py  # 16 comprehensive tests
│   │   ├── test_streak_manager.py
│   │   └── test_timer.py
│   └── ui/                       # User interface
│       ├── analytics.py          # Analytics dashboard (backend ready)
│       ├── break_window.py       # Break notification windows
│       ├── main_window.py        # Main application window
│       └── settings.py           # Settings panel
```

## Specification

For the complete feature plan, technical details, and current progress tracking, see [docs/specification.md](docs/specification.md).


---

**Version:** 1.4.0  
**Last Updated:** May 11, 2026  
**Status:** Core Implementation Complete - System Integration Complete - UI Fully Integrated - Break Enforcement Active