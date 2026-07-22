import cv2
from ultralytics import YOLO
import os
from pathlib import Path

class DetectAgent:
    def __init__(self, model_name = "yolo11n.pt"):
        # Resolve model path relative to this file
        current_dir = Path(__file__).resolve().parent
        model_dir = current_dir.parent / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_path = model_dir / model_name
        
        # If model doesn't exist, YOLO(str(path)) will download it to that path
        self.model = YOLO(str(self.model_path))

    def detect_objects(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return [], None

        results = self.model.predict(source=img, conf=0.4)

        detected_labels = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                label = self.model.names[class_id]
                detected_labels.append(label)

        unique_labels = list(set(detected_labels))

        # Plot result and save
        annotated_frame = results[0].plot()
        
        # Create output path: image_result.jpg in the same directory
        path_obj = Path(image_path)
        output_path = path_obj.parent / f"{path_obj.stem}_result{path_obj.suffix}"
        
        cv2.imwrite(str(output_path), annotated_frame)

        return unique_labels, str(output_path)
