import cv2
from ultralytics import YOLO
import os

class DetectAgent:
    def __init__(self, model_path = "yolo11n.pt"):
        if not os.path.exists('../models'):
            os.makedirs('../models')
        self.model = YOLO(f"../models/{model_path}")

    def detect_objects(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return None

        results = self.model.predict(source = img, conf= 0.4)

        detected_label = []

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                label = self.model.names[class_id]
                detected_label.append(label)

        unique_labels = list(set(detected_label))

        annotated_frame = results[0].plot()
        output_path = image_path.replace('.', '_result.')
        cv2.imwrite(output_path, annotated_frame)

        return unique_labels, annotated_frame

if __name__ == "__main__":
    # Đảm bảo bạn đã có một tấm ảnh tên 'test.jpg' trong cùng thư mục để thử
    engine = DetectAgent()
    labels, path = engine.detect_objects('test.jpg')
    print(f"Vật thể phát hiện được: {labels}")
    print(f"Ảnh kết quả lưu tại: {path}")
