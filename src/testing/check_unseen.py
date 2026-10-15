"""
check_unseen.py
Two sanity checks for the unseen test set before you evaluate on it:

  1. LABELS:  every image has a valid YOLO label file; prints images per class.
              An empty .txt file means "no sign in this image" (a background image).
  2. OVERLAP: screens for near-duplicates of images in dataset/train, valid and test,
              using a perceptual hash. It catches the same or almost the same picture,
              but it is only a screen: it cannot prove two different photos of the same
              sign are unrelated.

Usage (run from the repository root):
  python src/testing/check_unseen.py
  python src/testing/check_unseen.py --threshold 8      # stricter duplicate screen
"""
import argparse
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
NAMES = ["exit", "mens_restroom", "womens_restroom", "no_entry", "slippery_floor"]


def list_images(folder):
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT) if folder.exists() else []


def check_labels(root):
    images = list_images(root / "images")
    print(f"\n=== LABEL CHECK: {len(images)} images in {root / 'images'} ===")
    counts, problems, empty = Counter(), [], 0
    for img in images:
        lf = root / "labels" / (img.stem + ".txt")
        if not lf.exists():
            problems.append(f"no label file for {img.name} (create an empty {img.stem}.txt if it has no sign)")
            continue
        rows = [ln.split() for ln in lf.read_text().splitlines() if ln.strip()]
        if not rows:
            empty += 1
            continue
        ids = set()
        for r in rows:
            try:
                cid, vals = int(r[0]), [float(x) for x in r[1:]]
            except ValueError:
                problems.append(f"{lf.name}: unreadable line '{' '.join(r)}'")
                continue
            if len(r) != 5:
                problems.append(f"{lf.name}: expected 5 values per line (class x y w h), got {len(r)}")
            elif cid not in range(len(NAMES)):
                problems.append(f"{lf.name}: class id {cid} is not 0-{len(NAMES) - 1}")
            elif any(v < 0 or v > 1 for v in vals):
                problems.append(f"{lf.name}: box values must be between 0 and 1")
            else:
                ids.add(cid)
        counts.update(ids)

    print(f"{'class':18s}images")
    for i, n in enumerate(NAMES):
        print(f"{i} {n:16s}{counts[i]}")
    print(f"{'(no sign)':18s}{empty}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
    else:
        print("\nNo label problems found.")


def dhash(path, size=8):
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    small = cv2.resize(img, (size + 1, size), interpolation=cv2.INTER_AREA)
    return (small[:, 1:] > small[:, :-1]).flatten()


def check_overlap(root, dataset, threshold):
    unseen = list_images(root / "images")
    ref_paths = [p for s in ("train", "valid", "test") for p in list_images(dataset / s / "images")]
    print(f"\n=== OVERLAP CHECK: {len(unseen)} unseen vs {len(ref_paths)} dataset images ===")
    ref = [(p, dhash(p)) for p in ref_paths]
    ref = [(p, h) for p, h in ref if h is not None]
    if not ref:
        print("No reference images found. Is the dataset folder correct?")
        return
    ref_hashes = np.stack([h for _, h in ref])

    flagged = 0
    for img in unseen:
        h = dhash(img)
        if h is None:
            print(f"  could not read {img.name}")
            continue
        dist = np.count_nonzero(ref_hashes != h, axis=1)
        j = int(dist.argmin())
        if dist[j] <= threshold:
            flagged += 1
            print(f"  SIMILAR: {img.name}  ~  {ref[j][0].relative_to(dataset)}  (distance {dist[j]} of 64)")
    if flagged:
        print(f"\n{flagged} image(s) look similar to dataset images. Look at each pair and remove the unseen image if it is the same picture.")
    else:
        print(f"No near-duplicates found (threshold {threshold} of 64).")
    print("Note: this only catches the same or nearly the same picture.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unseen", default="dataset/unseen_test", help="folder with images/ and labels/")
    ap.add_argument("--dataset", default="dataset", help="folder with train/ valid/ test/")
    ap.add_argument("--threshold", type=int, default=6, help="max hash distance (out of 64) to flag as similar")
    args = ap.parse_args()
    root, dataset = Path(args.unseen), Path(args.dataset)
    if not (root / "images").exists():
        raise SystemExit(f"Could not find {root / 'images'}. Run this from the repository root.")
    check_labels(root)
    check_overlap(root, dataset, args.threshold)


if __name__ == "__main__":
    main()
