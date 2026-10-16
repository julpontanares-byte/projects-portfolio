# Trained Model

This folder contains the trained weights used by the Delivery Robot vision system.

## Model File

| | |
|---|---|
| **File** | `best.pt` (about 6.5 MB, stored directly in this repository) |
| **Architecture** | YOLOv8n (Ultralytics), object detection |
| **Starting weights** | `yolov8n.pt`, pretrained on COCO, fine-tuned by our group |
| **Parameters / compute** | about 3.0 million parameters, 8.2 GFLOPs |
| **Input size** | 640 × 640 |
| **Output** | Bounding box, class label, and confidence score for each detected sign |

## Recognized Classes

The class IDs and names are stored inside the weights file (`model.names`) and match `dataset/data.yaml`.

| ID | Class | Meaning |
|---|---|---|
| 0 | `exit` | Exit sign |
| 1 | `mens_restroom` | Men's restroom |
| 2 | `womens_restroom` | Women's restroom |
| 3 | `no_entry` | No entry for unauthorized persons |
| 4 | `slippery_floor` | Slippery floor |

## Training Summary

The model was trained with `src/training/train.py`. The full list of settings is in [`results/training/args.yaml`](../results/training/args.yaml).

| Setting | Value |
|---|---|
| Dataset | Cleaned 5-class dataset, see [`dataset/README.md`](../dataset/README.md) |
| Training images | 475 used (476 in the folder; 1 skipped by YOLO because its label file mixes polygon and box rows) |
| Validation images | 106 |
| Epochs | 50 (training time about 5.6 minutes) |
| Batch size | 16 |
| Image size | 640 |
| Optimizer | AdamW (chosen automatically), learning rate 0.00111, weight decay 0.0005 |
| Early stopping | Patience 20 epochs |
| Augmentation | Ultralytics defaults (mosaic until the last 10 epochs, horizontal flip, color jitter, scaling) |
| Random seed | 0 |
| Training environment | Google Colab, Tesla T4 GPU, Ultralytics 8.4.177, Python 3.13, PyTorch 2.11 |

To retrain:

```bash
python src/training/train.py --epochs 50
```

Training curves, confusion matrices, and sample predictions from the training run are in [`results/training/`](../results/training/).

## Validation Results

Results of `best.pt` on the **validation split** (106 images), as printed at the end of training.

| Class | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|
| **all** | 0.894 | 0.926 | 0.959 | 0.850 |
| exit | 0.928 | 0.958 | 0.962 | 0.771 |
| mens_restroom | 0.869 | 0.734 | 0.877 | 0.735 |
| womens_restroom | 0.859 | 0.938 | 0.971 | 0.873 |
| no_entry | 0.860 | 1.000 | 0.995 | 0.922 |
| slippery_floor | 0.954 | 1.000 | 0.990 | 0.947 |

Inference speed on the T4 GPU was about 10 ms per image.

The validation set was also used to select the best checkpoint, and it is small (14 to 27 images per class), so these numbers are optimistic. The held-out test split and the unseen set below give fairer estimates.

## Evaluation Results

Evaluated with `src/testing/evaluate.py` on a laptop CPU (Intel Core i5-1035G1, Python 3.12, PyTorch 2.14 CPU build, Ultralytics 8.4.177) after training was finished. The model was not changed after these evaluations.

### Dataset test split (104 images)

| Class | Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|---|
| exit | 0.902 | 1.000 | 0.949 | 0.993 | 0.832 |
| mens_restroom | 0.958 | 0.820 | 0.884 | 0.937 | 0.756 |
| womens_restroom | 0.902 | 0.950 | 0.925 | 0.967 | 0.748 |
| no_entry | 1.000 | 0.964 | 0.982 | 0.995 | 0.899 |
| slippery_floor | 0.853 | 0.929 | 0.889 | 0.892 | 0.828 |
| **all** | 0.923 | 0.932 | 0.928 | 0.957 | 0.812 |

### Unseen test set (35 images)

| Class | Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|---|
| exit | 0.321 | 0.500 | 0.391 | 0.262 | 0.064 |
| mens_restroom | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| womens_restroom | 0.499 | 0.143 | 0.222 | 0.128 | 0.067 |
| no_entry | 1.000 | 0.000 | 0.000 | 0.250 | 0.179 |
| slippery_floor | 0.915 | 1.000 | 0.956 | 0.995 | 0.746 |
| **all** | 0.747 | 0.329 | 0.456 | 0.327 | 0.211 |

