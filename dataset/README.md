# Dataset

This folder contains the dataset used by the Delivery Robot vision system: indoor sign images with bounding-box annotations in YOLOv8 format, cleaned to 5 classes.

## Source

| | |
|---|---|
| **Dataset** | KPDL – The Indoor Signs |
| **Version used** | v11 (COCO version, exported in YOLOv8 format) |
| **Author** | G (Roboflow Universe workspace `g-lcuz4`) |
| **Link** | https://universe.roboflow.com/g-lcuz4/kpdl-the-indoor-signs/dataset/11 |
| **License** | CC BY-NC-SA 4.0 |
| **Task** | Object detection (bounding boxes) |
| **Original size** | 832 images, 7 classes |

**Citation (APA 7th):** G. (2026). *KPDL – The Indoor Signs* (Version 11) [Data set]. Roboflow Universe. https://universe.roboflow.com/g-lcuz4/kpdl-the-indoor-signs/dataset/11

**License note:** CC BY-NC-SA 4.0 requires attribution, non-commercial use, and sharing modified versions under the same license. This cleaned version is a modified copy of the original dataset and is shared under the same license, for coursework use only.

## Target Classes

The original dataset has 7 classes, with Vietnamese names. We kept 5 and renamed them in English. The meanings are the group's own translations of the Vietnamese class names.

| ID | Class | Original name | Meaning | Role in the delivery scenario |
|---|---|---|---|---|
| 0 | `exit` | exit | Exit sign | Destination |
| 1 | `mens_restroom` | wc nam | Men's restroom | Destination |
| 2 | `womens_restroom` | wc nu | Women's restroom | Destination |
| 3 | `no_entry` | khong phan su mien vao | No entry for unauthorized persons | Restricted zone |
| 4 | `slippery_floor` | tron truot | Slippery floor | Hazard zone |

**Removed classes:** `cam hut thuoc` (no smoking) and `cam lua` (no fire). These are rules and restrictions that do not correspond to a destination, a restricted zone, or a navigation hazard for the robot.

## Dataset Summary

### Images per class and split

Counts are the number of images that contain each class. An image can hold several boxes of the same class.

| ID | Class | Original name | Train | Valid | Test | Total images | Boxes |
|---|---|---|---|---|---|---|---|
| 0 | exit | exit | 125 | 26 | 20 | 171 | 178 |
| 1 | mens_restroom | wc nam | 98 | 27 | 28 | 153 | 154 |
| 2 | womens_restroom | wc nu | 77 | 16 | 20 | 113 | 113 |
| 3 | no_entry | khong phan su mien vao | 80 | 14 | 11 | 105 | 135 |
| 4 | slippery_floor | tron truot | 96 | 23 | 25 | 144 | 147 |

### Training, validation, and testing sets

| Set | Images | Percentage | Purpose |
|---|---|---|---|
| Training | 476 | 69.4% | The model learns from these images |
| Validation | 106 | 15.5% | Used during development to tune settings and select the best model |
| Testing | 104 | 15.2% | Held out for the final evaluation, never used for training |
| **Total** | **686** | **100%** | |

The split is the one provided by the original dataset (70/15/15), preserved after cleaning.

### Unseen test set

| Class | Images |
|---|---|
| exit | 6 |
| mens_restroom | 6 |
| womens_restroom | 6 |
| no_entry | 6 |
| slippery_floor | 6 |
| No sign (background) | 5 |
| **Total** | **35** |

- **Sources:** [n] photos taken with a laptop webcam, [n] taken with a phone, [n] from [dataset/site name, link, license]. [Real signs / printed signs / screen displays: say which.]
- **Conditions:** [lighting, distances, angles, backgrounds, occlusion].
- **Labels:** drawn by the group in makesense.ai (YOLO format), same class IDs as `data.yaml`. The 5 no-sign images have empty label files.
- **Checks:** `src/testing/check_unseen.py` found no label problems and no near-duplicates of the train, valid, or test images (perceptual hash, 256 bits, threshold 24), and pairs were compared by eye.
- None of these images were used for training or validation.

## Preprocessing and Preparation

**Already applied by the source dataset:**
- Auto-orient
- Resize to 640×640 (fit, with black edges)
- No augmentation

**Applied by our group** with `src/training/prepare_dataset.py`:
1. Removed the annotations of the 2 dropped classes.
2. Renumbered the 5 kept classes from 0 to 4.
3. Removed 146 images whose only annotations were from the dropped classes (108 train, 20 valid, 18 test). This stops the model from learning those signs as background.
4. Kept the original train/valid/test assignment of every remaining image.
5. Wrote a new `data.yaml` for the 5 classes.

| Set | Images before | Images removed | Images kept |
|---|---|---|---|
| Train | 584 | 108 | 476 |
| Valid | 126 | 20 | 106 |
| Test | 122 | 18 | 104 |
| **Total** | **832** | **146** | **686** |

## Folder Structure

```
dataset/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
├── unseen_test/        # our own photos (to be added)
├── data.yaml
└── README.md
```

Each label file has the same name as its image. Every line is one bounding box in YOLO format:

```
<class_id> <x_center> <y_center> <width> <height>
```

All values after the class ID are normalized to the range 0 to 1.

## Usage

Point YOLOv8 training at the `data.yaml` file:

```bash
yolo detect train data=dataset/data.yaml model=yolov8n.pt epochs=50 imgsz=640
```

The paths in `data.yaml` are relative to the file itself, so it works wherever the repository is cloned.

## Reproducing the Cleaning

The raw Roboflow export (YOLOv8 format, version 11) is not stored in this repository. To rebuild this dataset:

1. Download the raw export from the link above and unzip it into a folder named `dataset_raw/` at the repository root.
2. Run `python src/training/prepare_dataset.py` from the repository root.

## Known Limitations

- **Small validation and test sets for some classes.** For example, `no_entry` has 14 validation and 11 test images, so its metrics can change a lot with a single prediction.
- **Class sizes are uneven**, from 105 images (`no_entry`) to 171 (`exit`).
- **Domain gap.** The images come from a different camera and environments than our laptop webcam and robot camera, which is why we collect our own unseen test set.
- **Possible similarity between classes.** The men's and women's restroom signs look alike, so confusion between them is likely.
- TODO: confirm and note whether the dataset contains background-only images (images with no sign).