# Vision-Based Autonomous 4WD Delivery Robot

A camera-based sign recognition system for a 4WD delivery robot, built with YOLOv8.

> **Current stage:** Midterm (SEE → RECOGNIZE). The vision system is complete. Robot integration, decision logic, motor control, and autonomous behavior belong to the Final stage (SEE → DECIDE → ACT) and are marked **[Final]**.

## Group Members

| Name |
|---|
| Ven John Rey Lavapie |
| Ivy Pauline Muit |
| Ayelyn Janne Panliboton |
| Juliet Pontanares |
| Rhea Lizza Sanglay |

**Course:** Computer Vision, BS Computer Science – 4A

**Instructor:** Elena Clarexe Gulane

## Assigned Specialization

**Autonomous Delivery Robot.** The vision system must recognize visual markers that identify delivery destinations, so that the robot can decide where to go and where to stop (Final).

## Project Description

The system detects and recognizes five types of indoor signs and treats them as markers that guide a delivery robot. The robot always has one assigned destination (`exit`, `mens_restroom`, or `womens_restroom`), so the same destination sign means **stop** or **continue** depending on the assignment:

| Marker (class) | Meaning | Type | Robot decision |
|---|---|---|---|
| `exit` | Exit sign | Destination marker | If it is the assigned destination: stop, delivery point reached. Otherwise: continue searching. (Also the planned start / return point **[Final]**.) |
| `mens_restroom` | Men's restroom | Destination marker | If assigned: stop, delivery point reached. Otherwise: continue searching. |
| `womens_restroom` | Women's restroom | Destination marker | If assigned: stop, delivery point reached. Otherwise: continue searching. |
| `no_entry` | No entry for unauthorized persons | Restricted area | Always stop and turn away, whichever destination is assigned. |
| `slippery_floor` | Wet / slippery floor sign | Hazard | Slow down while it is visible. If the assigned destination is also visible, the robot stops there instead. |

- **Midterm:** a working computer vision pipeline that captures an image or live camera frame, preprocesses it, detects and recognizes the signs, and shows the result visually (bounding box, class label, confidence score).
- **Final [Final]:** the recognized sign is converted into a robot decision and action (SEE → DECIDE → ACT), with motor control and autonomous behavior on the physical 4WD robot.

### Decision logic

The live demo includes a basic decision step that shows what the robot would do for each recognized sign. It is a simulation: no motors are driven in the Midterm. The assigned destination can be set with `--destination` and changed while the demo runs (`D` key). When several signs are visible, the rules apply in this order:

1. `no_entry` is detected: stop, restricted area, turn away.
2. The target destination is detected: stop, delivery point reached.
3. `slippery_floor` is detected: slow down.
4. Another destination marker is detected: continue.
5. Nothing is detected: keep searching.

**[Final]:** the same logic will drive the motors, with an LED or buzzer to confirm delivery, and a return to the `exit` marker after each delivery.

## System Overview

```
Camera / Image → Preprocessing → YOLOv8 Detector → Detection / Recognition → Visual Output
                                                                    │
                                          [Final] → Decision Logic → Robot Control → Motors
```

## Hardware Used

**Midterm**

| Component | Specification | Purpose |
|---|---|---|
| Camera | Built-in laptop webcam | Live image input for the demo and for collecting the unseen test photos |
| Development laptop | Intel Core i5-1035G1 CPU, NVIDIA GeForce MX230 (2 GB, not used) | Evaluation and live demo (CPU inference) |
| Training machine | Google Colab, NVIDIA Tesla T4 GPU | Model training |

**Final [Final]**

| Component | Specification | Purpose |
|---|---|---|
| 4WD chassis | To be finalized | Robot platform |
| DC motors | To be finalized | Movement |
| Motor driver | To be finalized | Motor control |
| Microcontroller | To be finalized (Arduino / ESP32 / Raspberry Pi) | Receives commands, drives motors |
| Camera | To be finalized | Robot vision |
| Power source | To be finalized | Power |

## Software and Tools

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12 (local), 3.13 (Colab) | Main programming language |
| Ultralytics (YOLOv8) | 8.4.177 | Model training, evaluation, and inference |
| PyTorch | 2.14 CPU build (local), 2.11 CUDA build (Colab) | Deep learning backend |
| OpenCV | see `requirements.txt` | Image capture, preprocessing, and visualization |
| NumPy | installed with the libraries above | Numerical processing |
| Roboflow (website) | n/a | Source of the base dataset |
| makesense.ai | n/a | Annotation of the unseen test images |
| Arduino IDE **[Final]** | to be finalized | Motor controller code |

