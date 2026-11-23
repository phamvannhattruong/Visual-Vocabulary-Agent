import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.settings import API_KEY_GEMINI, DEFAULT_GEMINI_MODEL, MODEL_DIR, UPLOAD_DIR
from backend.app.utils.content import extract_json_from_ai, get_relative_url

# Configure Ultralytics to store settings inside the project directory before importing YOLO
os.environ["YOLO_CONFIG_DIR"] = str(MODEL_DIR)

import cv2
import numpy as np
from PIL import Image, ImageOps
from ultralytics import YOLO

logger = logging.getLogger("backend.app.services.agents.vision")

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


# Comprehensive CEFR level and Vietnamese dictionary for COCO 80 classes
COCO_METADATA: Dict[str, Dict[str, str]] = {
    "person": {"vietnamese": "người", "cefr": "A1"},
    "bicycle": {"vietnamese": "xe đạp", "cefr": "A1"},
    "car": {"vietnamese": "ô tô", "cefr": "A1"},
    "motorcycle": {"vietnamese": "xe máy", "cefr": "A2"},
    "airplane": {"vietnamese": "máy bay", "cefr": "A2"},
    "bus": {"vietnamese": "xe buýt", "cefr": "A1"},
    "train": {"vietnamese": "tàu hỏa", "cefr": "A1"},
    "truck": {"vietnamese": "xe tải", "cefr": "A2"},
    "boat": {"vietnamese": "thuyền", "cefr": "A2"},
    "traffic light": {"vietnamese": "đèn giao thông", "cefr": "A2"},
    "fire hydrant": {"vietnamese": "trụ cứu hỏa", "cefr": "B1"},
    "stop sign": {"vietnamese": "biển báo dừng", "cefr": "A2"},
    "parking meter": {"vietnamese": "đồng hồ đỗ xe", "cefr": "B1"},
    "bench": {"vietnamese": "ghế dài", "cefr": "A2"},
    "bird": {"vietnamese": "con chim", "cefr": "A1"},
    "cat": {"vietnamese": "con mèo", "cefr": "A1"},
    "dog": {"vietnamese": "con chó", "cefr": "A1"},
    "horse": {"vietnamese": "con ngựa", "cefr": "A1"},
    "sheep": {"vietnamese": "con cừu", "cefr": "A1"},
    "cow": {"vietnamese": "con bò", "cefr": "A1"},
    "elephant": {"vietnamese": "con voi", "cefr": "A1"},
    "bear": {"vietnamese": "con gấu", "cefr": "A1"},
    "zebra": {"vietnamese": "ngựa vằn", "cefr": "A2"},
    "giraffe": {"vietnamese": "hươu cao cổ", "cefr": "A2"},
    "backpack": {"vietnamese": "ba lô", "cefr": "A2"},
    "umbrella": {"vietnamese": "cây dù / ô", "cefr": "A1"},
    "handbag": {"vietnamese": "túi xách", "cefr": "A2"},
    "tie": {"vietnamese": "cà vạt", "cefr": "A2"},
    "suitcase": {"vietnamese": "va li", "cefr": "A2"},
    "frisbee": {"vietnamese": "đĩa ném", "cefr": "B1"},
    "skis": {"vietnamese": "ván trượt tuyết", "cefr": "A2"},
    "snowboard": {"vietnamese": "ván trượt tuyết", "cefr": "A2"},
    "sports ball": {"vietnamese": "quả bóng", "cefr": "A1"},
    "kite": {"vietnamese": "con diều", "cefr": "A1"},
    "baseball bat": {"vietnamese": "gậy bóng chày", "cefr": "A2"},
    "baseball glove": {"vietnamese": "găng bóng chày", "cefr": "A2"},
    "skateboard": {"vietnamese": "ván trượt", "cefr": "A2"},
    "surfboard": {"vietnamese": "ván lướt sóng", "cefr": "A2"},
    "tennis racket": {"vietnamese": "vợt tennis", "cefr": "A2"},
    "bottle": {"vietnamese": "chai nước", "cefr": "A1"},
    "wine glass": {"vietnamese": "ly rượu", "cefr": "A2"},
    "cup": {"vietnamese": "cái cốc / tách", "cefr": "A1"},
    "fork": {"vietnamese": "cái nĩa", "cefr": "A1"},
    "knife": {"vietnamese": "con dao", "cefr": "A1"},
    "spoon": {"vietnamese": "cái thìa / muỗng", "cefr": "A1"},
    "bowl": {"vietnamese": "cái bát / tô", "cefr": "A1"},
    "banana": {"vietnamese": "quả chuối", "cefr": "A1"},
    "apple": {"vietnamese": "quả táo", "cefr": "A1"},
    "sandwich": {"vietnamese": "bánh mì kẹp", "cefr": "A1"},
    "orange": {"vietnamese": "quả cam", "cefr": "A1"},
    "broccoli": {"vietnamese": "súp lơ xanh", "cefr": "A2"},
    "carrot": {"vietnamese": "củ cà rốt", "cefr": "A1"},
    "hot dog": {"vietnamese": "bánh mì xúc xích", "cefr": "A1"},
    "pizza": {"vietnamese": "bánh pizza", "cefr": "A1"},
    "donut": {"vietnamese": "bánh vòng", "cefr": "A2"},
    "cake": {"vietnamese": "bánh ngọt", "cefr": "A1"},
    "chair": {"vietnamese": "cái ghế", "cefr": "A1"},
    "couch": {"vietnamese": "ghế sô pha", "cefr": "A2"},
    "potted plant": {"vietnamese": "chậu cây", "cefr": "A2"},
    "bed": {"vietnamese": "cái giường", "cefr": "A1"},
    "dining table": {"vietnamese": "bàn ăn", "cefr": "A1"},
    "toilet": {"vietnamese": "bồn cầu", "cefr": "A1"},
    "tv": {"vietnamese": "ti vi", "cefr": "A1"},
    "laptop": {"vietnamese": "máy tính xách tay", "cefr": "A2"},
    "mouse": {"vietnamese": "chuột máy tính", "cefr": "A1"},
    "remote": {"vietnamese": "điều khiển từ xa", "cefr": "A2"},
    "keyboard": {"vietnamese": "bàn phím", "cefr": "A2"},
    "cell phone": {"vietnamese": "điện thoại di động", "cefr": "A1"},
    "microwave": {"vietnamese": "lò vi sóng", "cefr": "A2"},
    "oven": {"vietnamese": "lò nướng", "cefr": "A2"},
    "toaster": {"vietnamese": "máy nướng bánh mì", "cefr": "B1"},
    "sink": {"vietnamese": "bồn rửa", "cefr": "A2"},
    "refrigerator": {"vietnamese": "tủ lạnh", "cefr": "A2"},
    "book": {"vietnamese": "quyển sách", "cefr": "A1"},
    "clock": {"vietnamese": "đồng hồ", "cefr": "A1"},
    "vase": {"vietnamese": "bình hoa", "cefr": "A2"},
    "scissors": {"vietnamese": "cái kéo", "cefr": "A2"},
    "teddy bear": {"vietnamese": "gấu bông", "cefr": "A1"},
    "hair drier": {"vietnamese": "máy sấy tóc", "cefr": "B1"},
    "toothbrush": {"vietnamese": "bàn chải đánh răng", "cefr": "A1"},
}

