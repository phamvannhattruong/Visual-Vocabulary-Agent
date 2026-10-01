"""
Lip Tracking & Mouth Mesh Extraction Demo (Phase 1)
---------------------------------------------------
Mục tiêu:
1. Bắt luồng video từ Webcam thời gian thực (real-time).
2. Nhận diện lưới điểm khuôn mặt (Face Mesh) với MediaPipe (Hỗ trợ cả MediaPipe 1.0+ Tasks API và bản cũ solutions API).
3. Cô lập, lọc và trực quan hóa chuyên biệt vùng môi (Outer lips, Inner lips).
4. Tính toán sơ bộ các chỉ số hình học (Mouth Width, Height, MAR) sẵn sàng cho Phase 2.
"""

import os
import cv2
import time
import math
import urllib.request
import numpy as np
from typing import Dict, List, Optional, Tuple

try:
    import mediapipe as mp
except ImportError:
    raise ImportError(
        "MediaPipe chưa được cài đặt. Vui lòng chạy lệnh: pip install mediapipe opencv-python numpy"
    )

# Tự động nhận diện API: Legacy Solutions API (MediaPipe < 0.10.30) vs Modern Tasks Vision API (MediaPipe >= 0.10.30 / 1.0+)
HAS_SOLUTIONS_API = hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh")

if not HAS_SOLUTIONS_API:
    from mediapipe.tasks import python as mp_tasks_python
    from mediapipe.tasks.python import vision as mp_tasks_vision

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
DEFAULT_MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
DEFAULT_MODEL_PATH = os.path.join(DEFAULT_MODEL_DIR, "face_landmarker.task")


def ensure_task_model(model_path: str = DEFAULT_MODEL_PATH) -> str:
    """Đảm bảo file model face_landmarker.task tồn tại, tự động tải từ CDN chính thức của MediaPipe nếu chưa có."""
    if os.path.exists(model_path):
        return model_path

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    print(f"[DOWNLOAD] Đang tải mô hình Face Landmarker về: {model_path}...")
    try:
        urllib.request.urlretrieve(MODEL_URL, model_path)
        print("[DOWNLOAD] Tải mô hình thành công!")
    except Exception as e:
        raise RuntimeError(
            f"Không thể tự động tải mô hình MediaPipe Face Landmarker từ {MODEL_URL}. Lỗi: {e}"
        )
    return model_path


