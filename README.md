# Vision-Based Autonomous 4WD Delivery Robot

> **Current stage:** Midterm (SEE → RECOGNIZE). The Final stage (SEE → DECIDE → ACT) sections are marked **[Final]** and will be completed later.
> Replace every `[bracketed placeholder]` and remove every `TODO` before the Final submission.

## Group Members

| Name | Role / Contribution |
|---|---|
| Ven John Rey Lavapie | [e.g., dataset preparation] |
| Ivy Pauline Muit | [e.g., model training] |
| Ayelyn Panliboton | [e.g., evaluation and testing] |
| Juliet Pontanares | [e.g., live demo / inference code] |
| Rhea Lizza Sanglay | [e.g., report and documentation] |

**Course:** Computer Vision, BS Computer Science – 4A
**Instructor:** Elena Clarexe Gulane

## Assigned Specialization

**Delivery Robot.** The vision system must recognize destination markers so the robot can decide where to go (Final).

## Project Description

This project develops a camera-based vision system for a 4WD mobile delivery robot. The system detects and recognizes indoor signs that act as destination markers and zone markers (for example, restrooms and exits as delivery points, and restricted or hazardous zones to avoid).

- **Midterm:** a working computer vision pipeline that captures an image or live camera frame, preprocesses it, detects and recognizes the signs, and displays the result visually (bounding box, class label, confidence score).
- **Final [Final]:** the recognized sign is converted into a robot decision and action (SEE → DECIDE → ACT), with motor control and autonomous behavior on the physical 4WD robot.

## System Overview

```
Camera / Image → Preprocessing → YOLOv8 Detector → Detection / Recognition → Visual Output
                                                                    │
                                          [Final] → Decision Logic → Robot Control → Motors
```

TODO: replace with the group's actual system diagram (also add it to the report, Section 2.1).

## Hardware Used

**Midterm**

| Component | Specification / Model | Purpose |
|---|---|---|
| Camera | Laptop webcam ([model]) | Live image input for the demo |
| Computer | [Laptop model, CPU/GPU, RAM] | Training and inference |

**Final [Final]**

| Component | Specification / Model | Purpose |
|---|---|---|
| 4WD chassis | [model] | Robot platform |
| DC motors | [model] | Movement |
| Motor driver | [model] | Motor control |
| Microcontroller | [Arduino / ESP32 / Raspberry Pi] | Receives commands, drives motors |
| Camera | [USB webcam / Pi camera / ESP32-CAM] | Robot vision |
| Power source | [battery type] | Power |

## Software and Tools

| Tool | Version | Purpose |
|---|---|---|
| Python | [3.x] | Main programming language |
| Ultralytics (YOLOv8) | [version] | Model training and inference |
| OpenCV | [version] | Image capture, preprocessing, visualization |
| NumPy | [version] | Numerical processing |
| Roboflow (website) | n/a | Source of the base dataset |
| Arduino IDE **[Final]** | [version] | Motor controller code |

## Computer Vision Methodology

1. **Dataset:** a public indoor-sign dataset, cleaned to 5 classes, plus our own unseen test photos.
2. **Preprocessing:** [Auto-orient and resize to 640×640 (from the source dataset); describe any additional steps the group applies, e.g., normalization or augmentation.]
3. **Model:** YOLOv8 object detector fine-tuned on our dataset (transfer learning from pretrained weights).
4. **Evaluation:** precision, recall, mAP, F1-score, and confusion matrix on the test set and on our separate unseen set.
5. **Output:** bounding boxes, class labels, and confidence scores drawn on the image or live frame.

TODO: confirm the final model size (e.g., yolov8n or yolov8s) and training settings, then update this section and Section 4 of the report.

## Dataset Overview

- **Base dataset:** KPDL – The Indoor Signs, version 11 (Roboflow Universe)
- **Link:** https://universe.roboflow.com/g-lcuz4/kpdl-the-indoor-signs/dataset/11
- **License:** CC BY-NC-SA 4.0 (attribution required, non-commercial, share-alike)
- **Format:** YOLOv8 (bounding boxes)
- **Modification:** the original dataset has 7 classes. We kept 5 and removed the other 2, and renumbered the remaining class IDs from 0 to 4.

### Target Classes (tentative, TODO: confirm after checking image counts)

