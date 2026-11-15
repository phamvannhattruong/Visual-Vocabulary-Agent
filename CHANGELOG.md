# Nhật Ký Thay Đổi (Changelog) 📝

Tất cả những thay đổi đáng chú ý của dự án **Visual Vocabulary Agent (VVA)** sẽ được ghi chép chi tiết trong tệp này.

Định dạng nhật ký tuân thủ theo chuẩn **[Keep a Changelog](https://keepachangelog.com/vi/1.0.0/)**, và dự án áp dụng quy tắc đặt phiên bản ngữ nghĩa **[Semantic Versioning](https://semver.org/lang/vi/)**.

---

## [Chưa phát hành (Unreleased)]

### Sẽ bổ sung (Added)
- Phân hệ phân tích khẩu hình miệng thời gian thực (Lip-Tracking) sử dụng MediaPipe Face Mesh.
- Thuật toán Lặp lại ngắt quãng (Spaced Repetition System - SRS) theo đường cong quên lãng Ebbinghaus.
- Hệ thống quản lý tài khoản người dùng, xác thực đăng nhập qua JWT/OAuth2 và đồng bộ tiến độ học tập trên mây.
- Tính năng xuất bộ thẻ Flashcard (Anki / CSV export) từ các từ vựng đã nhận diện.

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

[Chưa phát hành (Unreleased)]: https://github.com/your-username/Visual_Vocabulary_Agent/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-username/Visual_Vocabulary_Agent/releases/tag/v1.0.0
