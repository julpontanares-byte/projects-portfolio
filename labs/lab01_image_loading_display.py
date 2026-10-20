from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np


def load_image(image_path: Path) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    return image


def display_image(image_bgr: np.ndarray) -> None:
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(6, 4))
    plt.imshow(image_rgb)
    plt.title("Sample OpenCV Image")
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    sample_image_path = Path(__file__).with_name("sample_image.png")

    if not sample_image_path.exists():
        sample_image = np.full((240, 320, 3), (30, 144, 255), dtype=np.uint8)
        cv2.putText(
            sample_image,
            "OpenCV Lab",
            (55, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imwrite(str(sample_image_path), sample_image)

    loaded_image = load_image(sample_image_path)
    display_image(loaded_image)
