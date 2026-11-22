import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure Ultralytics config is within project models dir before importing any app modules
os.environ["YOLO_CONFIG_DIR"] = str(PROJECT_ROOT / "backend" / "resources" / "models")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import numpy as np
from PIL import Image

from backend.app.services.agents.vision import DetectAgent, calculate_iou
from backend.app.services.agents.teacher import TeacherAgent


class TestVisionAgentPhase1And2(unittest.TestCase):
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
        h, w, c = normalized_bgr.shape
        self.assertEqual(h, 100)
        self.assertEqual(w, 50)
        self.assertEqual(c, 3)

    def test_calculate_iou(self):
        box1 = [0, 0, 10, 10]
        box2 = [0, 0, 10, 10]
        self.assertAlmostEqual(calculate_iou(box1, box2), 1.0)

        box3 = [20, 20, 30, 30]
        self.assertEqual(calculate_iou(box1, box3), 0.0)

        box4 = [5, 0, 15, 10]  # overlap 5x10 = 50, union = 100 + 100 - 50 = 150
        self.assertAlmostEqual(calculate_iou(box1, box4), 50.0 / 150.0, places=4)

    def test_detect_objects_backward_compatibility(self):
        test_img_path = Path("frontend/static/uploads/test.jpg")
        self.assertTrue(test_img_path.exists(), "test.jpg must exist for detection test")

        unique_labels, annotated_path, detected_objects = self.agent.detect_objects(test_img_path)

        self.assertIsInstance(unique_labels, list)
        self.assertIsInstance(annotated_path, str)
        self.assertTrue(Path(annotated_path).exists())
        self.assertIsInstance(detected_objects, list)
        self.assertGreater(len(detected_objects), 0)

        first_obj = detected_objects[0]
        required_keys = {
            "id",
            "label",
            "confidence",
            "confidence_percent",
            "box",
            "box_normalized",
            "crop_url",
            "cefr_level",
            "vietnamese",
            "source",
        }
        self.assertTrue(required_keys.issubset(first_obj.keys()))

    def test_detect_hybrid_fast_mode(self):
        test_img_path = Path("frontend/static/uploads/test.jpg")
        labels, output_path, detected_objects, scene_context = self.agent.detect_hybrid(
            test_img_path, scan_mode="fast"
        )

        self.assertIsInstance(labels, list)
        self.assertIsInstance(detected_objects, list)
        self.assertIsInstance(scene_context, dict)
        self.assertIn("scene", scene_context)

        # In fast mode, all objects should come from YOLO
        for obj in detected_objects:
            self.assertEqual(obj["source"], "yolo")
            self.assertIn("cefr_level", obj)
            self.assertIn("vietnamese", obj)

    def test_detect_hybrid_with_mocked_gemini(self):
        test_img_path = Path("frontend/static/uploads/test.jpg")
        mock_gemini_payload = {
            "scene": "Study Desk",
            "scene_vietnamese": "Bàn học tập",
            "description": "A student desk with laptop, stationery and notebook.",
            "spatial_relationships": [
                "The pencil is beside the notebook.",
                "The cup is positioned next to the laptop.",
            ],
            "objects": [
                {
                    "label": "pencil",
                    "vietnamese": "bút chì",
                    "cefr_level": "A1",
                    "confidence": 0.95,
                    "box_2d": [50, 50, 200, 200],
                },
                {
                    "label": "notebook",
                    "vietnamese": "vở ghi chép",
                    "cefr_level": "A2",
                    "confidence": 0.92,
                    "box_2d": [250, 250, 450, 450],
                },
            ],
        }

        with patch.object(self.agent, "_call_gemini_vision_analysis", return_value=mock_gemini_payload):
            labels, output_path, detected_objects, scene_context = self.agent.detect_hybrid(
                test_img_path, scan_mode="deep"
            )

            # Scene context should match mocked Gemini output
            self.assertEqual(scene_context["scene"], "Study Desk")
            self.assertEqual(scene_context["scene_vietnamese"], "Bàn học tập")
            self.assertEqual(len(scene_context["spatial_relationships"]), 2)

            # Check that Gemini objects were merged
            gemini_objects = [o for o in detected_objects if o["source"] == "gemini"]
            self.assertGreaterEqual(len(gemini_objects), 1)

            gemini_labels = [o["label"] for o in gemini_objects]
            self.assertIn("pencil", gemini_labels)

    def test_teacher_agent_with_scene_context(self):
        teacher = TeacherAgent()
        scene_ctx = {
            "scene": "Study Desk",
            "scene_vietnamese": "Bàn học",
            "description": "A desk with a cup and laptop",
            "spatial_relationships": ["The cup is next to the laptop"],
        }
        with patch.object(teacher, "generate_response", return_value="Lesson with prepositions [QUIZ_START]{}[QUIZ_END]"):
            result = teacher.generate_learning_content(["cup", "laptop"], scene_context=scene_ctx)
            self.assertIn("Lesson with prepositions", result)


if __name__ == "__main__":
    unittest.main()