| ID | Class | Meaning | Role in the delivery scenario |
|---|---|---|---|
| 0 | `exit` | Exit sign | Destination |
| 1 | `wc nam` | Men's restroom | Destination |
| 2 | `wc nu` | Women's restroom | Destination |
| 3 | `khong phan su mien vao` | No entry for unauthorized persons | Restricted zone |
| 4 | `tron truot` | Slippery floor | Hazard zone |

Removed classes: `cam hut thuoc` (no smoking) and `cam lua` (no fire). [State the reason, e.g., not relevant to robot navigation.]

### Dataset Splits

| Set | Images | Percentage | Purpose |
|---|---|---|---|
| Training | [n] | [%] | Model learns from these |
| Validation | [n] | [%] | Tuning and model selection |
| Testing | [n] | [%] | Final held-out score |
| **Unseen test** | [n] | n/a | Our own photos from different places and conditions, never used in training or validation |

See [`dataset/README.md`](dataset/README.md) for per-class counts, the cleaning procedure, and how the unseen set was collected.

## Model / Algorithm

- **Architecture:** YOLOv8 [n / s / m]
- **Pretrained weights:** [yolov8n.pt (COCO)]
- **Trained weights:** see [`models/README.md`](models/README.md)
- **Recognized classes:** exit, wc nam, wc nu, khong phan su mien vao, tron truot

## System Architecture / Workflow

**Midterm:** Camera frame or image → Preprocessing → YOLOv8 inference → Detections (box, class, confidence) → Visual output.

**Final [Final]:** Camera → YOLOv8 → Recognized sign → Decision logic → Command to controller → Motor driver → Motors → Robot action.

TODO [Final]: add the decision table (sign → robot action) and the robot control flowchart.

## Installation and Setup

```bash
# 1. Clone the repository
git clone [repository URL]
cd [repository folder]

# 2. (Recommended) create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

The dataset is already included in `dataset/` (see its README). No Roboflow API key is needed.

## Running the System

> TODO: update the file names below to match the actual scripts once they are written.

```bash
# Train
yolo detect train data=dataset/data.yaml model=yolov8n.pt epochs=[n] imgsz=640

# Evaluate on the test set
yolo detect val model=models/best.pt data=dataset/data.yaml split=test

# Evaluate on the unseen set
yolo detect val model=models/best.pt data=dataset/data_unseen.yaml split=test

# Live demo (laptop webcam)
python src/vision/live_demo.py
```

## Sample Results

| Result | Description |
|---|---|
| ![sample detection](results/sample_detection.png) | [Describe the example] |

TODO: add the metrics table (precision, recall, mAP, F1), the confusion matrix, and success/failure examples. Full results are in [`results/`](results/).

## Project Materials

| Material | Location |
|---|---|
| Midterm report (PDF) | [link or `docs/` path] |
| Final report (PDF) **[Final]** | [link] |
| Dataset | [`dataset/`](dataset/) |
| Trained model | [`models/`](models/) |
| Source code | [`src/`](src/) |
| Test results | [`results/`](results/) |
| Demonstration evidence | [`demonstration/`](demonstration/) |
| Video – Test 1: Figure-8 Line Detection and Tracking **[Final]** | [link] |
| Video – Test 2: Delivery Robot **[Final]** | [link] |

## Repository Structure

```
[Project-Title]/
├── README.md
├── requirements.txt
├── src/
│   ├── vision/        # preprocessing, inference, live demo
│   ├── training/      # model training
│   ├── testing/       # evaluation scripts
│   └── robot/         # [Final] robot control and communication
├── dataset/           # cleaned dataset + README
├── models/            # trained weights + README
├── results/
│   ├── test_1/        # [Final] Figure-8 results
│   └── test_2/        # [Final] specialization results
└── demonstration/     # photos, screenshots, videos + README
```

## References and Acknowledgments

- G. (2026). *KPDL – The Indoor Signs* (Version 11) [Data set]. Roboflow Universe. https://universe.roboflow.com/g-lcuz4/kpdl-the-indoor-signs/dataset/11 (CC BY-NC-SA 4.0)
- Ultralytics. [YOLOv8 documentation]. TODO: add the APA 7th edition citation.
- OpenCV. TODO: add the APA 7th edition citation.

All external datasets, code, and models used by this project are acknowledged here and in the project report.

## License

The dataset is shared under **CC BY-NC-SA 4.0**, as required by the source dataset.