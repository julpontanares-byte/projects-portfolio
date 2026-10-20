import argparse
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
NAMES = ["exit", "mens_restroom", "womens_restroom", "no_entry", "slippery_floor"]
FONT = cv2.FONT_HERSHEY_SIMPLEX


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


def dhash(path, size=16):
    """Difference hash: size*size bits describing whether brightness rises left to right."""
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    small = cv2.resize(img, (size + 1, size), interpolation=cv2.INTER_AREA)
    return (small[:, 1:] > small[:, :-1]).flatten()


def thumb(path, w=320, h=240):
    """Image scaled to fit inside w x h on a dark background."""
    canvas = np.full((h, w, 3), 40, np.uint8)
    img = cv2.imread(str(path))
    if img is None:
        return canvas
    s = min(w / img.shape[1], h / img.shape[0])
    nw, nh = max(int(img.shape[1] * s), 1), max(int(img.shape[0] * s), 1)
    img = cv2.resize(img, (nw, nh))
    y, x = (h - nh) // 2, (w - nw) // 2
    canvas[y:y + nh, x:x + nw] = img
    return canvas


def save_pair_pages(pairs, out_dir, per_page=4):
    """Save pages of side-by-side pairs: unseen image on the left, its closest dataset image on the right."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("page_*.jpg"):
        old.unlink()
    pages = []
    for start in range(0, len(pairs), per_page):
        rows = []
        for unseen, match, dist, rel in pairs[start:start + per_page]:
            cap = np.full((24, 640, 3), 30, np.uint8)
            text = f"d={dist}/256  {unseen.name[:30]}  |  {rel[:34]}"
            cv2.putText(cap, text, (6, 17), FONT, 0.42, (255, 255, 255), 1)
            rows.append(np.vstack([cap, np.hstack([thumb(unseen), thumb(match)])]))
        page = out_dir / f"page_{start // per_page + 1:02d}.jpg"
        cv2.imwrite(str(page), np.vstack(rows))
        pages.append(page)
    return pages


def check_overlap(root, dataset, threshold, pairs_dir):
    unseen = list_images(root / "images")
    ref_paths = [p for s in ("train", "valid", "test") for p in list_images(dataset / s / "images")]
    print(f"\n=== OVERLAP CHECK: {len(unseen)} unseen vs {len(ref_paths)} dataset images ===")
    ref = [(p, dhash(p)) for p in ref_paths]
    ref = [(p, h) for p, h in ref if h is not None]
    if not ref:
        print("No reference images found. Is the dataset folder correct?")
        return
    ref_hashes = np.stack([h for _, h in ref])

    pairs = []
    for img in unseen:
        h = dhash(img)
        if h is None:
            print(f"  could not read {img.name}")
            continue
        dist = np.count_nonzero(ref_hashes != h, axis=1)
        j = int(dist.argmin())
        if dist[j] <= threshold:
            rel = str(ref[j][0].relative_to(dataset))
            pairs.append((img, ref[j][0], int(dist[j]), rel))
            print(f"  SIMILAR: {img.name}  ~  {rel}  (distance {dist[j]} of 256)")

    if not pairs:
        print(f"No near-duplicates found (threshold {threshold} of 256).")
    else:
        pages = save_pair_pages(pairs, pairs_dir)
        print(f"\n{len(pairs)} image(s) flagged. Open the pictures in {pairs_dir} and compare each pair by eye:")
        for p in pages:
            print("  ", p)
        print("Delete an unseen image (and its label file) only if it really is the same picture as the dataset image.")
        repeat = Counter(str(m) for _, m, _, _ in pairs)
        shared = [(Path(m).name, n) for m, n in repeat.items() if n > 1]
        if shared:
            print("Tip: one dataset image matching several different unseen photos usually means a false alarm.")
    print("Note: this only screens for the same or nearly the same picture. It can miss a dataset image "
          "re-photographed from a screen, so also think about where each unseen photo came from.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unseen", default="dataset/unseen_test", help="folder with images/ and labels/")
    ap.add_argument("--dataset", default="dataset", help="folder with train/ valid/ test/")
    ap.add_argument("--threshold", type=int, default=24, help="max hash distance (out of 256) to flag as similar")
    ap.add_argument("--pairs-dir", default="runs/overlap_pairs", help="where to save the side-by-side pictures")
    args = ap.parse_args()
    root, dataset = Path(args.unseen), Path(args.dataset)
    if not (root / "images").exists():
        raise SystemExit(f"Could not find {root / 'images'}. Run this from the repository root.")
    check_labels(root)
    check_overlap(root, dataset, args.threshold, Path(args.pairs_dir))


if __name__ == "__main__":
    main()