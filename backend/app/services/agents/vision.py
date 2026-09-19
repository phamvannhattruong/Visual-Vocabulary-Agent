import cv2
from ultralytics import YOLO
from pathlib import Path
from backend.app.core.settings import MODEL_DIR

class DetectAgent:
    def __init__(self, model_name = "yolo11n.pt"):
        self.model_path = MODEL_DIR / model_name
        
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

        # Class names are normally strings, but custom YOLO metadata can expose
        # a mapping for a class name.  A mapping cannot be put in a ``set`` and
        # would otherwise raise ``TypeError: unhashable type: 'dict'`` here.
        # Convert labels to the text the teacher agent expects while preserving
        # their detection order.
        unique_labels = list(dict.fromkeys(str(label) for label in detected_labels))

        # Plot result and save
        annotated_frame = results[0].plot()
        
        # Create output path: image_result.jpg in the same directory
        path_obj = Path(image_path)
        output_path = path_obj.parent / f"{path_obj.stem}_result{path_obj.suffix}"
        
        cv2.imwrite(str(output_path), annotated_frame)

        return unique_labels, str(output_path)