## Computer Vision Methodology

1. **Dataset:** a public indoor-sign dataset (KPDL – The Indoor Signs) cleaned to 5 classes, plus our own unseen test photos.
2. **Preprocessing:**
   - Source dataset: auto-orient and resize to 640×640 (fit, with black edges); no augmentation applied at the source.
   - Model input (applied by YOLOv8 to every image or frame): resize so the longest side is 640 px, pad to 640×640 (letterbox), convert BGR to RGB, and scale pixel values to 0–1.
   - Training augmentation: Ultralytics defaults (mosaic, horizontal flip, color jitter, scaling).
3. **Model:** YOLOv8n object detector fine-tuned from COCO-pretrained weights (transfer learning).
4. **Evaluation:** precision, recall, F1-score, mAP, and confusion matrix on the held-out test split and on a separate unseen set.
5. **Output:** bounding boxes, class labels, and confidence scores drawn on the image or live frame.

## Dataset Overview

- **Base dataset:** KPDL – The Indoor Signs, version 11 (Roboflow Universe)
- **Link:** https://universe.roboflow.com/g-lcuz4/kpdl-the-indoor-signs/dataset/11
- **License:** CC BY-NC-SA 4.0 (attribution required, non-commercial, share-alike)
- **Format:** YOLOv8 (bounding boxes)
- **Modification:** the original dataset has 832 images and 7 classes. We kept 5 classes, removed 2 (`cam hut thuoc`, no smoking, and `cam lua`, no fire, which are not destinations or navigation hazards), renumbered the class IDs from 0 to 4, and removed the 146 images that contained only the removed classes. 686 images remain.

### Target Classes

| ID | Class | Original name | Meaning | Images |
|---|---|---|---|---|
| 0 | `exit` | exit | Exit sign | 171 |
| 1 | `mens_restroom` | wc nam | Men's restroom | 153 |
| 2 | `womens_restroom` | wc nu | Women's restroom | 113 |
| 3 | `no_entry` | khong phan su mien vao | No entry for unauthorized persons | 105 |
| 4 | `slippery_floor` | tron truot | Slippery floor | 144 |

The image counts are the number of images that contain each class, across all three splits.

### Dataset Splits

| Set | Images | Percentage | Purpose |
|---|---|---|---|
| Training | 476 | 69.4% | The model learns from these images |
| Validation | 106 | 15.5% | Tuning and model selection |
| Testing | 104 | 15.2% | Final held-out score |
| **Unseen test** | 35 | n/a | Our own photos (6 per sign class and 5 with no sign), taken in different places and conditions. Never used for training or validation. |

See [`dataset/README.md`](dataset/README.md) for the cleaning procedure, per-split counts, and how the unseen set was collected and checked.

## Model / Algorithm

- **Architecture:** YOLOv8n (about 3.0 million parameters, 8.2 GFLOPs)
- **Pretrained weights:** `yolov8n.pt` (COCO)
- **Training:** 50 epochs, batch 16, image size 640, AdamW optimizer (chosen automatically), seed 0, on Google Colab (T4)
- **Trained weights:** [`models/best.pt`](models/best.pt), documented in [`models/README.md`](models/README.md)
- **Recognized classes:** `exit`, `mens_restroom`, `womens_restroom`, `no_entry`, `slippery_floor`

## System Architecture / Workflow

**Midterm:** Camera frame or image → Preprocessing → YOLOv8 inference → Detections (box, class, confidence) → Visual output.

**Final [Final]:** Camera → YOLOv8 → Recognized sign → Decision logic → Command to controller → Motor driver → Motors → Robot action.

## Installation and Setup

```bash
# 1. Clone the repository
git clone https://github.com/pau-827/BuzzBee.git
cd BuzzBee

# 2. (Recommended) create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

The cleaned dataset and the trained weights are already included in the repository. No Roboflow API key is needed. The first install downloads PyTorch, which is large.

## Running the System

All commands are run from the repository root.

```bash
# Live demo with the laptop webcam
python src/vision/live_demo.py

# Live demo on a single image or a folder of images
python src/vision/live_demo.py --source path/to/image.jpg
python src/vision/live_demo.py --source dataset/unseen_test/images

# Evaluate the model on the test split and on the unseen set
python src/testing/evaluate.py --device cpu

# Collect unseen photos with the webcam (SPACE = save, Q = quit)
python src/vision/capture_images.py --label exit

# Check the unseen set (labels, counts per class, near-duplicates of dataset images)
python src/testing/check_unseen.py