class LipMeshTracker:
    """Bộ trích xuất và theo dõi khẩu hình miệng bằng MediaPipe Face Mesh (Tương thích kép)."""

    # Tọa độ chỉ số landmark chuẩn theo mô hình MediaPipe Face Mesh (468/478 điểm)
    # 1. Viền môi ngoài (Outer lips) theo thứ tự khép kín
    OUTER_LIPS: List[int] = [
        61, 185, 40, 39, 37, 0, 267, 269, 270, 409,
        291, 375, 321, 405, 314, 17, 84, 181, 91, 146, 61
    ]

    # 2. Viền môi trong (Inner lips) theo thứ tự khép kín
    INNER_LIPS: List[int] = [
        78, 191, 80, 81, 82, 13, 312, 311, 310, 415,
        308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78
    ]

    # 3. Các điểm mốc cốt lõi cho tính toán hình học phát âm
    KEY_POINTS: Dict[str, int] = {
        "left_corner": 61,       # Khóe miệng trái
        "right_corner": 291,     # Khóe miệng phải
        "top_outer": 0,          # Đỉnh môi trên ngoài
        "bottom_outer": 17,      # Đáy môi dưới ngoài
        "top_inner": 13,         # Đỉnh môi trên trong
        "bottom_inner": 14       # Đáy môi dưới trong
    }

    def __init__(
        self,
        max_num_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_path: Optional[str] = None
    ):
        """
        Khởi tạo MediaPipe Face Mesh với tính tương thích cao (cả MediaPipe mới và cũ).
        """
        self.use_legacy = HAS_SOLUTIONS_API

        if self.use_legacy:
            print("[INFO] Đang sử dụng MediaPipe Legacy Solutions API (mp.solutions.face_mesh).")
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=max_num_faces,
                refine_landmarks=refine_landmarks,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence
            )
            self.tesselation_connections = list(self.mp_face_mesh.FACEMESH_TESSELATION)
        else:
            print("[INFO] Đang sử dụng MediaPipe Tasks Vision API (FaceLandmarker).")
            task_model_path = model_path or ensure_task_model()
            base_options = mp_tasks_python.BaseOptions(model_asset_path=task_model_path)
            options = mp_tasks_vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=mp_tasks_vision.RunningMode.IMAGE,
                num_faces=max_num_faces,
                min_face_detection_confidence=min_detection_confidence,
                min_face_presence_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
                output_face_blendshapes=False
            )
            self.detector = mp_tasks_vision.FaceLandmarker.create_from_options(options)
            self.tesselation_connections = [
                (c.start, c.end) for c in mp_tasks_vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION
            ]

    def extract_landmarks(
        self, frame: np.ndarray
    ) -> Tuple[Optional[List[Tuple[int, int]]], Optional[object]]:
        """
        Xử lý frame và trả về danh sách tọa độ pixel (x, y) của tất cả landmark.
        """
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.use_legacy:
            # Đánh dấu không ghi để tối ưu tốc độ xử lý bộ nhớ
            rgb_frame.flags.writeable = False
            results = self.face_mesh.process(rgb_frame)
            rgb_frame.flags.writeable = True

            if not results.multi_face_landmarks:
                return None, None

            # Lấy khuôn mặt đầu tiên
            face_landmarks = results.multi_face_landmarks[0]
            landmarks_px = [
                (int(lm.x * w), int(lm.y * h))
                for lm in face_landmarks.landmark
            ]
            return landmarks_px, face_landmarks
        else:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            results = self.detector.detect(mp_image)
            if not results.face_landmarks:
                return None, None

            face_landmarks = results.face_landmarks[0]
            landmarks_px = [
                (int(lm.x * w), int(lm.y * h))
                for lm in face_landmarks
            ]
            return landmarks_px, face_landmarks

    @staticmethod
    def euclidean_dist(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Tính khoảng cách Euclidean giữa hai điểm (x, y)."""
        return math.dist(p1, p2)

    def compute_lip_metrics(self, landmarks_px: List[Tuple[int, int]]) -> Dict[str, float]:
        """
        Tính toán các chỉ số hình học cơ bản của khẩu hình:
        - mouth_width: Khoảng cách giữa 2 khóe miệng (Landmark 61 và 291).
        - inner_height: Độ hở trong giữa 2 môi (Landmark 13 và 14).
        - outer_height: Chiều cao toàn bộ môi ngoài (Landmark 0 và 17).
        - mar: Mouth Aspect Ratio (Tỷ lệ chiều cao / chiều rộng).
        """
        p_left = landmarks_px[self.KEY_POINTS["left_corner"]]
        p_right = landmarks_px[self.KEY_POINTS["right_corner"]]
        p_top_in = landmarks_px[self.KEY_POINTS["top_inner"]]
        p_bot_in = landmarks_px[self.KEY_POINTS["bottom_inner"]]
        p_top_out = landmarks_px[self.KEY_POINTS["top_outer"]]
        p_bot_out = landmarks_px[self.KEY_POINTS["bottom_outer"]]

        mouth_width = self.euclidean_dist(p_left, p_right)
        inner_height = self.euclidean_dist(p_top_in, p_bot_in)
        outer_height = self.euclidean_dist(p_top_out, p_bot_out)

        mar = (inner_height / mouth_width) if mouth_width > 0 else 0.0

        return {
            "mouth_width": mouth_width,
            "inner_height": inner_height,
            "outer_height": outer_height,
            "mar": mar
        }

    def draw_full_mesh(self, frame: np.ndarray, landmarks_px: List[Tuple[int, int]]) -> None:
        """Vẽ lưới Face Mesh toàn mặt (Tesselation)."""
        if not landmarks_px:
            return
        total_pts = len(landmarks_px)
        for start_idx, end_idx in self.tesselation_connections:
            if start_idx < total_pts and end_idx < total_pts:
                cv2.line(
                    frame,
                    landmarks_px[start_idx],
                    landmarks_px[end_idx],
                    (180, 180, 180),
                    1,
                    cv2.LINE_AA
                )

    def draw_lip_contours(
        self,
        frame: np.ndarray,
        landmarks_px: List[Tuple[int, int]],
        show_points: bool = True
    ) -> None:
        """Vẽ đường viền khép kín môi ngoài và môi trong với hiệu ứng màu phân tách."""
        # 1. Vẽ môi ngoài (Màu lục lam Cyan rực rỡ)
        outer_pts = np.array([landmarks_px[idx] for idx in self.OUTER_LIPS], dtype=np.int32)
        cv2.polylines(frame, [outer_pts], isClosed=True, color=(255, 230, 0), thickness=2)

        # 2. Vẽ môi trong (Màu đỏ cam Neon)
        inner_pts = np.array([landmarks_px[idx] for idx in self.INNER_LIPS], dtype=np.int32)
        cv2.polylines(frame, [inner_pts], isClosed=True, color=(0, 140, 255), thickness=2)

        # 3. Vẽ các điểm mốc (dots)
        if show_points:
            for idx in self.OUTER_LIPS:
                cv2.circle(frame, landmarks_px[idx], 2, (255, 255, 255), -1)
            for idx in self.INNER_LIPS:
                cv2.circle(frame, landmarks_px[idx], 2, (0, 255, 255), -1)

        # 4. Highlight đặc biệt các điểm mốc đo đạc chính
        key_colors = {
            "left_corner": (0, 255, 0),
            "right_corner": (0, 255, 0),
            "top_inner": (0, 0, 255),
            "bottom_inner": (0, 0, 255)
        }
        for name, idx in self.KEY_POINTS.items():
            if name in key_colors:
                pt = landmarks_px[idx]
                cv2.circle(frame, pt, 4, key_colors[name], -1)

    def close(self):
        """Giải phóng tài nguyên MediaPipe an toàn."""
        if self.use_legacy:
            if hasattr(self, "face_mesh") and self.face_mesh:
                self.face_mesh.close()
        else:
            if hasattr(self, "detector") and self.detector:
                try:
                    self.detector.close()
                except Exception:
                    pass


def run_lip_tracker(camera_index: int = 0, frame_width: int = 1280, frame_height: int = 720):
    """Vòng lặp chính thu nhận webcam, xử lý landmark và hiển thị HUD."""
    print("Khởi động Webcam và bộ trích xuất MediaPipe...")
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"[LỖI] Không thể mở Webcam ở cổng {camera_index}. Vui lòng kiểm tra lại thiết bị!")
        return

    # Cấu hình độ phân giải camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    tracker = LipMeshTracker()
    prev_time = time.time()
    fps = 0.0

    # Trạng thái hiển thị
    show_full_mesh = False
    show_landmarks = True

    print("\n--- HƯỚNG DẪN ĐIỀU KHIỂN ---")
    print("  [M]: Bật/Tắt hiển thị toàn bộ Face Mesh")
    print("  [L]: Bật/Tắt hiển thị các điểm mốc Lips (Dots)")
    print("  [Q] hoặc [ESC]: Thoát chương trình\n")

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success or frame is None:
                print("[CẢNH BÁO] Không đọc được frame từ webcam. Đang thử lại...")
                break

            # 1. Lật ảnh ngang (Mirror mode) để người dùng soi gương tự nhiên
            frame = cv2.flip(frame, 1)

            # 2. Tính toán FPS mượt mà
            current_time = time.time()
            dt = current_time - prev_time
            prev_time = current_time
            if dt > 0:
                current_fps = 1.0 / dt
                fps = 0.9 * fps + 0.1 * current_fps  # Smooth FPS

            # 3. Trích xuất Landmark môi
            landmarks_px, face_landmarks_raw = tracker.extract_landmarks(frame)

            # 4. Vẽ Face Mesh toàn mặt nếu được bật
            if show_full_mesh and landmarks_px:
                tracker.draw_full_mesh(frame, landmarks_px)

            # 5. Vẽ vùng môi và tính chỉ số
            if landmarks_px:
                # Vẽ viền và điểm mốc môi
                tracker.draw_lip_contours(frame, landmarks_px, show_points=show_landmarks)

                # Tính chỉ số hình học
                metrics = tracker.compute_lip_metrics(landmarks_px)

                # Xác định trạng thái miệng (Mở / Khép)
                mouth_state = "OPEN" if metrics["mar"] > 0.15 else "CLOSED"
                state_color = (0, 255, 0) if mouth_state == "OPEN" else (0, 200, 255)

                # Vẽ bảng HUD hiển thị chỉ số
                hud_overlay = frame.copy()
                cv2.rectangle(hud_overlay, (20, 20), (320, 210), (20, 20, 30), -1)
                cv2.addWeighted(hud_overlay, 0.7, frame, 0.3, 0, frame)
                cv2.rectangle(frame, (20, 20), (320, 210), (90, 80, 230), 2)

                cv2.putText(frame, "LIP TRACKING HUD (Phase 1)", (35, 48),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
                cv2.putText(frame, f"FPS: {fps:.1f}", (35, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 120), 2)
                cv2.putText(frame, f"Width: {metrics['mouth_width']:.1f} px", (35, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
                cv2.putText(frame, f"Inner Height: {metrics['inner_height']:.1f} px", (35, 138),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
                cv2.putText(frame, f"MAR (Ratio): {metrics['mar']:.3f}", (35, 166),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
                cv2.putText(frame, f"State: {mouth_state}", (35, 196),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, state_color, 2)
            else:
                # Cảnh báo không tìm thấy khuôn mặt
                cv2.putText(frame, "KHONG TIM THAY KHUON MAT", (30, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # 6. Hiển thị cửa sổ
            cv2.imshow("English Pronunciation Lip Tracker - Phase 1", frame)

            # 7. Bắt phím điều khiển
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q') or key == ord('Q'):
                print("Đang thoát...")
                break
            elif key == ord('m') or key == ord('M'):
                show_full_mesh = not show_full_mesh
                print(f"[TOGGLE] Full Face Mesh: {'BẬT' if show_full_mesh else 'TẮT'}")
            elif key == ord('l') or key == ord('L'):
                show_landmarks = not show_landmarks
                print(f"[TOGGLE] Lip Landmark Dots: {'BẬT' if show_landmarks else 'TẮT'}")

    except KeyboardInterrupt:
        print("\nNgắt bởi người dùng.")
    finally:
        # Giải phóng tài nguyên an toàn
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()
        print("Đã giải phóng Webcam và đóng các cửa sổ.")


if __name__ == "__main__":
    run_lip_tracker(camera_index=0)
