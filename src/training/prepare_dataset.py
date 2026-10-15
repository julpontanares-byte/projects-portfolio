"""
prepare_dataset.py
Builds the cleaned 5-class dataset from the raw Roboflow YOLOv8 export
(KPDL - The Indoor Signs, v11, CC BY-NC-SA 4.0).

What it does:
  1. Counts images/boxes per class and split in the RAW export.
  2. Removes the classes not listed in KEEP and renumbers the kept classes 0..N-1.
  3. Drops images whose ONLY boxes belonged to removed classes (so removed signs
     are not silently learned as "background"). Images that were originally
     background-only (no boxes) are kept.
  4. Writes the cleaned dataset, a new data.yaml, and dataset_summary.md.

Usage (run from the repository root):
  python src/training/prepare_dataset.py --dry-run     # counts only, writes nothing
  python src/training/prepare_dataset.py               # build dataset/ from dataset_raw/
"""
import argparse
import shutil
import sys
from collections import Counter
from pathlib import Path

SPLITS = ["train", "valid", "test"]
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Class order exactly as in the raw data.yaml (ID = position in this list)
RAW_NAMES = ["cam hut thuoc", "cam lua", "exit", "khong phan su mien vao",
             "tron truot", "wc nam", "wc nu"]

# Classes to KEEP: raw name -> English name used in the cleaned dataset.
# New class ID = position in this dict (0, 1, 2, ...). Edit this to change the selection.
KEEP = {
    "exit": "exit",
    "wc nam": "mens_restroom",
    "wc nu": "womens_restroom",
    "khong phan su mien vao": "no_entry",
    "tron truot": "slippery_floor",
}


def read_boxes(label_file):
    """Return a list of label lines (each a list of strings), or [] if the file is missing/empty."""
    if not label_file.exists():
        return []
    return [ln.split() for ln in label_file.read_text().splitlines() if ln.strip()]


def count_raw(raw):
    stats = {}
    for split in SPLITS:
        imgs, boxes = Counter(), Counter()
        for lf in (raw / split / "labels").glob("*.txt"):
            ids = [int(p[0]) for p in read_boxes(lf)]
            boxes.update(ids)
            imgs.update(set(ids))
        stats[split] = (imgs, boxes)
    return stats


def print_raw_counts(stats, min_images):
    print(f"\nRAW dataset: images containing each class (a single image can hold several boxes)")
    print(f"{'class':28s}{'train':>7s}{'valid':>7s}{'test':>7s}{'total':>8s}{'boxes':>8s}  keep?")
    for i, name in enumerate(RAW_NAMES):
        tr, va, te = (stats[s][0][i] for s in SPLITS)
        total = tr + va + te
        boxes = sum(stats[s][1][i] for s in SPLITS)
        flag = ""
        if name in KEEP:
            flag = "KEEP" + ("" if total >= min_images else f"  <-- only {total} images, below {min_images}")
        print(f"{name:28s}{tr:7d}{va:7d}{te:7d}{total:8d}{boxes:8d}  {flag}")


def clean(raw, out):
    keep_ids = {RAW_NAMES.index(n): new for new, n in enumerate(KEEP)}
    new_names = list(KEEP.values())
    summary = {}
    for split in SPLITS:
        (out / split / "images").mkdir(parents=True, exist_ok=True)
        (out / split / "labels").mkdir(parents=True, exist_ok=True)
        imgs, boxes = Counter(), Counter()
        n_kept = n_dropped = 0
        for img in sorted((raw / split / "images").iterdir()):
            if img.suffix.lower() not in IMG_EXT:
                continue
            lines = read_boxes(raw / split / "labels" / (img.stem + ".txt"))
            new_lines = [[str(keep_ids[int(p[0])])] + p[1:] for p in lines if int(p[0]) in keep_ids]
            if lines and not new_lines:      # only contained removed classes
                n_dropped += 1
                continue
            shutil.copy2(img, out / split / "images" / img.name)
            (out / split / "labels" / (img.stem + ".txt")).write_text(
                "".join(" ".join(p) + "\n" for p in new_lines))
            n_kept += 1
            boxes.update(int(p[0]) for p in new_lines)
            imgs.update(set(int(p[0]) for p in new_lines))
        summary[split] = (imgs, boxes, n_kept, n_dropped)

    # data.yaml (paths are relative to this file, so it works wherever the repo is cloned)
    (out / "data.yaml").write_text(
        "train: train/images\nval: valid/images\ntest: test/images\n\n"
        f"nc: {len(new_names)}\nnames: {new_names}\n")

    # dataset_summary.md (handy for report Sections 3.2 / 3.5 and the dataset README)
    rows = ["| ID | Class | Original name | Train | Valid | Test | Total images | Boxes |",
            "|---|---|---|---|---|---|---|---|"]
    for new, (raw_name, eng) in enumerate(KEEP.items()):
        tr, va, te = (summary[s][0][new] for s in SPLITS)
        bx = sum(summary[s][1][new] for s in SPLITS)
        rows.append(f"| {new} | {eng} | {raw_name} | {tr} | {va} | {te} | {tr + va + te} | {bx} |")
    split_rows = ["| Split | Images kept | Images dropped (only removed classes) |", "|---|---|---|"]
    for s in SPLITS:
        split_rows.append(f"| {s} | {summary[s][2]} | {summary[s][3]} |")
    removed = [n for n in RAW_NAMES if n not in KEEP]
    (out / "dataset_summary.md").write_text(
        "# Cleaned dataset summary\n\n" + "\n".join(rows) + "\n\n" + "\n".join(split_rows) +
        f"\n\nRemoved classes: {', '.join(removed)}\n")

    print("\nCLEANED dataset written to:", out)
    print("\n".join(rows))
    print("\n".join(split_rows))
    print("\nSee dataset_summary.md and data.yaml in the output folder.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="dataset_raw", help="folder with the raw Roboflow YOLOv8 export")
    ap.add_argument("--out", default="dataset", help="folder for the cleaned dataset")
    ap.add_argument("--dry-run", action="store_true", help="only print counts, write nothing")
    ap.add_argument("--min-images", type=int, default=100, help="warn if a kept class has fewer images")
    args = ap.parse_args()
    raw, out = Path(args.raw), Path(args.out)

    if not (raw / "data.yaml").exists():
        sys.exit(f"Could not find {raw / 'data.yaml'}. Put the unzipped Roboflow export in '{raw}'.")
    yaml_text = (raw / "data.yaml").read_text()
    missing = [n for n in RAW_NAMES if n not in yaml_text]
    if missing:
        sys.exit(f"RAW_NAMES does not match the raw data.yaml (not found: {missing}).")

    print_raw_counts(count_raw(raw), args.min_images)
    if args.dry_run:
        return
    if any((out / s).exists() for s in SPLITS):
        sys.exit(f"\n'{out}' already contains train/valid/test. Delete them or pass a different --out.")
    clean(raw, out)


if __name__ == "__main__":
    main()
