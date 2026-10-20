# Juliet Pontanares: Projects Portfolio

BS Computer Science, 4th Year
GitHub profile: [github.com/julpontanares-byte](https://github.com/julpontanares-byte)

This repository collects the team projects, collaborations, and laboratory activities I worked on, with the source code, documentation, and results for each one. The main computer vision project is **BuzzBee**, the other two projects are software development collaborations, and the Computer Vision laboratory activities are in [`cv-labs/`](cv-labs/).

---

## Projects at a glance

| Project | Type | What it does | Main tech | Folder | Original repo |
|---|---|---|---|---|---|
| **BuzzBee** | Computer Vision (team) | Vision-based sign recognition for a 4WD delivery robot | Python, YOLOv8, PyTorch, OpenCV | [`BuzzBee/`](BuzzBee/) | [pau-827/BuzzBee](https://github.com/pau-827/BuzzBee) |
| **campusKubo** | Application Development (team) | Boarding house and bedspace finder for students, with Tenant, Manager, and Admin portals | Python, Flet, SQLite, Argon2 | [`campusKubo/`](campusKubo/) | [ferenimedez-stab/campusKubo-Boarding-Bedspace-Finder-for-Students](https://github.com/ferenimedez-stab/campusKubo-Boarding-Bedspace-Finder-for-Students) |
| **FocusBreaker** | Desktop app (team) | Customizable productivity timer with scheduled breaks, streaks, and work modes | Python, PySide6 / Flet, SQLite | [`focusBreakerv2/`](focusBreakerv2/) | [ferenimedez-stab/focusBreakerv2](https://github.com/ferenimedez-stab/focusBreakerv2) |

---

## 1. BuzzBee: Vision-Based Autonomous 4WD Delivery Robot

**Course:** Computer Vision, BS Computer Science 4A · **Instructor:** Elena Clarexe Gulane

**Team:** Ven John Rey Lavapie, Ivy Pauline Muit, Ayelyn Janne Panliboton, Juliet Pontanares, Rhea Lizza Sanglay

### Overview
A camera-based system that detects and recognizes five types of indoor signs so a delivery robot can tell where to stop and what to avoid. The same destination sign means *stop* or *continue* depending on the robot's assigned destination.

| Class | Meaning |
|---|---|
| `exit` | Exit sign (destination marker) |
| `mens_restroom` | Men's restroom (destination marker) |
| `womens_restroom` | Women's restroom (destination marker) |
| `no_entry` | Restricted area (always stop and turn away) |
| `slippery_floor` | Hazard (slow down) |

### Methodology
1. **Dataset:** KPDL – The Indoor Signs (Roboflow Universe), cleaned from 7 to 5 classes (686 images), plus our own 35 unseen test photos.
2. **Preprocessing:** resize and letterbox to 640×640, BGR to RGB, and scale pixels to 0–1. Training used the Ultralytics default augmentation (mosaic, flip, color jitter, scaling).
3. **Model:** YOLOv8n fine-tuned from COCO-pretrained weights (transfer learning), trained for 50 epochs on Google Colab (Tesla T4).
4. **Evaluation:** precision, recall, mAP, and confusion matrices on the held-out test split and on a separate unseen set.
5. **Output:** bounding boxes, class labels, and confidence scores on images or live webcam frames, plus a simulated decision step (stop, slow down, continue).

### Results

| Set | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|
| Test split (104 images) | 0.923 | 0.932 | 0.957 | 0.812 |
| Unseen set (35 images) | 0.747 | 0.329 | 0.327 | 0.211 |

The model performs very well on the held-out test split but drops on our own unseen photos. `slippery_floor` generalizes well (mAP@0.5 of 0.995 on the unseen set), while restroom and no-entry signs are often missed or labeled `exit`. More varied training images would be needed to fix this.

### Status
Midterm stage (SEE → RECOGNIZE) is complete. Robot hardware, motor control, and autonomous behavior belong to the Final stage.

**Details, setup, and usage:** [`BuzzBee/README.md`](BuzzBee/README.md)

---

## 2. campusKubo: Boarding and Bedspace Finder for Students

**Team:** BoardGirls

### Overview
A Flet (Python) application that helps students find boarding houses while giving property managers and administrators the tools to run the platform safely. It has three role-based portals:

- **Tenant:** advanced filtering, reservations with automatic capacity updates, notifications, and an AI-assisted recommendation widget.
- **Manager:** listing creation and editing, amenities and capacity management.
- **Admin:** listing approvals, role-based access control, user management, and audit logging.

### Highlights
- Argon2 password hashing, password policy, account lockout, and audit logs
- SQLite storage with WAL journaling and seeded demo data
- Analytics cards and charts for bookings, revenue, and occupancy
- Pytest suite with 8 tests (3 unit and 5 integration/functional)

**Details, setup, and usage:** [`campusKubo/README.md`](campusKubo/README.md)

---

## 3. FocusBreaker: Productivity Timer

### Overview
A customizable productivity timer inspired by the Pomodoro technique. It schedules automated breaks, tracks streaks, and offers three work modes:

- **Normal:** 25-minute work intervals and 5-minute breaks, with snooze and skip.
- **Strict:** 52-minute work intervals, 17-minute breaks, and full-screen overlays.
- **Focused:** deep work with no breaks until the end, followed by mandatory breaks.

### Highlights
- Randomized break media (videos and images) and a streak and quality-score system
- Session history and analytics dashboard
- System tray integration and a settings panel
- Test suite covering the timer, scheduler, session manager, streaks, and mode controller

**Details, setup, and usage:** [`focusBreakerv2/README.md`](focusBreakerv2/README.md)

---

## Computer Vision laboratory activities

Individual Google Colab notebooks from the Computer Vision course are in [`cv-labs/`](cv-labs/). The full list of activities, with a summary of each, is in [`cv-labs/README.md`](cv-labs/README.md).

---

## Repository structure

```
projects-portfolio/
├── README.md            # this file
├── BuzzBee/             # computer vision: YOLOv8 sign recognition
├── campusKubo/          # Flet app: boarding house finder
├── focusBreakerv2/      # productivity timer app
└── cv-labs/             # Computer Vision laboratory activities (Colab notebooks)
```

Each folder contains its own README with installation steps, usage, and documentation.

## Topics

`computer-vision` · `yolov8` · `object-detection` · `deep-learning` · `opencv` · `python` · `robotics` · `portfolio`

## Notes and attribution

- These projects were developed with teammates. Each project's folder was imported with its full commit history, so the original contributors are credited in the Git log.
- The BuzzBee dataset is based on *KPDL – The Indoor Signs* (Roboflow Universe, CC BY-NC-SA 4.0), used for non-commercial coursework with attribution.
- Ultralytics YOLOv8 and OpenCV are used under their respective licenses.