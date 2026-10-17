# Dataset

This folder contains the dataset used by the Delivery Robot vision system: indoor sign images with bounding-box annotations in YOLOv8 format, cleaned to 5 classes, plus a separate set of unseen test photos.

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
| 0 | `exit` | exit | Exit sign | Destination marker: stop if it is the assigned destination, otherwise continue |
| 1 | `mens_restroom` | wc nam | Men's restroom | Destination marker: stop if it is the assigned destination, otherwise continue |
| 2 | `womens_restroom` | wc nu | Women's restroom | Destination marker: stop if it is the assigned destination, otherwise continue |
| 3 | `no_entry` | khong phan su mien vao | No entry for unauthorized persons | Restricted area: always stop and turn away |
| 4 | `slippery_floor` | tron truot | Slippery floor | Hazard: slow down |

At any time, one of the three destination markers is the robot's assigned destination. See the main [`README.md`](../README.md) for the full decision logic.

**Removed classes:** `cam hut thuoc` (no smoking) and `cam lua` (no fire). These are rules and restrictions that do not correspond to a destination, a restricted area, or a navigation hazard for the robot.

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

Our own photos, kept in `unseen_test/`. They are used only for the final evaluation, to measure how the model handles situations it was not trained on.

| Class | Images | Instances (boxes) |
|---|---|---|
| exit | 6 | 8 |
| mens_restroom | 6 | 7 |
| womens_restroom | 6 | 7 |
| no_entry | 6 | 6 |
| slippery_floor | 6 | 6 |
| No sign (background) | 5 | 0 |
| **Total** | **35** | **34** |

- **Capture:** the photos were taken with the group's laptop webcam using `src/vision/capture_images.py`, at 1280×720. File names follow the pattern `unseen_<class>_<NN>.jpg`, where the class in the name is what the photographer pointed the camera at.
- **Conditions:** dim and uneven lighting, sensor noise, glare, different distances and angles, signs on doors, walls, and floors, and some small or distant signs. The 5 no-sign images show hallways, doors, and walls.
- **Labels:** drawn by the group in makesense.ai (YOLO format), with the same class IDs as `data.yaml`. The 5 no-sign images have empty label files.
- **Checks:** `src/testing/check_unseen.py` found no label problems and no near-duplicates of the train, valid, or test images (256-bit perceptual hash, threshold 24). This screen only catches the same or nearly the same image.
- **Use:** none of these images were used for training or validation, and they are not modified or preprocessed before evaluation beyond the model's own input resizing.

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
├── unseen_test/
│   ├── images/          # 35 photos named unseen_<class>_<NN>.jpg
│   └── labels/          # YOLO label files (empty for the no-sign photos)
├── data.yaml
└── README.md
```

Each label file has the same name as its image. Every line is one bounding box in YOLO format:

```
<class_id> <x_center> <y_center> <width> <height>
```

All values after the class ID are normalized to the range 0 to 1.

## Usage

Train with the `data.yaml` file (the model was trained on Google Colab):

```bash
python src/training/train.py --epochs 50
```

Evaluate on the test split and on the unseen set:

```bash
python src/testing/evaluate.py --device cpu
```

The paths in `data.yaml` are relative to the file itself, so it works wherever the repository is cloned. The unseen set is never part of `data.yaml`. The evaluation script builds a temporary configuration for it.

## Reproducing the Cleaning

The raw Roboflow export (YOLOv8 format, version 11) is not stored in this repository. To rebuild this dataset:

1. Download the raw export from the link above and unzip it into a folder named `dataset_raw/` at the repository root.
2. Run `python src/training/prepare_dataset.py --dry-run` to see the per-class counts, then `python src/training/prepare_dataset.py` to build the cleaned dataset.

## Known Limitations

- **Small validation and test sets for some classes.** For example, `no_entry` has 14 validation and 11 test images, so its metrics can change a lot with a single prediction. The unseen set has only 6 to 8 instances per class, so its scores are indicative.
- **Class sizes are uneven**, from 105 images (`no_entry`) to 171 (`exit`). `womens_restroom` (113) and `no_entry` (105) are below the 150 images per class planned for the Final.
- **Domain gap.** The training images are mostly clean, close-up photos from other cameras and environments, while our laptop webcam and robot camera produce darker, noisier frames at a distance. The unseen results show a large drop for this reason (see [`models/README.md`](../models/README.md)).
- **Possible similarity between classes.** The men's and women's restroom signs look alike, so confusion between them is likely.
- **No background-only images.** The training and validation splits contain no images without a sign, so the model has seen few examples of empty scenes.
- **One training image is skipped by YOLO.** `20-1-_jpg.rf.3aa0781751e863f70976f9e9c2cd486c.jpg` has a label file that mixes polygon and box rows, so Ultralytics ignores it. Training used 475 of the 476 training images.
- **Mixed annotation types.** The source dataset contains both polygon and bounding-box labels. For detection, Ultralytics uses bounding boxes only and converts polygons to their enclosing boxes.