Performance drops sharply on the unseen set, which contains real signs with designs, sizes, and lighting unlike the training images. What the results show:

- **`slippery_floor` generalizes well.** It is a distinctive yellow object, detected confidently in every unseen image that contains it.
- **`exit` is partly detected.** Exit signs were found in about half of the instances, and missed in clear, well-framed photos as well.
- **Restroom and no-entry signs are mostly missed or labeled `exit`.** The model often draws an `exit` box on restroom doors and on a clear "NO ENTRY" sign, and it misses small door signs and differently styled signs.
- **Some signs get duplicate overlapping boxes** with different classes, and there is an occasional false detection on an empty hallway.

Each unseen class has only 6 to 8 instances, so these scores are indicative, not precise. A precision of 1.000 next to a recall of 0.000 (men's restroom, no_entry) is not a strength, because there were no correct detections to measure, so use mAP and the confusion matrix for those classes. The confusion matrices and the precision/recall tables are computed at different operating points and can disagree for the same class (for example, in the test-split confusion matrix about 43% of men's restroom signs are labeled women's restroom, while the table reports a men's restroom recall of 0.82), so both are reported.

Speed on the laptop CPU was about 95 to 130 ms per image (roughly 8 to 10 frames per second).

### Notes on the evaluation

- The evaluation was run three times (with plots, without plots, and a plain re-run). All three gave identical metrics.
- The first sample-prediction image of the first unseen run (`val_batch0_pred.jpg`) showed a display artifact: streaked colors across all tiles. The predictions in it match those of the clean re-run, so the model input and metrics were not affected. The clean version is the one stored in `results/evaluation/unseen/`. In that image, the yellow tint on the `unseen_no_entry_04` tile appears to be a plotting artifact as well; the original photo is normal.
- Tables and plots: [`results/evaluation/test/`](../results/evaluation/test/) and [`results/evaluation/unseen/`](../results/evaluation/unseen/).

## Loading and Using the Model

Install the dependencies first (`pip install -r requirements.txt`).

**Python**

```python
from ultralytics import YOLO

model = YOLO("models/best.pt")
print(model.names)   # {0: 'exit', 1: 'mens_restroom', 2: 'womens_restroom', 3: 'no_entry', 4: 'slippery_floor'}

results = model.predict("path/to/image.jpg", conf=0.5)
for box in results[0].boxes:
    class_name = model.names[int(box.cls)]
    confidence = float(box.conf)
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    print(class_name, round(confidence, 2), (x1, y1, x2, y2))
```

**Command line (single image, folder, or laptop webcam)**

```bash
yolo predict model=models/best.pt source=path/to/image.jpg conf=0.5 save=True
yolo predict model=models/best.pt source=0 conf=0.5 show=True
```

`source=0` uses the default laptop webcam. The Ultralytics default confidence threshold is 0.25, and we use 0.5 by default to reduce false and duplicate detections. A higher threshold removes more false boxes but also misses more real signs, so it can be adjusted.

### Live demo

The live demo script draws the boxes, class names, and confidence scores, and shows the model's preprocessed input:

```bash
python src/vision/live_demo.py                                  # laptop webcam
python src/vision/live_demo.py --source path/to/image.jpg       # one image
python src/vision/live_demo.py --source dataset/unseen_test/images   # a folder of images
```

Keys: `Q` quit, `+` / `-` change the confidence threshold, `S` save a screenshot to `results/demo/`, `N` / `P` next / previous image. The webcam image is not mirrored, because mirrored signs can be misread.

## Known Limitations

- **Restroom signs are confused with each other.** In the test-split confusion matrix, about 43% of men's restroom signs are labeled women's restroom and about 30% of women's restroom signs are labeled men's restroom. Counts per class are small, so individual percentages change a lot with a single image.
- **Unseen real-world signs are often missed or labeled `exit`** (see Evaluation Results).
- **Duplicate boxes.** Some signs receive several overlapping boxes at low confidence. A higher confidence threshold reduces this.
- **Domain gap.** Most training images are clean, close-up photos from the source dataset. Performance on our webcam, at a distance, in poor lighting, or from a low robot viewpoint is lower, as the unseen results show.
- **Small or distant signs** are often missed.
- **Single-sign scenes.** Every image in the cleaned dataset contains exactly one sign class (the per-class image counts add up to the number of images in each split), so scenes with several different signs were not evaluated.
- **Trained on the Vietnamese-style signs of the source dataset.** Signs with a very different design may not be recognized.