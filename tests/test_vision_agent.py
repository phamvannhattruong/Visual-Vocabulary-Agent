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
        cls.addClassCleanup(shutil.rmtree, cls.temp_dir)
        cls.test_image = cls.temp_dir / "test.jpg"
        sample = PROJECT_ROOT / "frontend/static/uploads/test.jpg"
        if sample.is_file():
            shutil.copyfile(sample, cls.test_image)

        for target in ("backend.app.services.agents.vision.UPLOAD_DIR", "backend.app.utils.storage.UPLOAD_DIR"):
            upload_dir_patch = patch(target, cls.temp_dir)
            upload_dir_patch.start()
            cls.addClassCleanup(upload_dir_patch.stop)

    def sample_image(self):
        if not self.test_image.is_file():
            self.skipTest("Place a sample photo in frontend/static/uploads/test.jpg to run detection tests")
        return self.test_image

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
        unique_labels, annotated_path, detected_objects = self.agent.detect_objects(self.sample_image())

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
        labels, output_path, detected_objects, scene_context = self.agent.detect_hybrid(
            self.sample_image(), scan_mode="fast"
        )

        self.assertIsInstance(labels, list)
        self.assertIsInstance(detected_objects, list)
        self.assertIsInstance(scene_context, dict)
        self.assertIn("scene", scene_context)
        self.assertEqual(self.agent.model.get_providers(), ["CPUExecutionProvider"])
        self.assertGreater(len(detected_objects), 0)

        # In fast mode, all objects should come from YOLO
        for obj in detected_objects:
            self.assertEqual(obj["source"], "yolo")
            self.assertIn("cefr_level", obj)
            self.assertIn("vietnamese", obj)
            self.assertTrue((self.temp_dir / obj["crop_url"].removeprefix("/uploads/")).is_file())
            x1, y1, x2, y2 = obj["box_normalized"]
            self.assertTrue(0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1)

    def test_detect_hybrid_with_mocked_gemini(self):
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
                self.sample_image(), scan_mode="deep"
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

    def test_disallowed_labels_filtering(self):
        mock_payload_with_disallowed = {
            "scene": "Kitchen",
            "scene_vietnamese": "Nhà bếp",
            "description": "A glass of water.",
            "spatial_relationships": [],
            "objects": [
                {
                    "label": "water",  # Disallowed amorphous label
                    "vietnamese": "nước",
                    "cefr_level": "A1",
                    "confidence": 0.90,
                    "box_2d": [100, 100, 300, 300],
                },
                {
                    "label": "cup",
                    "vietnamese": "cái cốc",
                    "cefr_level": "A1",
                    "confidence": 0.94,
                    "box_2d": [100, 100, 400, 350],
                },
            ],
        }

        with patch.object(self.agent, "_call_gemini_vision_analysis", return_value=mock_payload_with_disallowed):
            labels, output_path, detected_objects, scene_context = self.agent.detect_hybrid(
                self.sample_image(), scan_mode="deep"
            )
            object_labels = [o["label"] for o in detected_objects]
            self.assertNotIn("water", object_labels, "'water' must be filtered by DISALLOWED_LABELS")

    def test_refine_detected_box_boundary_clamping(self):
        # Create dummy image
        dummy_img = np.zeros((200, 300, 3), dtype=np.uint8)
        # Box with coordinates outside boundaries
        raw_box = [-20, -10, 350, 250]
        refined = self.agent.refine_detected_box(dummy_img, "cup", raw_box)
        self.assertEqual(refined[0], 0)
        self.assertEqual(refined[1], 0)
        self.assertEqual(refined[2], 300)
        self.assertEqual(refined[3], 200)

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

    def test_teacher_agent_with_user_memory(self):
        teacher = TeacherAgent()
        user_mem = {
            "learner_level": "A2",
            "total_lessons": 8,
            "known_vocabulary": ["book", "chair", "laptop"],
            "weak_pronunciation_words": ["cup"],
            "mastered_words": ["laptop"],
        }
        captured_prompts = []

        def fake_generate(prompt):
            captured_prompts.append(prompt)
            return "Personalized Lesson [QUIZ_START]{}[QUIZ_END]"

        with patch.object(teacher, "generate_response", side_effect=fake_generate):
            result = teacher.generate_learning_content(["cup", "mouse"], user_memory=user_mem)
            self.assertIn("Personalized Lesson", result)
            self.assertEqual(len(captured_prompts), 1)
            prompt_text = captured_prompts[0]
            self.assertIn("Learner Long-Term Memory Profile", prompt_text)
            self.assertIn("Estimated CEFR Level: A2", prompt_text)
            self.assertIn("book, chair, laptop", prompt_text)
            self.assertIn("cup", prompt_text)
            self.assertIn("NOVELTY PREFERENCE", prompt_text)
            self.assertIn("REINFORCE WEAK WORDS", prompt_text)

    def test_teacher_agent_review_challenge_directives(self):
        """Verify prompt differentiates new vs already learned words and requests 3-question challenge with synonym lesson."""
        teacher = TeacherAgent()
        user_mem = {
            "learner_level": "B1",
            "total_lessons": 5,
            "known_vocabulary": ["bottle", "cup"],
            "weak_pronunciation_words": ["bottle"],
            "mastered_words": ["cup"],
        }
        captured_prompts = []

        def fake_generate(prompt):
            captured_prompts.append(prompt)
            return "Adaptive Lesson [QUIZ_START]{}[QUIZ_END]"

        with patch.object(teacher, "generate_response", side_effect=fake_generate):
            teacher.generate_learning_content(["bottle", "stapler"], user_memory=user_mem)
            self.assertEqual(len(captured_prompts), 1)
            prompt = captured_prompts[0]
            self.assertIn("New / Unencountered Vocabulary: stapler", prompt)
            self.assertIn("Already Learned Vocabulary (To Review): bottle", prompt)
            self.assertIn("3-Question Deep Review Challenge", prompt)
            self.assertIn("synonym_lesson", prompt)

    def test_extract_quiz_multi_questions_and_synonym_lesson(self):
        """Verify extract_quiz parses review challenge with synonym expansion lesson."""
        from backend.app.utils.parsers import extract_quiz

        ai_output = """Here is your visual lesson on bottle.
[QUIZ_START]
{
  "mode": "review_challenge",
  "target_word": "bottle",
  "questions": [
    {
      "id": 1,
      "type": "pronunciation",
      "question": "Phiên âm IPA của bottle?",
      "options": ["/ˈbɒtl/", "/ˈbʌtl/"],
      "answer": "/ˈbɒtl/"
    },
    {
      "id": 2,
      "type": "meaning",
      "question": "Nghĩa tiếng Việt của bottle?",
      "options": ["Cái chai", "Cái cốc"],
      "answer": "Cái chai"
    },
    {
      "id": 3,
      "type": "synonym",
      "question": "Từ gần nghĩa với bottle?",
      "options": ["flask", "pen"],
      "answer": "flask",
      "synonym_lesson": {
        "word": "flask",
        "ipa": "/flɑːsk/",
        "meaning_vn": "Bình giữ nhiệt",
        "example": "He carried a flask. (Anh ấy mang một bình giữ nhiệt.)"
      }
    }
  ]
}
[QUIZ_END]
"""
        clean_text, quiz_data = extract_quiz(ai_output)
        self.assertNotIn("[QUIZ_START]", clean_text)
        self.assertIsNotNone(quiz_data)
        self.assertEqual(quiz_data["mode"], "review_challenge")
        self.assertEqual(len(quiz_data["questions"]), 3)
        self.assertEqual(quiz_data["questions"][2]["synonym_lesson"]["word"], "flask")
        self.assertEqual(quiz_data["questions"][2]["synonym_lesson"]["ipa"], "/flɑːsk/")


if __name__ == "__main__":
    unittest.main()
