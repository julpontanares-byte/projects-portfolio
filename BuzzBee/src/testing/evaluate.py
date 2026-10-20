import argparse
from pathlib import Path

import yaml
from ultralytics import YOLO


def f1(p, r):
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def write_report(res, tag, subdir):
    """Print and save a per-class metrics table."""
    box = res.box
    names = res.names
    rows = ["| Class | Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 |", "|---|---|---|---|---|---|"]
    for i, cls_id in enumerate(box.ap_class_index):
        p, r = box.p[i], box.r[i]
        rows.append(f"| {names[int(cls_id)]} | {p:.3f} | {r:.3f} | {f1(p, r):.3f} | "
                    f"{box.ap50[i]:.3f} | {box.ap[i]:.3f} |")
    rows.append(f"| **all** | {box.mp:.3f} | {box.mr:.3f} | {f1(box.mp, box.mr):.3f} | "
                f"{box.map50:.3f} | {box.map:.3f} |")
    table = "\n".join(rows)

    out_dir = Path("results") / "evaluation" / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"metrics_{tag}.md"
    out.write_text(f"# Metrics: {tag}\n\n{table}\n")
    print(f"\n=== {tag} ===\n{table}\n(saved to {out})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/best.pt")
    ap.add_argument("--data", default="dataset/data.yaml")
    ap.add_argument("--unseen", default="dataset/unseen_test", help="folder with images/ and labels/")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--device", default=None)
    ap.add_argument("--no-plots", action="store_true",
                    help="skip the plots (and the confusion matrix) to get the metrics without plotting")
    ap.add_argument("--suffix", default="", help="added to output names so a re-run does not overwrite the first run")
    args = ap.parse_args()

    data_path = Path(args.data).resolve()
    model = YOLO(args.model)

    # 1) The dataset's own test split
    res = model.val(data=str(data_path), split="test", imgsz=args.imgsz,
                    plots=not args.no_plots, name=f"eval_test{args.suffix}", device=args.device)
    write_report(res, f"test{args.suffix}", "test")

    # 2) Our unseen set (a temporary config that reuses the class names from data.yaml)
    unseen = Path(args.unseen).resolve()
    if not (unseen / "images").exists():
        print(f"\nSkipping unseen evaluation: {unseen / 'images'} not found yet.")
        return
    names = yaml.safe_load(data_path.read_text())["names"]
    cfg = {"path": str(unseen), "train": "images", "val": "images", "test": "images", "names": names}
    Path("runs").mkdir(exist_ok=True)
    cfg_path = Path("runs") / "data_unseen.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))
    res = model.val(data=str(cfg_path.resolve()), split="test", imgsz=args.imgsz,
                    plots=not args.no_plots, name=f"eval_unseen{args.suffix}", device=args.device)
    write_report(res, f"unseen{args.suffix}", "unseen")


if __name__ == "__main__":
    main()