import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from backend.app.core.settings import MODEL_DIR, UPLOAD_DIR
from backend.app.utils.content import get_relative_url

# Configure Ultralytics to store settings inside the project directory before importing YOLO
os.environ["YOLO_CONFIG_DIR"] = str(MODEL_DIR)

import cv2
import numpy as np
from PIL import Image, ImageOps
from ultralytics import YOLO


try:
    import spaces
except ImportError:
    # Fallback mock for non-ZeroGPU environments (local / testing)
    class _SpacesMock:
        @staticmethod
        def GPU(func=None, **kwargs):
            if func is not None:
                return func
            def decorator(fn):
                return fn
            return decorator
    spaces = _SpacesMock()

class DetectAgent:
    def __init__(self, model_name: str = "yolo11n.pt"):
        self.model_path = MODEL_DIR / model_name
        
        # If model doesn't exist, YOLO(str(path)) will download it to that path
        self.model = YOLO(str(self.model_path))

    def normalize_image_orientation(self, image_path: Path) -> np.ndarray | None:
        """
        Normalize image orientation using EXIF metadata and convert to BGR for OpenCV.
        Overwrites the file on disk so all downstream consumers receive the upright image.
        """
        try:
            with Image.open(image_path) as pil_img:
                transposed_img = ImageOps.exif_transpose(pil_img)
                if transposed_img is None:
                    transposed_img = pil_img

                if transposed_img.mode != "RGB":
                    transposed_img = transposed_img.convert("RGB")

                # Save corrected image back to image_path
                transposed_img.save(image_path, quality=95)

                img_rgb = np.array(transposed_img)
                return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        except Exception:
            return cv2.imread(str(image_path))

    @spaces.GPU
    def detect_objects(
        self,
        image_path: str | Path,
        conf_threshold: float = 0.35,
    ) -> Tuple[List[str], str | None, List[Dict[str, Any]]]:
        """
        Detect objects with:
        1. EXIF orientation correction.
        2. Bounding boxes & confidence extraction.
        3. Automated object cropping for visual vocabulary flashcards.

        Returns:
            unique_labels: List of unique object labels.
            annotated_path: Path to the annotated result image.
            detected_objects: List of structured detection records.
        """
        path_obj = Path(image_path)
        img = self.normalize_image_orientation(path_obj)
        if img is None:
            return [], None, []

        h, w = img.shape[:2]
        runs_dir = MODEL_DIR / "runs"
        results = self.model.predict(source=img, conf=conf_threshold, save=False, project=str(runs_dir))

        crops_dir = UPLOAD_DIR / "crops"
        crops_dir.mkdir(parents=True, exist_ok=True)

        detected_objects: List[Dict[str, Any]] = []
        raw_labels: List[str] = []

        if results and len(results) > 0 and results[0].boxes is not None:
            for idx, box in enumerate(results[0].boxes):
                class_id = int(box.cls[0])
                label = str(self.model.names[class_id])
                confidence = float(box.conf[0])
                raw_labels.append(label)

                # Bounding box pixel coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                # Clamp to image boundaries
                x1 = max(0, min(x1, w - 1))
                y1 = max(0, min(y1, h - 1))
                x2 = max(x1 + 1, min(x2, w))
                y2 = max(y1 + 1, min(y2, h))

                # Add a 5% margin around the crop for visually pleasing framing
                margin_x = int((x2 - x1) * 0.05)
                margin_y = int((y2 - y1) * 0.05)
                crop_x1 = max(0, x1 - margin_x)
                crop_y1 = max(0, y1 - margin_y)
                crop_x2 = min(w, x2 + margin_x)
                crop_y2 = min(h, y2 + margin_y)

                cropped_img = img[crop_y1:crop_y2, crop_x1:crop_x2]
                safe_label = re.sub(r"[^a-zA-Z0-9_-]", "_", label.lower())
                crop_filename = f"{path_obj.stem}_crop_{idx + 1}_{safe_label}.jpg"
                crop_path = crops_dir / crop_filename

                if cropped_img.size > 0:
                    cv2.imwrite(str(crop_path), cropped_img)
                    crop_url = get_relative_url(str(crop_path))
                else:
                    crop_url = None

                box_normalized = [
                    round(x1 / w, 4),
                    round(y1 / h, 4),
                    round(x2 / w, 4),
                    round(y2 / h, 4),
                ]

                detected_objects.append({
                    "id": idx + 1,
                    "label": label,
                    "confidence": round(confidence, 3),
                    "confidence_percent": round(confidence * 100),
                    "box": [x1, y1, x2, y2],
                    "box_normalized": box_normalized,
                    "crop_url": crop_url,
                })

        unique_labels = list(dict.fromkeys(raw_labels))

        output_path = path_obj.parent / f"{path_obj.stem}_result{path_obj.suffix}"
        if results and len(results) > 0:
            annotated_frame = results[0].plot()
            cv2.imwrite(str(output_path), annotated_frame)
        else:
            cv2.imwrite(str(output_path), img)

        return unique_labels, str(output_path), detected_objects

