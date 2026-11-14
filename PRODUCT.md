# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Học sinh, sinh viên và người tự học tiếng Anh tại Việt Nam có nhu cầu mở rộng vốn từ vựng thực tế và chuẩn hóa phát âm IPA. Họ thường gặp khó khăn với phương pháp học truyền thống (ghi nhớ danh sách từ rời rạc) và phát âm sai do thiếu phản hồi trực quan.

## Product Purpose

Visual Vocabulary Agent (VVA) cung cấp trải nghiệm học tiếng Anh trực quan và chủ động. Người học tải ảnh từ môi trường xung quanh, AI nhận diện các đối tượng và tạo bài học ngữ cảnh tức thì (từ vựng, phiên âm IPA, câu ví dụ song ngữ, trắc nghiệm), kết hợp cùng gia sư AI đối thoại và luyện phát âm có phản hồi đa phương thức.

## Positioning

Học từ vựng trực quan theo ngữ cảnh thế giới thực kết hợp thị giác máy tính (YOLO nhận diện vật thể trong ảnh), AI tutor tạo nội dung học ngữ cảnh tức thời, và luyện phát âm đa phương thức (bảng IPA 44 âm, phản hồi giọng nói và phân tích khẩu hình miệng thời gian thực).

## Operating Context

- Môi trường trình duyệt web (Desktop và Mobile web).
- Tương tác với ảnh thực tế (chụp từ camera hoặc tải ảnh lên).
- Ghi âm microphone để luyện phát âm và nghe audio phát âm mẫu (TTS).
- Luyện phát âm trực tiếp qua webcam (định hướng phân tích khẩu hình Lip-tracking).

## Capabilities and Constraints

- **Capabilities:**
  - Nhận diện đối tượng trong ảnh bằng mô hình YOLO (`yolo11n.pt`).
  - Tự động sinh nội dung bài học, định nghĩa, phiên âm IPA, câu ví dụ song ngữ Anh - Việt và câu hỏi trắc nghiệm qua Gemini AI.
  - Chatbot gia sư AI hỗ trợ giải đáp thắc mắc, luyện phản xạ giao tiếp.
  - Bảng tra cứu và luyện 44 âm IPA tiếng Anh có phát âm audio mẫu.
  - Phân tích và chấm điểm phát âm từ audio thu âm.
  - (Đang phát triển) Đánh giá khẩu hình môi thời gian thực sử dụng MediaPipe Face Mesh.
- **Constraints:**
  - Backend sử dụng FastAPI (Python), frontend sử dụng HTML/CSS/JS thuần kết hợp Jinja2 templates.
  - Yêu cầu quyền truy cập Camera & Microphone trên trình duyệt để sử dụng đầy đủ các tính năng thu âm/hình ảnh.
  - Hỗ trợ lưu trữ dữ liệu với SQL Server hoặc tự động fallback sang SQLite cục bộ.

## Brand Commitments

- Tên ứng dụng: Visual Vocabulary Agent (VVA).
- Tông giọng (Tone & Voice): Thân thiện, khích lệ người học, chuẩn xác về mặt ngữ pháp & phát âm, giải thích song ngữ Anh - Việt dễ hiểu.
- Biểu tượng nhận diện: Cây đũa thần phép thuật (`fa-wand-magic-sparkles`) và phong cách trực quan, hiện đại.

## Evidence on Hand

- Mô hình YOLO11 (`backend/resources/models/yolo11n.pt`).
- Dữ liệu tri thức 44 âm IPA (`training/data/raw/ipa_data.json`, `training/data/raw/ipa_knowledge.txt`).
- Tập dữ liệu huấn luyện mẫu (`training/data/train_dataset.jsonl`).
- Kế hoạch phát triển tính năng phân tích khẩu hình (`english_pronunciation_lip_tracking_plan.md`).

## Product Principles

1. **Trực quan gắn liền thực tế:** Mọi từ vựng học được phải gắn với hình ảnh thực tế đời sống, biến môi trường xung quanh thành không gian học tập.
2. **Chuẩn hóa phát âm ngay từ đầu:** Kết hợp âm thanh, ký hiệu phiên âm IPA quốc tế và trực quan khẩu hình để người học không phát âm theo cảm tính.
3. **Phản hồi tức thì & Khích lệ:** Tự động tạo bài tập tương tác, chấm điểm và đưa ra hướng dẫn cải thiện cụ thể từ AI Tutor một cách nhanh chóng và thân thiện.
4. **Độ tin cậy & Sẵn sàng cao:** Kiến trúc xử lý mượt mà, hỗ trợ fallback cơ sở dữ liệu để trải nghiệm người học không bị gián đoạn.

