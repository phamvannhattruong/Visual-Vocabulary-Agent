import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure Ultralytics config is within project models dir before importing any app modules
os.environ["YOLO_CONFIG_DIR"] = str(PROJECT_ROOT / "backend" / "resources" / "models")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import numpy as np
from PIL import Image

from backend.app.services.agents.vision import DetectAgent


class TestVisionAgentPhase1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = DetectAgent()
        cls.temp_dir = Path(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def test_normalize_image_orientation_with_exif(self):
        # Create an image with dimensions (100w, 50h)
        img_path = self.temp_dir / "exif_test.jpg"
        img = Image.new("RGB", (100, 50), color="blue")

        # EXIF tag 274 (0x0112) is Orientation. Value 6 means Rotate 90 CW
        exif = img.getexif()
        exif[274] = 6
        img.save(img_path, exif=exif)

        # Run normalize_image_orientation
        normalized_bgr = self.agent.normalize_image_orientation(img_path)
        self.assertIsNotNone(normalized_bgr)

        # After applying exif_transpose for orientation 6, dimensions should be swapped (50w, 100h)
        # In numpy array shape is (height, width, channels)
        h, w, c = normalized_bgr.shape
        self.assertEqual(h, 100)
        self.assertEqual(w, 50)
        self.assertEqual(c, 3)

    def test_detect_objects_structure(self):
        # Use existing test image
        test_img_path = Path("frontend/static/uploads/test.jpg")
        self.assertTrue(test_img_path.exists(), "test.jpg must exist for detection test")

        unique_labels, annotated_path, detected_objects = self.agent.detect_objects(test_img_path)

        # Check return types
        self.assertIsInstance(unique_labels, list)
        self.assertIsInstance(annotated_path, str)
        self.assertTrue(Path(annotated_path).exists())
        self.assertIsInstance(detected_objects, list)
        self.assertGreater(len(detected_objects), 0)

        # Check structure of detected items
        first_obj = detected_objects[0]
        required_keys = {
            "id",
            "label",
            "confidence",
            "confidence_percent",
            "box",
            "box_normalized",
            "crop_url",
        }
        self.assertTrue(required_keys.issubset(first_obj.keys()))

        # Check box coordinates
        box = first_obj["box"]
        self.assertEqual(len(box), 4)
        x1, y1, x2, y2 = box
        self.assertLess(x1, x2)
        self.assertLess(y1, y2)

        # Check normalized box coordinates
        box_norm = first_obj["box_normalized"]
        self.assertEqual(len(box_norm), 4)
        for val in box_norm:
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)

        # Check crop url
        if first_obj["crop_url"]:
            self.assertTrue(first_obj["crop_url"].startswith("/uploads/crops/"))


if __name__ == "__main__":
    unittest.main()
