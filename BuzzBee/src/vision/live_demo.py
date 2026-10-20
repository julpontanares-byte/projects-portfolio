import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VID_EXT = {".mp4", ".avi", ".mov", ".mkv"}
FONT = cv2.FONT_HERSHEY_SIMPLEX
COLORS = [(255, 128, 0), (0, 170, 0), (190, 0, 190), (0, 120, 255), (0, 190, 230)]  # BGR, one per class
WIN = "Delivery Robot - sign recognition"
SHOT_DIR = Path("results/demo")
HEADER_H, FOOTER_H, MIN_W = 116, 30, 820
DESTS = ["exit", "mens_restroom", "womens_restroom"]   # destination markers
RED, GREEN, AMBER, BLUE, GRAY = (0, 0, 190), (0, 150, 0), (0, 150, 220), (190, 100, 0), (90, 90, 90)  # BGR


def fit(img, max_w=1280, max_h=720):
    """Shrink large images so they fit on screen (never enlarges)."""
    h, w = img.shape[:2]
    s = min(max_w / w, max_h / h, 1.0)
    return cv2.resize(img, (int(w * s), int(h * s))) if s < 1.0 else img


def letterbox(img, size=640):
    """Resize keeping the aspect ratio and pad to size x size (what the model receives)."""
    h, w = img.shape[:2]
    r = size / max(h, w)
    nh, nw = round(h * r), round(w * r)
    canvas = np.full((size, size, 3), 114, np.uint8)
    top, left = (size - nh) // 2, (size - nw) // 2
    canvas[top:top + nh, left:left + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    return canvas


def clip_text(text, max_w, scale=0.6, thickness=1):
    """Shorten text with '...' so it fits in max_w pixels (the info bars have a fixed width)."""
    if cv2.getTextSize(text, FONT, scale, thickness)[0][0] <= max_w:
        return text
    while len(text) > 4 and cv2.getTextSize(text + "...", FONT, scale, thickness)[0][0] > max_w:
        text = text[:-1]
    return text + "..."


def put_label(img, text, x, y, color):
    (tw, th), bl = cv2.getTextSize(text, FONT, 0.6, 2)
    y0 = max(y - th - bl, 0)
    cv2.rectangle(img, (x, y0), (x + tw + 4, y0 + th + bl), color, -1)
    cv2.putText(img, text, (x + 2, y0 + th), FONT, 0.6, (255, 255, 255), 2)


def annotate(frame, result, names):
    """Draw boxes, class names and confidence scores. Returns the image and the detections."""
    out = frame.copy()
    dets = []
    for b in result.boxes:
        cid, score = int(b.cls), float(b.conf)
        x1, y1, x2, y2 = (int(v) for v in b.xyxy[0].tolist())
        color = COLORS[cid % len(COLORS)]
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 3)
        put_label(out, f"{names[cid]} {score:.2f}", x1, y1, color)
        dets.append((names[cid], score))
    return out, dets


def decide(dets, target):
    """Basic decision logic: turn the recognized signs into what the robot would do. Returns (text, color)."""
    names = {n for n, _ in dets}
    pretty = lambda n: n.replace("_", " ")
    if "no_entry" in names:
        return "STOP - restricted area, turn away", RED
    if target in names:
        return f"STOP - delivery point reached ({pretty(target)})", GREEN
    if "slippery_floor" in names:
        return "SLOW DOWN - wet floor ahead", AMBER
    others = [n for n in DESTS if n in names]
    if others:
        return f"CONTINUE - {pretty(others[0])} is not the assigned destination", BLUE
    return "SEARCHING - no sign detected", GRAY


def next_target(key, target):
    """The D key cycles through the destination markers."""
    if key == ord("d"):
        return DESTS[(DESTS.index(target) + 1) % len(DESTS)]
    return target


def compose(annotated, original, dets, conf, note, fps, decision, target):
    """Add the info bars: settings, detections, preprocessing thumbnail and pipeline/keys."""
    h, w = annotated.shape[:2]
    cw = max(w, MIN_W)
    canvas = np.full((HEADER_H + h + FOOTER_H, cw, 3), 30, np.uint8)
    x0 = (cw - w) // 2
    canvas[HEADER_H:HEADER_H + h, x0:x0 + w] = annotated

    line1 = f"confidence >= {conf:.2f}  |  detections: {len(dets)}"
    if fps:
        line1 += f"  |  {fps:.1f} FPS"
    if note:
        line1 += f"  |  {note}"
    summary = "Detected: " + (", ".join(f"{n} {s:.2f}" for n, s in dets) if dets else "nothing above threshold")
    text_w = cw - 210  # keep clear of the "model input" thumbnail
    cv2.putText(canvas, clip_text(line1, text_w), (10, 26), FONT, 0.6, (255, 255, 255), 1)
    cv2.putText(canvas, clip_text(summary, text_w), (10, 58), FONT, 0.6, (0, 255, 255), 1)

    text, color = decision
    cv2.rectangle(canvas, (0, 88), (cw, HEADER_H - 2), color, -1)
    bar = f"TARGET: {target}   >   DECISION: {text}"
    cv2.putText(canvas, clip_text(bar, cw - 20, 0.6, 2), (10, 108), FONT, 0.6, (255, 255, 255), 2)

    thumb = cv2.resize(letterbox(original), (76, 76))
    canvas[4:80, cw - 84:cw - 8] = thumb
    cv2.putText(canvas, "model input", (cw - 190, 26), FONT, 0.5, (200, 200, 200), 1)
    cv2.putText(canvas, "640x640", (cw - 170, 46), FONT, 0.5, (200, 200, 200), 1)

    footer = "SEE > RECOGNIZE > DECIDE  |  Q quit  +/- conf  D target  S screenshot  N/P next/prev"
    cv2.putText(canvas, clip_text(footer, cw - 20, 0.5), (10, HEADER_H + h + 20), FONT, 0.5, (200, 200, 200), 1)
    return canvas


