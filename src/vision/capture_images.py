"""
capture_images.py
Collects the UNSEEN test photos with the laptop webcam.
Shows a live preview; press SPACE to save the current frame, Q (or Esc) to quit.

Usage (run from the repository root):
  python src/vision/capture_images.py --label exit
  python src/vision/capture_images.py --label mens_restroom
  python src/vision/capture_images.py --label nosign      # walls, doors, corridors (no sign in view)

Files are saved as dataset/unseen_test/images/unseen_<label>_<NN>.jpg and numbering
continues from the existing files, so you can stop and resume without overwriting.
These images must NEVER be used for training or validation.
"""
import argparse
import sys
import time
from pathlib import Path

import cv2

LABELS = ["exit", "mens_restroom", "womens_restroom", "no_entry", "slippery_floor", "nosign"]


def next_index(folder, prefix):
    """Next free number for files named <prefix>_<NN>.jpg."""
    nums = []
    for p in folder.glob(f"{prefix}_*.jpg"):
        try:
            nums.append(int(p.stem.split("_")[-1]))
        except ValueError:
            pass
    return max(nums, default=0) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, choices=LABELS, help="what is in front of the camera")
    ap.add_argument("--out", default="dataset/unseen_test/images", help="where to save the photos")
    ap.add_argument("--camera", type=int, default=0, help="webcam index (try 1 if 0 is the wrong camera)")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prefix = f"unseen_{args.label}"
    idx = next_index(out, prefix)

    # DirectShow starts much faster than the default backend on Windows
    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW) if sys.platform.startswith("win") \
        else cv2.VideoCapture(args.camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if not cap.isOpened():
        sys.exit(f"Could not open camera {args.camera}. Close other apps using the webcam or try --camera 1.")

    saved, last_saved = 0, 0.0
    print(f"Capturing '{args.label}' to {out}. SPACE = save, Q = quit.")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Lost the camera feed.")
            break

        preview = frame.copy()
        cv2.putText(preview, f"{args.label} | saved this session: {saved} | SPACE=save  Q=quit",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        if time.time() - last_saved < 0.5:
            cv2.putText(preview, "SAVED", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 3)
        cv2.imshow("Capture unseen images", preview)

        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # SPACE: save the clean frame (without the text overlay)
            path = out / f"{prefix}_{idx:02d}.jpg"
            cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            print("saved", path)
            idx += 1
            saved += 1
            last_saved = time.time()
        elif key in (ord("q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Done. Saved {saved} image(s) for '{args.label}'.")


if __name__ == "__main__":
    main()