# Rebuild the cleaned dataset from the raw Roboflow export (optional)
python src/training/prepare_dataset.py

# Retrain the model (done on Google Colab with a GPU)
python src/training/train.py --epochs 50
```

Live demo keys: `Q` quit, `+` / `-` change the confidence threshold, `S` save a screenshot to `results/demo/`, `N` / `P` next / previous image.

The unseen test set must not be used for training, validation, or tuning, so the evaluation is run on the final model only.

## Sample Results

| Set | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|
| Test split (104 images) | 0.923 | 0.932 | 0.957 | 0.812 |
| Unseen set (35 images) | 0.747 | 0.329 | 0.327 | 0.211 |

The model performs very well on the held-out test split but drops sharply on the unseen photos, which contain real signs with designs, sizes, and lighting unlike the training images. `slippery_floor` generalizes well (mAP@0.5 of 0.995 on the unseen set), while men's restroom, women's restroom, and no-entry signs are often missed or labeled `exit`. Each unseen class has only 6 to 8 instances, so these scores are indicative. Details are in [`models/README.md`](models/README.md).

| Training curves | Test split confusion matrix | Unseen set confusion matrix |
|---|---|---|
| ![training curves](results/training/results.png) | ![test confusion matrix](results/evaluation/test/confusion_matrix_normalized.png) | ![unseen confusion matrix](results/evaluation/unseen/confusion_matrix_normalized.png) |

All result files are in [`results/`](results/).

## Project Status

- **Done (Midterm):** dataset preparation, model training, evaluation on the test and unseen sets, and project documentation.
- **In progress (Midterm):** live demonstration evidence (screenshots in `results/demo/`) and the Midterm report.
- **Not started [Final]:** robot hardware, decision logic, motor control, autonomous behavior, and the two demonstration videos.

## Known Limitations

- Performance drops on unseen real-world signs (see Sample Results). Many men's restroom, women's restroom, and no-entry signs are missed or labeled `exit`.
- Small or distant signs are often missed, and some signs receive duplicate overlapping boxes at low confidence.
- The training images are mostly clean, close-up photos, so a laptop or robot camera at a distance, in dim light, or from a low viewpoint is a harder condition.
- Two classes (`womens_restroom`, `no_entry`) are below the 150 images per class planned for the Final, so more images are needed.

## Project Materials

| Material | Location |
|---|---|
| Midterm report (PDF) | To be added |
| Final report (PDF) **[Final]** | To be added |
| Dataset | [`dataset/`](dataset/) |
| Trained model | [`models/`](models/) |
| Source code | [`src/`](src/) |
| Training and evaluation results | [`results/`](results/) |
| Demonstration evidence | [`demonstration/`](demonstration/) |
| Video – Test 1: Figure-8 Line Detection and Tracking **[Final]** | To be added |
| Video – Test 2: Delivery Robot **[Final]** | To be added |

## Repository Structure

```
BuzzBee/
├── README.md
├── requirements.txt
├── src/
│   ├── vision/        # capture_images.py, live_demo.py
│   ├── training/      # prepare_dataset.py, train.py, train_colab.ipynb
│   ├── testing/       # evaluate.py, check_unseen.py
│   └── robot/         # [Final] robot control and communication
├── dataset/           # train/, valid/, test/, unseen_test/, data.yaml, README
├── models/            # best.pt + README
├── results/
│   ├── training/      # training curves, confusion matrices, sample predictions
│   ├── evaluation/    # test/ and unseen/ metrics tables and plots
│   ├── demo/          # live demo screenshots
│   ├── test_1/        # [Final] Figure-8 results
│   └── test_2/        # [Final] specialization results
└── demonstration/     # photos, screenshots, videos + README
```

## References and Acknowledgments

- G. (2026). *KPDL – The Indoor Signs* (Version 11) [Data set]. Roboflow Universe. https://universe.roboflow.com/g-lcuz4/kpdl-the-indoor-signs/dataset/11 (CC BY-NC-SA 4.0)
- Jocher, G., Chaurasia, A., & Qiu, J. (2023). *Ultralytics YOLOv8* (Version 8.4.177) [Computer software]. https://github.com/ultralytics/ultralytics
- Bradski, G. (2000). The OpenCV Library. *Dr. Dobb's Journal of Software Tools*.

All external datasets, code, and models used by this project are acknowledged here and in the project report.

## License

The cleaned dataset is shared under **CC BY-NC-SA 4.0**, as required by the source dataset. The project code and documentation were created for coursework.