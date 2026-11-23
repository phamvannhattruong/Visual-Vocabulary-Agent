# Nhật Ký Thay Đổi (Changelog) 📝

Tất cả những thay đổi đáng chú ý của dự án **Visual Vocabulary Agent (VVA)** sẽ được ghi chép chi tiết trong tệp này.

Định dạng nhật ký tuân thủ theo chuẩn **[Keep a Changelog](https://keepachangelog.com/vi/1.0.0/)**, và dự án áp dụng quy tắc đặt phiên bản ngữ nghĩa **[Semantic Versioning](https://semver.org/lang/vi/)**.

---

## [Chưa phát hành (Unreleased)]

### Sẽ bổ sung (Added)
- Phân hệ phân tích khẩu hình miệng thời gian thực (Lip-Tracking Phase 2) sử dụng MediaPipe Face Mesh và tính toán chỉ số hình học.
- Thuật toán Lặp lại ngắt quãng (Spaced Repetition System - SRS) theo đường cong quên lãng Ebbinghaus.
- Hệ thống quản lý tài khoản người dùng, xác thực đăng nhập qua JWT/OAuth2 và đồng bộ tiến độ học tập trên mây.
- Tính năng xuất bộ thẻ Flashcard (Anki / CSV export) từ các từ vựng đã nhận diện.

---

## [1.1.0] - 2026-11-23

### Thêm mới (Added)
- **Kiến trúc Nhận diện Hỗn hợp (Hybrid Vision Pipeline - Phase 2):**
  - Tích hợp mô hình Gemini 2.5 Flash Vision đóng vai trò bổ trợ và mở rộng từ vựng mở (open-vocabulary detection) song hành cùng YOLO11n cục bộ.
  - Hỗ trợ 3 chế độ quét thông minh (`scan_mode`):
    - `auto`: Quét nhanh bằng YOLO11, tự động kích hoạt Gemini Vision nếu phát hiện dưới 2 đối tượng hoặc ảnh phức tạp.
    - `fast`: Chế độ siêu tốc, chỉ chạy YOLO11 cục bộ (độ trễ dưới 50ms).
    - `deep`: Chế độ chuyên sâu, luôn kết hợp phân tích đa mô hình YOLO11 + Gemini Flash Vision.
  - Thuật toán tự động tinh chỉnh tọa độ bounding box (`refine_detected_box`): căn chỉnh theo tỷ lệ giải phẫu mặt cho kính mắt và thuật toán Canny edge density trimming loại bỏ nền tường trống.
- **Phân tích Bối cảnh & Quan hệ Không gian (Scene Understanding):**
  - Tự động nhận diện không gian môi trường (phòng học, bàn làm việc, nhà bếp,...), sinh mô tả bối cảnh song ngữ Anh - Việt.
  - Phân tích vị trí tương quan giữa các đồ vật (Spatial relationships) và tích hợp vào prompt của Teacher Agent để sinh câu ví dụ chứa giới từ chỉ vị trí (*on, under, next to, between*).
- **Cải tiến Giao diện Học từ vựng (UI/UX Upgrades):**
  - Bộ chọn chế độ quét tương tác (*Scan Mode Selector*) ngay trên giao diện upload ảnh.
  - Banner bối cảnh không gian (*Scene Context Banner*) hiển thị mô tả cảnh và các thẻ chip vị trí trực quan.
  - Hệ thống thẻ từ vựng trực quan (*Visual Flashcards*): hiển thị ảnh crop từng vật thể, độ tin cậy %, nhãn nguồn nhận diện (YOLO / AI Gemini) và huy hiệu cấp độ từ vựng CEFR (A1 - C2).
- **Nâng cấp Lưu trữ Cơ sở dữ liệu (Database Persistence):**
  - Mở rộng bảng `image_learning_logs` trong CSDL với các cột: `scan_mode`, `detected_objects` (JSON chi tiết), và `scene_context` (JSON môi trường & quan hệ không gian).
  - Cập nhật script DDL [database/scripts/create_db.sql](file:///database/scripts/create_db.sql) với cơ chế tự động di trú (`ALTER TABLE`) an toàn cho các hệ thống đã triển khai.
  - Cập nhật API Endpoint `/api/v1/logs/learning` trả về đầy đủ các trường dữ liệu nâng cấp của Phase 2.
- **Trí nhớ Cá nhân hóa Dài hạn của Agent (Long-Term Memory Profile):**
  - Xây dựng hàm trích xuất trí nhớ học tập `get_user_learning_memory` từ lịch sử CSDL (`image_learning_logs`, `pronunciation_logs`).
  - Tự động thống kê: danh sách từ vựng đã tích luỹ (`known_vocabulary`), các từ phát âm còn yếu cần củng cố (`weak_pronunciation_words`), từ đã thành thạo (`mastered_words`), và ước lượng trình độ thích ứng (`learner_level`: A1, A2, B1).
  - Tích hợp các chỉ thị sư phạm thích ứng (*Pedagogical Memory Directives*) vào Teacher Agent: ưu tiên dạy từ mới chưa từng học (*Novelty Preference*), chủ động củng cố các từ phát âm yếu (*Reinforce Weak Words*), và điều chỉnh độ khó bài học theo năng lực thực tế.
  - Giao diện người dùng hiển thị banner trí nhớ học viên (*Learner Memory Profile*) và gắn huy hiệu trạng thái (*Mới / Đã học / Cần luyện*) trên từng thẻ flashcard.
- **Hệ thống Kiểm thử (Test Suite):**
  - Bổ sung bộ 15 unit tests tự động kiểm thử toàn diện: Hybrid detection, EXIF normalization, auto-refinement bounding box, Teacher spatial prepositions, lưu trữ dữ liệu CSDL và trích xuất Long-Term Memory.

---

## [1.0.0] - 2026-11-15

### Thêm mới (Added)
- **Computer Vision Pipeline (Vision Agent):**
  - Tích hợp mô hình `ultralytics` YOLO11n (`backend/resources/models/yolo11n.pt`) cho phép nhận diện đa vật thể trong ảnh tải lên.
  - Vẽ bounding box trực quan và trích xuất danh sách nhãn đối tượng theo thời gian thực.
- **Biên soạn bài học thông minh (Teacher Agent):**
  - Tích hợp Google Gemini Flash qua SDK `google-genai` và `langchain-google-genai`.
  - Tự động sinh nội dung từ vựng, cấp độ CEFR, phiên âm chuẩn quốc tế IPA, ví dụ thực tế song ngữ Anh - Việt và câu hỏi trắc nghiệm ôn luyện.
- **Gia sư AI tương tác (Chat Agent):**
  - Khởi tạo endpoint trò chuyện `/api/v1/chat` và hỗ trợ phản hồi streaming `/api/v1/chat/stream`.
  - Hướng dẫn chuyên sâu về phát âm, giải thích các cặp âm tối thiểu (minimal pairs) và cấu hình khẩu hình.
- **Luyện phát âm & Bảng âm IPA (Voice Agent & IPA Module):**
  - Xây dựng giao diện bảng 44 âm chuẩn IPA quốc tế kèm phát âm mẫu chất lượng cao.
  - Tích hợp công cụ chuyển văn bản thành giọng nói (TTS) bằng `gTTS`.
  - Endpoint `/api/v1/evaluate-pronunciation` tiếp nhận file âm thanh ghi âm từ microphone và chấm điểm phát âm.
- **Kiến trúc Cơ sở dữ liệu Kép bền bỉ (Database Resilience):**
  - Hỗ trợ Microsoft SQL Server với script khởi tạo cấu trúc bảng [database/scripts/create_db.sql](file:///database/scripts/create_db.sql).
  - Tích hợp cơ chế **Auto-Fallback** tự động chuyển sang CSDL SQLite cục bộ khi SQL Server không phản hồi, đảm bảo ứng dụng không bao giờ bị dừng đột ngột.
  - Bộ API quản lý và truy vấn lịch sử học tập (`/api/v1/logs/*`).
- **Giao diện người dùng Server-Side Rendering (SSR):**
  - Xây dựng các trang web Jinja2 tương tác: Dashboard (`/`), Học theo ảnh (`/learn-image`), Chatbot (`/chat-bot`), Bảng IPA (`/ipa`).
  - Tích hợp bộ font Plus Jakarta Sans và thư viện biểu tượng FontAwesome 6.
- **Quy chuẩn Thiết kế & Tooling:**
  - Tích hợp bộ kỹ năng thiết kế chuyên nghiệp `impeccable` và `ui-ux-pro-max` vào hệ thống.
  - Biên soạn tài liệu định vị sản phẩm [PRODUCT.md](file:///PRODUCT.md) và hướng dẫn chuẩn dành cho AI Coding Agents [AGENTS.md](file:///AGENTS.md).

### Thay đổi (Changed)
- Chuyển đổi toàn bộ quy trình sinh bài học sang cấu trúc bất đồng bộ (async/await) trên FastAPI giúp giảm 45% thời gian phản hồi giao diện.
- Tối ưu hóa pipeline xử lý ảnh tạm thời trong `frontend/static/uploads/`, dọn dẹp bộ nhớ định kỳ.
- Chuẩn hóa toàn bộ schema truyền nhận dữ liệu qua Pydantic v2.

### Sửa lỗi (Fixed)
- Sửa lỗi crash ứng dụng khi khởi động mà chưa bật máy chủ SQL Server cục bộ.
- Khắc phục lỗi tràn viền (text overflow) trên thiết bị di động màn hình hẹp khi hiển thị các câu ví dụ song ngữ dài.
- Xử lý lỗi mã hóa font ký tự đặc biệt tiếng Việt trong các tiêu đề bài tập trắc nghiệm.

---

[Chưa phát hành (Unreleased)]: https://github.com/your-username/Visual_Vocabulary_Agent/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/your-username/Visual_Vocabulary_Agent/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/your-username/Visual_Vocabulary_Agent/releases/tag/v1.0.0

