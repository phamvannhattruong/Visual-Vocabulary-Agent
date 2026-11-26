"""Architecture, modularization, and route registration verification tests."""
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class TestArchitectureAndRoutes(unittest.TestCase):
    def test_main_app_import_and_routes(self):
        """Verify FastAPI app is correctly initialized with all pages and API routes."""
        from backend.app.main import app

        self.assertIsNotNone(app)
        self.assertEqual(app.title, "Visual Vocabulary Agent API")

        # Extract all registered paths, including from FastAPI 0.115+ _IncludedRouter
        registered_paths = set()
        for route in app.routes:
            if hasattr(route, "path"):
                registered_paths.add(route.path)
            elif hasattr(route, "original_router") and hasattr(route, "include_context"):
                pfx = getattr(route.include_context, "prefix", "") or ""
                for sub in route.original_router.routes:
                    sub_path = getattr(sub, "path", "")
                    registered_paths.add(pfx + sub_path)

        # 1. Verify SSR Web View Pages
        expected_pages = {"/", "/learn-image", "/chat-bot", "/ipa"}
        for page_path in expected_pages:
            self.assertIn(page_path, registered_paths, f"Missing Web Page route: {page_path}")

        # 2. Verify REST API Endpoints
        expected_apis = {
            "/api/v1/analyze",
            "/api/v1/evaluate-pronunciation",
            "/api/v1/chat",
            "/api/v1/chat-bot",
            "/api/v1/chat/stream",
            "/api/v1/logs/status",
            "/api/v1/logs/chat",
            "/api/v1/logs/learning",
            "/api/v1/logs/pronunciation",
            "/api/v1/logs/activities",
        }
        for api_path in expected_apis:
            self.assertIn(api_path, registered_paths, f"Missing API endpoint: {api_path}")

        # 3. Verify Static Mounts
        mounted_prefixes = {route.path for route in app.routes if hasattr(route, "name") and route.name in ("assets", "uploads")}
        self.assertIn("/assets", mounted_prefixes)
        self.assertIn("/uploads", mounted_prefixes)

    def test_utils_modularization_and_backward_compatibility(self):
        """Verify storage and parsers are separated and content.py proxy works 100%."""
        # 1. Direct module imports
        from backend.app.utils.storage import save_upload_file, get_relative_url
        from backend.app.utils.parsers import extract_json_from_ai, extract_quiz, build_message_list

        self.assertTrue(callable(save_upload_file))
        self.assertTrue(callable(get_relative_url))
        self.assertTrue(callable(extract_json_from_ai))
        self.assertTrue(callable(extract_quiz))
        self.assertTrue(callable(build_message_list))

        # 2. Backward compatibility proxy through content.py
        import backend.app.utils.content as content_proxy

        self.assertIs(content_proxy.save_upload_file, save_upload_file)
        self.assertIs(content_proxy.get_relative_url, get_relative_url)
        self.assertIs(content_proxy.extract_json_from_ai, extract_json_from_ai)
        self.assertIs(content_proxy.extract_quiz, extract_quiz)
        self.assertIs(content_proxy.build_message_list, build_message_list)

        # 3. Test parsers logic directly
        text_with_json = 'Some text {"score": 95, "feedback": "Good job"} other text'
        parsed = extract_json_from_ai(text_with_json)
        self.assertEqual(parsed, {"score": 95, "feedback": "Good job"})

        text_with_quiz = 'Lesson text\n[QUIZ_START]\n{"question": "Q1", "options": ["A", "B"], "answer": "A"}\n[QUIZ_END]'
        clean_text, quiz_obj = extract_quiz(text_with_quiz)
        self.assertEqual(clean_text, "Lesson text")
        self.assertEqual(quiz_obj, {"question": "Q1", "options": ["A", "B"], "answer": "A"})

    def test_services_agents_exports(self):
        """Verify services.agents exposes all agent classes cleanly."""
        from backend.app.services.agents import (
            Agent,
            DetectAgent,
            TeacherAgent,
            VoiceAgent,
            ChatAgent,
        )
        self.assertTrue(callable(Agent))
        self.assertTrue(callable(DetectAgent))
        self.assertTrue(callable(TeacherAgent))
        self.assertTrue(callable(VoiceAgent))
        self.assertTrue(callable(ChatAgent))

    def test_settings_centralization(self):
        """Verify core settings exports all necessary directories and configs."""
        from backend.app.core.settings import (
            PROJECT_ROOT,
            FRONTEND_DIR,
            TEMPLATES_DIR,
            ASSETS_DIR,
            UPLOAD_DIR,
            CROPS_DIR,
            MODEL_DIR,
            DATABASE_DIR,
            DATABASE_URL,
            DEFAULT_GEMINI_MODEL,
            DEFAULT_YOLO_MODEL,
        )
        self.assertTrue(PROJECT_ROOT.exists())
        self.assertTrue(TEMPLATES_DIR.exists())
        self.assertTrue(ASSETS_DIR.exists())
        self.assertTrue(UPLOAD_DIR.exists())
        self.assertTrue(CROPS_DIR.exists())
        self.assertTrue(MODEL_DIR.exists())
        self.assertTrue(DATABASE_DIR.exists())
        self.assertIsNotNone(DATABASE_URL)
        self.assertEqual(DEFAULT_GEMINI_MODEL, "gemini-2.5-flash")
        self.assertEqual(DEFAULT_YOLO_MODEL, "yolo11n.onnx")

    def test_image_learning_log_phase2_db_persistence(self):
        """Verify image learning log stores and retrieves Phase 2 metadata correctly."""
        import json
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.app.db.base import Base
        from backend.app.db.models import ImageLearningLog
        from backend.app.db.crud import log_image_learning, get_image_logs

        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestSession = sessionmaker(bind=test_engine)

        with TestSession() as db:
            log_entry = log_image_learning(
                db=db,
                file_name="test_scene.jpg",
                detected_labels=["laptop", "cup"],
                annotated_img_url="/uploads/test_scene_annotated.jpg",
                lesson_context="Here is your lesson.",
                quiz_data={"question": "What is on the desk?", "options": ["laptop", "apple"], "answer": "laptop"},
                scan_mode="deep",
                detected_objects=[
                    {"id": 1, "label": "laptop", "cefr_level": "A1", "source": "yolo"},
                    {"id": 2, "label": "cup", "cefr_level": "A1", "source": "gemini"},
                ],
                scene_context={
                    "scene": "Workspace",
                    "scene_vietnamese": "Góc làm việc",
                    "description": "Modern desk with a laptop and a coffee cup.",
                    "spatial_relationships": ["The cup is next to the laptop."],
                },
            )
            self.assertIsNotNone(log_entry.id)
            self.assertEqual(log_entry.scan_mode, "deep")

            logs = get_image_logs(db=db, limit=10)
            self.assertEqual(len(logs), 1)
            saved = logs[0]
            self.assertEqual(saved.file_name, "test_scene.jpg")
            self.assertEqual(saved.scan_mode, "deep")

            # Verify JSON deserialization of Phase 2 columns
            objects = json.loads(saved.detected_objects)
            self.assertEqual(len(objects), 2)
            self.assertEqual(objects[0]["label"], "laptop")
            self.assertEqual(objects[1]["source"], "gemini")

            scene = json.loads(saved.scene_context)
            self.assertEqual(scene["scene"], "Workspace")
            self.assertEqual(scene["spatial_relationships"], ["The cup is next to the laptop."])

    def test_user_learning_memory_profile(self):
        """Verify get_user_learning_memory compiles past logs into an agent memory profile."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.app.db.base import Base
        from backend.app.db.crud import (
            get_or_create_user,
            log_image_learning,
            log_pronunciation,
            get_user_learning_memory,
        )
        from backend.app.schemas.learning import LearnerMemory

        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestSession = sessionmaker(bind=test_engine)

        with TestSession() as db:
            user = get_or_create_user(db, "learner_agent_test")

            # Save 1 image log with objects
            log_image_learning(
                db=db,
                file_name="desk.jpg",
                detected_labels=["laptop", "cup", "pen"],
                annotated_img_url="/uploads/desk.jpg",
                lesson_context="Lesson text",
                quiz_data={"question": "Q"},
                scan_mode="auto",
                scene_context={"scene": "Study Desk", "scene_vietnamese": "Bàn học"},
                user_id=user.id,
            )

            # Save pronunciation logs
            log_pronunciation(
                db=db,
                target_word="laptop",
                score=88,
                feedback="Excellent pronunciation",
                tip="Keep it up",
                user_id=user.id,
            )
            log_pronunciation(
                db=db,
                target_word="pen",
                score=62,
                feedback="Need more aspiration",
                tip="Release more air",
                user_id=user.id,
            )

            # Extract memory profile
            memory_data = get_user_learning_memory(db=db, user_id=user.id)

            self.assertEqual(memory_data["user_id"], user.id)
            self.assertEqual(memory_data["total_lessons"], 1)
            self.assertIn("laptop", memory_data["known_vocabulary"])
            self.assertIn("cup", memory_data["known_vocabulary"])
            self.assertIn("pen", memory_data["known_vocabulary"])
            self.assertIn("pen", memory_data["weak_pronunciation_words"])
            self.assertIn("laptop", memory_data["mastered_words"])
            self.assertIn("Study Desk", memory_data["recent_scenes"])
            self.assertEqual(memory_data["learner_level"], "A1")

            # Validate against Pydantic schema
            learner_memory_obj = LearnerMemory(**memory_data)
            self.assertEqual(learner_memory_obj.known_vocabulary_count, 3)
            self.assertEqual(len(learner_memory_obj.weak_pronunciation_words), 1)


if __name__ == "__main__":
    unittest.main()
