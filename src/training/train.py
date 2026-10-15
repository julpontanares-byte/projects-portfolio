"""
train.py
Fine-tunes a pretrained YOLOv8 model on the cleaned 5-class sign dataset.
Works on Google Colab (GPU), a local GPU, or CPU.

Usage (run from the repository root):
  python src/training/train.py                       # defaults: yolov8n, 50 epochs
  python src/training/train.py --epochs 80 --batch 16
  python src/training/train.py --model yolov8s.pt    # a larger model

Outputs:
  runs/detect/<name>/   training curves, validation plots, weights/
  models/best.pt        copy of the best weights (commit this one)
"""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="dataset/data.yaml", help="dataset config")
    ap.add_argument("--model", default="yolov8n.pt", help="pretrained weights to start from")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16, help="lower this (e.g. 8) if you run out of GPU memory")
    ap.add_argument("--patience", type=int, default=20, help="stop early if validation does not improve")
    ap.add_argument("--name", default="delivery_signs", help="run name")
    ap.add_argument("--device", default=None, help="e.g. 0 for the first GPU, cpu for CPU (default: auto)")
    ap.add_argument("--seed", type=int, default=0, help="fixed seed so results can be reproduced")
    args = ap.parse_args()

    # Absolute path so the relative paths inside data.yaml resolve next to the file
    data_path = Path(args.data).resolve()
    if not data_path.exists():
        raise SystemExit(f"Could not find {data_path}. Run this from the repository root.")

    model = YOLO(args.model)
    model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        name=args.name,
        device=args.device,
        seed=args.seed,
        plots=True,
    )

    # Copy the best weights to models/ so they are easy to find and commit
    best = Path(model.trainer.best)
    Path("models").mkdir(exist_ok=True)
    shutil.copy2(best, Path("models") / "best.pt")
    print(f"\nBest weights: {best}")
    print("Copied to: models/best.pt")


if __name__ == "__main__":
    main()