def predict(model, frame, conf, args):
    return model.predict(frame, conf=conf, imgsz=args.imgsz, verbose=False, device=args.device)[0]


def window_closed():
    """True if the user closed the window with the X button."""
    try:
        return cv2.getWindowProperty(WIN, cv2.WND_PROP_VISIBLE) < 1
    except cv2.error:
        return True


def adjust_conf(key, conf):
    if key in (ord("+"), ord("=")):
        return min(round(conf + 0.05, 2), 0.95)
    if key in (ord("-"), ord("_")):
        return max(round(conf - 0.05, 2), 0.05)
    return conf


def save_shot(img, tag):
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SHOT_DIR / f"{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}.png"
    cv2.imwrite(str(path), img)
    print("saved screenshot:", path)


def run_stream(cap, model, conf, args):
    fps, t_prev, target = 0.0, time.time(), args.destination
    while True:
        ok, frame = cap.read()
        if not ok:
            print("No more frames (or the camera feed was lost).")
            break
        frame = fit(frame)
        result = predict(model, frame, conf, args)
        shown_img, dets = annotate(frame, result, model.names)

        now = time.time()
        fps = 0.9 * fps + 0.1 / max(now - t_prev, 1e-6) if fps else 1.0 / max(now - t_prev, 1e-6)
        t_prev = now
        shown = compose(shown_img, frame, dets, conf, "", fps, decide(dets, target), target)
        cv2.imshow(WIN, shown)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27) or window_closed():
            break
        if key == ord("s"):
            save_shot(shown, "webcam")
        conf = adjust_conf(key, conf)
        target = next_target(key, target)


def run_images(images, model, conf, args):
    idx, dirty, shown, target = 0, True, None, args.destination
    while images:
        if dirty:
            path = images[idx]
            img = cv2.imread(str(path))
            if img is None:
                print("Could not read", path, "- skipping it.")
                images.pop(idx)
                idx = idx % len(images) if images else 0
                continue
            img = fit(img)
            result = predict(model, img, conf, args)
            shown_img, dets = annotate(img, result, model.names)
            decision = decide(dets, target)
            shown = compose(shown_img, img, dets, conf, f"{path.name} ({idx + 1}/{len(images)})", None, decision, target)
            print(f"{path.name}: " + (", ".join(f"{n} {s:.2f}" for n, s in dets) if dets else "no detections")
                  + f"  ->  [{target}] {decision[0]}")
            dirty = False

        cv2.imshow(WIN, shown)
        key = cv2.waitKey(50) & 0xFF
        if key in (ord("q"), 27) or window_closed():
            break
        new_conf = adjust_conf(key, conf)
        if new_conf != conf:
            conf, dirty = new_conf, True
        new_target = next_target(key, target)
        if new_target != target:
            target, dirty = new_target, True
        if key in (ord("n"), 32) and len(images) > 1:
            idx, dirty = (idx + 1) % len(images), True
        elif key == ord("p") and len(images) > 1:
            idx, dirty = (idx - 1) % len(images), True
        elif key == ord("s"):
            save_shot(shown, images[idx].stem)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/best.pt")
    ap.add_argument("--source", default=None, help="image, folder of images, or video file (default: webcam)")
    ap.add_argument("--conf", type=float, default=0.5, help="confidence threshold (change live with + and -)")
    ap.add_argument("--destination", default="mens_restroom", choices=DESTS,
                    help="the robot's assigned destination (change live with D)")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--camera", type=int, default=0, help="webcam index (try 1 if 0 is the wrong camera)")
    ap.add_argument("--device", default=None, help="e.g. cpu or 0 (default: auto)")
    args = ap.parse_args()

    if not Path(args.model).exists():
        sys.exit(f"Could not find the model file {args.model}. Run this from the repository root.")
    model = YOLO(args.model)
    print("Model loaded. Classes:", model.names)

    src = Path(args.source) if args.source else None
    if src is None or src.suffix.lower() in VID_EXT:
        if src is None:
            cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW) if sys.platform.startswith("win") \
                else cv2.VideoCapture(args.camera)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        else:
            cap = cv2.VideoCapture(str(src))
        if not cap.isOpened():
            sys.exit("Could not open the camera/video. Close other apps using the webcam or try --camera 1.")
        run_stream(cap, model, args.conf, args)
        cap.release()
    else:
        if src.is_dir():
            images = sorted(p for p in src.iterdir() if p.suffix.lower() in IMG_EXT)
        elif src.is_file() and src.suffix.lower() in IMG_EXT:
            images = [src]
        else:
            sys.exit(f"{src} is not an image, a folder of images, or a video.")
        if not images:
            sys.exit(f"No images found in {src}.")
        run_images(images, model, args.conf, args)
        if not images:
            print("None of the images could be read.")
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()