# Labels representing amorphous substances, background, or anatomical parts that should not have separate boxes
DISALLOWED_LABELS = {
    "water", "liquid", "air", "skin", "hair", "wall", "ceiling",
    "light", "shadow", "reflection", "face", "head", "body", "background",
    "room", "space", "door", "floor"
}


def calculate_iou(box_a: List[int], box_b: List[int]) -> float:
    """Calculate Intersection over Union (IoU) of two bounding boxes [x1, y1, x2, y2]."""
    x_a = max(box_a[0], box_b[0])
    y_a = max(box_a[1], box_b[1])
    x_b = min(box_a[2], box_b[2])
    y_b = min(box_a[3], box_b[3])

    inter_w = max(0, x_b - x_a)
    inter_h = max(0, y_b - y_a)
    inter_area = inter_w * inter_h

    box_a_area = max(1, (box_a[2] - box_a[0]) * (box_a[3] - box_a[1]))
    box_b_area = max(1, (box_b[2] - box_b[0]) * (box_b[3] - box_b[1]))

    union_area = float(box_a_area + box_b_area - inter_area)
    return inter_area / union_area if union_area > 0 else 0.0


class DetectAgent:
    """
    Hybrid Vision Agent:
    - Phase 1: Local YOLO11 object detection, EXIF normalization, and cropping.
    - Phase 2: Hybrid Gemini 2.5 Flash Vision for open-vocabulary detection,
               scene environment understanding, and spatial relations.
    """

    def __init__(self, model_name: str = "yolo11n.pt"):
        self.model_path = MODEL_DIR / model_name
        self.model = YOLO(str(self.model_path))
        self._gemini_client = None
        self._face_cascade = None

    def _get_face_cascade(self):
        """Lazy initialization of Haar cascade for facial geometry alignment."""
        if self._face_cascade is None:
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self._face_cascade = cv2.CascadeClassifier(cascade_path)
            except Exception as e:
                logger.debug(f"Could not load face cascade: {e}")
                self._face_cascade = None
        return self._face_cascade

    def refine_detected_box(self, img: np.ndarray, label: str, raw_box: List[int]) -> List[int]:
        """
        Auto-refine and snap bounding box coordinates:
        1. Specialized facial anatomy alignment for glasses/sunglasses.
        2. Edge density trimming for containers and everyday objects to eliminate empty background.
        """
        h, w = img.shape[:2]
        x1, y1, x2, y2 = raw_box
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(x1 + 1, min(x2, w))
        y2 = max(y1 + 1, min(y2, h))

        # 1. Specialized refinement for eyewear based on facial anatomy
        if label.lower() in ("glasses", "eyeglasses", "spectacles", "sunglasses"):
            face_cascade = self._get_face_cascade()
            if face_cascade is not None and not face_cascade.empty():
                try:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(
                        gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60)
                    )
                    for (fx, fy, fw, fh) in faces:
                        # Check if box overlaps with the detected face horizontally and vertically
                        if not (x2 < fx or x1 > fx + fw or y2 < fy or y1 > fy + fh):
                            # Eyeglasses sit across 8% to 92% of face width, and 28% to 58% of face height
                            gx1 = max(0, fx + int(fw * 0.08))
                            gx2 = min(w, fx + int(fw * 0.92))
                            gy1 = max(0, fy + int(fh * 0.28))
                            gy2 = min(h, fy + int(fh * 0.58))
                            return [int(gx1), int(gy1), int(gx2), int(gy2)]
                except Exception as e:
                    logger.debug(f"Eyewear facial refinement failed: {e}")

        # 2. General edge density trimming to eliminate empty background walls / padding
        roi = img[y1:y2, x1:x2]
        if roi.shape[0] >= 24 and roi.shape[1] >= 24:
            try:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
                edges = cv2.Canny(blurred, 30, 100)
                row_act = np.sum(edges > 0, axis=1)
                col_act = np.sum(edges > 0, axis=0)
                act_rows = np.where(row_act >= 3)[0]
                act_cols = np.where(col_act >= 3)[0]
                if len(act_rows) > 0 and len(act_cols) > 0:
                    r_min, r_max = act_rows[0], act_rows[-1]
                    c_min, c_max = act_cols[0], act_cols[-1]
                    rh, rw = roi.shape[:2]
                    pad_y = int(rh * 0.04)
                    pad_x = int(rw * 0.04)
                    new_y1 = y1
                    new_y2 = y2
                    new_x1 = x1
                    new_x2 = x2

                    # Trim if empty padding is at least 10%
                    if r_min > int(rh * 0.10):
                        new_y1 = max(0, y1 + r_min - pad_y)
                    if (rh - r_max) > int(rh * 0.10):
                        new_y2 = min(h, y1 + r_max + pad_y)
                    if c_min > int(rw * 0.10):
                        new_x1 = max(0, x1 + c_min - pad_x)
                    if (rw - c_max) > int(rw * 0.10):
                        new_x2 = min(w, x1 + c_max + pad_x)

                    if (new_x2 - new_x1) >= int(rw * 0.3) and (new_y2 - new_y1) >= int(rh * 0.3):
                        return [int(new_x1), int(new_y1), int(new_x2), int(new_y2)]
            except Exception as e:
                logger.debug(f"Edge density trimming failed: {e}")

        return [int(x1), int(y1), int(x2), int(y2)]

    def _get_gemini_client(self):
        """Lazy initialization of Google GenAI client for multimodal reasoning."""
        if self._gemini_client is None:
            if not API_KEY_GEMINI:
                return None
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=API_KEY_GEMINI)
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI Client: {e}")
                return None
        return self._gemini_client

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

    def _call_gemini_vision_analysis(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        Query Gemini 2.5 Flash Vision for open-vocabulary objects, scene context,
        and spatial relationships between detected entities.
        """
        client = self._get_gemini_client()
        if client is None:
            return None

        prompt = """
        You are a high-precision computer vision and English vocabulary education expert.
        Analyze this image and return a strictly structured JSON object.

        CRITICAL BOUNDING BOX & OBJECT DETECTION SPECIFICATIONS:
        1. "box_2d": [ymin, xmin, ymax, xmax] normalized integers strictly from 0 to 1000:
           - ymin: topmost edge of the object
           - xmin: leftmost edge of the object
           - ymax: bottommost edge of the object
           - xmax: rightmost edge of the object
           - Strictly ensure ymin < ymax and xmin < xmax.
        2. EXTREMELY TIGHT BOUNDING BOXES:
           - Bounding boxes MUST fit EXTREMELY TIGHTLY around the exact visible physical boundaries of the object.
           - Absolutely DO NOT include excess background, walls, ceiling, floor, or surrounding empty air.
        3. WEARABLE ACCESSORIES & EYEWEAR:
           - For "glasses" / "sunglasses": The box MUST tightly enclose ONLY the spectacles frame and lenses across the eyes and nose bridge (roughly the middle vertical area of the face). NEVER enclose the forehead, eyebrows, hair, chin, or whole head.
        4. CONTAINERS VS LIQUIDS:
           - For "cup", "mug", "glass", "bottle", "plastic cup": The box MUST fit the container tightly from the top rim down to the very base. DO NOT include empty wall above the rim.
           - DO NOT detect liquids or substances inside containers (e.g., DO NOT detect "water", "tea", "coffee", "beer"). Always detect the physical container itself ("cup", "glass", "bottle").
        5. PHYSICAL COUNTABLE OBJECTS ONLY:
           - Detect only tangible, countable objects useful for English learners (e.g., "cup", "pen", "notebook", "laptop", "glasses", "backpack", "watch", "chair").
           - NEVER detect amorphous substances, backgrounds, or body parts: DO NOT detect "water", "liquid", "air", "skin", "hair", "face", "head", "wall", "ceiling", "light", "shadow".

        Output format:
        {
          "scene": "General Setting / Room Type",
          "scene_vietnamese": "Tên không gian tiếng Việt",
          "description": "A 1-sentence English description of the scene.",
          "spatial_relationships": [
            "The cup is held next to the person.",
            "The glasses are worn on the face."
          ],
          "objects": [
            {
              "label": "glasses",
              "vietnamese": "kính mắt",
              "cefr_level": "A1",
              "confidence": 0.95,
              "box_2d": [450, 320, 580, 580]
            }
          ]
        }
        """

        candidate_models = []
        preferred_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", DEFAULT_GEMINI_MODEL]
        for m in preferred_models:
            if m and m not in candidate_models:
                candidate_models.append(m)

        for m in candidate_models:
            try:
                from google.genai import types
                image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                response = client.models.generate_content(
                    model=m,
                    contents=[prompt, image_part],
                )
                raw_text = response.text or ""
                parsed = extract_json_from_ai(raw_text)
                if isinstance(parsed, dict) and "objects" in parsed:
                    return parsed
                # Direct json parse attempt if extract_json_from_ai misses
                json_match = re.search(r"\{[\s\S]*\}", raw_text)
                if json_match:
                    return json.loads(json_match.group(0))
            except Exception as e:
                logger.warning(f"Gemini Vision analysis call with model {m} failed: {e}")
                continue
        return None

    @spaces.GPU
    def detect_objects(
        self,
        image_path: str | Path,
        conf_threshold: float = 0.35,
    ) -> Tuple[List[str], str | None, List[Dict[str, Any]]]:
        """Backward-compatible wrapper executing the default auto hybrid pipeline."""
        labels, output_path, detected_objects, _ = self.detect_hybrid(
            image_path=image_path,
            scan_mode="auto",
            conf_threshold=conf_threshold,
        )
        return labels, output_path, detected_objects

    @spaces.GPU
    def detect_hybrid(
        self,
        image_path: str | Path,
        scan_mode: str = "auto",
        conf_threshold: float = 0.35,
    ) -> Tuple[List[str], str | None, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Phase 2 Hybrid Detection:
        Combines local YOLO11 prediction with Gemini 2.5 Flash Vision
        for open-vocabulary detection and spatial scene reasoning.

        Args:
            image_path: Path to target image.
            scan_mode: "auto" (default: runs YOLO, invokes Gemini if <2 objects),
                       "fast" (YOLO only), or "deep" (always runs both).
            conf_threshold: Confidence threshold for YOLO detection.

        Returns:
            unique_labels: List of English vocabulary labels.
            annotated_path: Path to the annotated result image.
            detected_objects: Structured records with crops, CEFR, and source.
            scene_context: Environment and spatial relationships metadata.
        """
        path_obj = Path(image_path)
        img = self.normalize_image_orientation(path_obj)
        if img is None:
            return [], None, [], {"scene": "Unknown", "description": "", "spatial_relationships": []}

        h, w = img.shape[:2]
        runs_dir = MODEL_DIR / "runs"
        results = self.model.predict(source=img, conf=conf_threshold, save=False, project=str(runs_dir))

        crops_dir = UPLOAD_DIR / "crops"
        crops_dir.mkdir(parents=True, exist_ok=True)

        detected_objects: List[Dict[str, Any]] = []
        raw_labels: List[str] = []

        # 1. Process YOLO detections
        if results and len(results) > 0 and results[0].boxes is not None:
            for idx, box in enumerate(results[0].boxes):
                class_id = int(box.cls[0])
                label = str(self.model.names[class_id]).lower()
                confidence = float(box.conf[0])
                raw_labels.append(label)

                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                x1 = max(0, min(x1, w - 1))
                y1 = max(0, min(y1, h - 1))
                x2 = max(x1 + 1, min(x2, w))
                y2 = max(y1 + 1, min(y2, h))

                margin_x = int((x2 - x1) * 0.05)
                margin_y = int((y2 - y1) * 0.05)
                crop_x1 = max(0, x1 - margin_x)
                crop_y1 = max(0, y1 - margin_y)
                crop_x2 = min(w, x2 + margin_x)
                crop_y2 = min(h, y2 + margin_y)

                cropped_img = img[crop_y1:crop_y2, crop_x1:crop_x2]
                safe_label = re.sub(r"[^a-zA-Z0-9_-]", "_", label)
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

                meta = COCO_METADATA.get(label, {"vietnamese": label, "cefr": "A1"})

                detected_objects.append({
                    "id": idx + 1,
                    "label": label,
                    "vietnamese": meta.get("vietnamese", label),
                    "confidence": round(confidence, 3),
                    "confidence_percent": round(confidence * 100),
                    "box": [x1, y1, x2, y2],
                    "box_normalized": box_normalized,
                    "crop_url": crop_url,
                    "cefr_level": meta.get("cefr", "A1"),
                    "source": "yolo",
                })

        # 2. Prepare base annotated image
        annotated_frame = results[0].plot() if (results and len(results) > 0) else img.copy()

        # 3. Determine whether to invoke Gemini Vision (Hybrid Strategy)
        should_call_gemini = False
        if scan_mode == "deep":
            should_call_gemini = True
        elif scan_mode == "auto" and len(detected_objects) < 2:
            should_call_gemini = True

        scene_context: Dict[str, Any] = {
            "scene": "General Environment",
            "scene_vietnamese": "Không gian chung",
            "description": "General setting with everyday objects.",
            "spatial_relationships": [],
        }

        if should_call_gemini:
            try:
                # Read upright image bytes
                with open(path_obj, "rb") as f:
                    img_bytes = f.read()

                gemini_data = self._call_gemini_vision_analysis(img_bytes)
                if gemini_data:
                    # Update scene context
                    scene_context["scene"] = gemini_data.get("scene", "General Environment")
                    scene_context["scene_vietnamese"] = gemini_data.get("scene_vietnamese", "Không gian chung")
                    scene_context["description"] = gemini_data.get("description", "")
                    scene_context["spatial_relationships"] = gemini_data.get("spatial_relationships", [])

                    gemini_objects = gemini_data.get("objects", [])
                    next_id = len(detected_objects) + 1

                    for g_obj in gemini_objects:
                        g_label = str(g_obj.get("label", "")).strip().lower()
                        if not g_label or g_label in DISALLOWED_LABELS:
                            continue

                        g_box_2d = g_obj.get("box_2d", [])
                        if isinstance(g_box_2d, (list, tuple)) and len(g_box_2d) == 4:
                            ymin, xmin, ymax, xmax = g_box_2d
                            gx1 = int(max(0, min(w - 1, (xmin / 1000.0) * w)))
                            gy1 = int(max(0, min(h - 1, (ymin / 1000.0) * h)))
                            gx2 = int(max(gx1 + 1, min(w, (xmax / 1000.0) * w)))
                            gy2 = int(max(gy1 + 1, min(h, (ymax / 1000.0) * h)))
                        else:
                            gx1, gy1, gx2, gy2 = 0, 0, w, h

                        # Apply Auto-Refinement (facial anatomy alignment & edge density snapping)
                        refined_box = self.refine_detected_box(img, g_label, [gx1, gy1, gx2, gy2])
                        gx1, gy1, gx2, gy2 = refined_box
                        g_box = [gx1, gy1, gx2, gy2]

                        # Check if matches an existing YOLO object
                        matched_yolo = None
                        for y_obj in detected_objects:
                            if y_obj["source"] == "yolo":
                                iou = calculate_iou(g_box, y_obj["box"])
                                if iou > 0.35 or y_obj["label"].lower() == g_label:
                                    matched_yolo = y_obj
                                    break

                        if matched_yolo:
                            # Enrich YOLO object with Gemini Vietnamese translation and CEFR level
                            if g_obj.get("vietnamese"):
                                matched_yolo["vietnamese"] = g_obj["vietnamese"]
                            if g_obj.get("cefr_level"):
                                matched_yolo["cefr_level"] = g_obj["cefr_level"]
                        else:
                            # Create new object discovered by Gemini Flash
                            safe_label = re.sub(r"[^a-zA-Z0-9_-]", "_", g_label)
                            crop_filename = f"{path_obj.stem}_crop_{next_id}_{safe_label}.jpg"
                            crop_path = crops_dir / crop_filename

                            cropped_img = img[gy1:gy2, gx1:gx2]
                            if cropped_img.size > 0:
                                cv2.imwrite(str(crop_path), cropped_img)
                                crop_url = get_relative_url(str(crop_path))
                            else:
                                crop_url = None

                            conf = float(g_obj.get("confidence", 0.90))
                            cefr = g_obj.get("cefr_level", "A1")
                            vn_name = g_obj.get("vietnamese", g_label)

                            detected_objects.append({
                                "id": next_id,
                                "label": g_label,
                                "vietnamese": vn_name,
                                "confidence": round(conf, 3),
                                "confidence_percent": round(conf * 100),
                                "box": g_box,
                                "box_normalized": [
                                    round(gx1 / w, 4),
                                    round(gy1 / h, 4),
                                    round(gx2 / w, 4),
                                    round(gy2 / h, 4),
                                ],
                                "crop_url": crop_url,
                                "cefr_level": cefr,
                                "source": "gemini",
                            })
                            raw_labels.append(g_label)

                            # Draw annotation on frame for Gemini open-vocabulary items
                            # Cyan/Teal bounding box (BGR: 220, 180, 40)
                            cv2.rectangle(annotated_frame, (gx1, gy1), (gx2, gy2), (220, 180, 40), 2)
                            tag_text = f"{g_label} [{cefr}]"
                            (text_w, text_h), baseline = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                            cv2.rectangle(
                                annotated_frame,
                                (gx1, max(0, gy1 - text_h - 6)),
                                (gx1 + text_w + 6, max(text_h + 6, gy1)),
                                (220, 180, 40),
                                -1,
                            )
                            cv2.putText(
                                annotated_frame,
                                tag_text,
                                (gx1 + 3, max(text_h, gy1 - 3)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (255, 255, 255),
                                1,
                                cv2.LINE_AA,
                            )

                            next_id += 1

            except Exception as exc:
                logger.warning(f"Hybrid Gemini Vision enrichment skipped due to error: {exc}")

        # 4. Fallback scene context if not provided
        if not scene_context.get("spatial_relationships") and len(detected_objects) >= 2:
            first_label = detected_objects[0]["label"]
            second_label = detected_objects[1]["label"]
            scene_context["spatial_relationships"] = [
                f"The {first_label} is visible in the scene along with the {second_label}."
            ]

        unique_labels = list(dict.fromkeys(raw_labels))

        # 5. Save final annotated image
        output_path = path_obj.parent / f"{path_obj.stem}_result{path_obj.suffix}"
        cv2.imwrite(str(output_path), annotated_frame)

        return unique_labels, str(output_path), detected_objects, scene_context
