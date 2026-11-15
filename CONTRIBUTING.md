# Hướng Dẫn Đóng Góp (Contributing Guide) 🤝

Cảm ơn bạn đã quan tâm và muốn đóng góp cho dự án **Visual Vocabulary Agent (VVA)**! Sự tham gia của bạn giúp ứng dụng ngày càng thông minh, mượt mà và mang lại nhiều giá trị thiết thực hơn cho cộng đồng người học tiếng Anh.

Tài liệu này cung cấp các hướng dẫn chi tiết về quy trình làm việc, chiến lược phân nhánh, quy chuẩn commit và cách thức gửi Pull Request (PR) chuẩn mực.

---

## Mục lục
- [1. Bộ Quy tắc Ứng xử (Code of Conduct)](#1-bộ-quy-tắc-ứng-xử-code-of-conduct)
- [2. Thiết lập Môi trường Phát triển Cục bộ](#2-thiết-lập-môi-trường-phát-triển-cục-bộ)
- [3. Chiến lược Phân nhánh (Branching Strategy)](#3-chiến-lược-phân-nhánh-branching-strategy)
- [4. Quy chuẩn Đặt tên Commit (Conventional Commits)](#4-quy-chuẩn-đặt-tên-commit-conventional-commits)
- [5. Quy trình Gửi Pull Request (PR Process)](#5-quy-trình-gửi-pull-request-pr-process)
- [6. Tiêu chuẩn Chất lượng Mã nguồn](#6-tiêu-chuẩn-chất-lượng-mã-nguồn)
- [7. Báo cáo Lỗi & Đề xuất Tính năng](#7-báo-cáo-lỗi--đề-xuất-tính-năng)

---

## 1. Bộ Quy tắc Ứng xử (Code of Conduct)

Chúng tôi hướng tới việc xây dựng một môi trường đóng góp cởi mở, thân thiện và tôn trọng lẫn nhau. Mọi người tham gia đóng góp đều được kỳ vọng:
- Giao tiếp lịch sự, mang tính xây dựng và tôn trọng các góc nhìn khác nhau.
- Tập trung vào những gì mang lại lợi ích tốt nhất cho người dùng và chất lượng dự án.
- Tiếp nhận và đưa ra phản hồi phản biện một cách chuyên nghiệp.

---

## 2. Thiết lập Môi trường Phát triển Cục bộ

1. **Fork** repository này về tài khoản GitHub cá nhân của bạn.
2. **Clone** bản fork về máy cục bộ:
   ```bash
   git clone https://github.com/<your-username>/Visual_Vocabulary_Agent.git
   cd Visual_Vocabulary_Agent
   ```
3. Tạo môi trường ảo và cài đặt thư viện:
   ```bash
   python -m venv .venv
   # Kích hoạt trên Windows:
   .\.venv\Scripts\activate
   # Kích hoạt trên macOS/Linux:
   source .venv/bin/activate
   
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Cấu hình file `.env` với khóa API cá nhân (tuyệt đối không commit file `.env` này).
5. Khởi chạy thử ứng dụng để chắc chắn môi trường hoạt động bình thường:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

---

## 3. Chiến lược Phân nhánh (Branching Strategy)

Dự án áp dụng mô hình phân nhánh **Git Flow tinh gọn (Trunk-based with Feature Branches)**:

| Nhánh chính | Vai trò |
| :--- | :--- |
| `main` | Mã nguồn ổn định nhất, sẵn sàng triển khai thực tế. Được bảo vệ (Protected branch), chỉ merge qua Pull Request có review. |
| `develop` *(nếu có)* | Nhánh tích hợp cho phiên bản tiếp theo. |

### Quy tắc đặt tên nhánh phát triển (Feature/Bugfix Branches)
Tất cả các nhánh làm việc đều phải xuất phát từ `main` mới nhất và đặt tên theo định dạng chuẩn:
```text
<loại-nhánh>/<mô-tả-ngắn-gọn-kebab-case>
```

#### Các tiền tố quy định:
- `feature/` hoặc `feat/`: Phát triển tính năng mới.
  - *Ví dụ:* `feature/lip-tracking-mediapipe`, `feat/export-flashcard`
- `fix/` hoặc `bugfix/`: Sửa lỗi phát sinh trong hệ thống.
  - *Ví dụ:* `fix/sqlite-fallback-error`, `fix/audio-recording-ios`
- `refactor/`: Tái cấu trúc mã nguồn mà không thay đổi tính năng hay logic hoạt động.
  - *Ví dụ:* `refactor/vision-agent-pipeline`
- `docs/`: Thêm hoặc cập nhật tài liệu kỹ thuật, hướng dẫn sử dụng.
  - *Ví dụ:* `docs/update-installation-guide`
- `perf/`: Tối ưu hóa hiệu năng, giảm độ trễ, tối ưu bộ nhớ.
  - *Ví dụ:* `perf/cache-yolo-inference`
- `test/`: Thêm mới hoặc sửa đổi unit test, integration test.
  - *Ví dụ:* `test/add-chat-endpoint-tests`

---

## 4. Quy chuẩn Đặt tên Commit (Conventional Commits)

Dự án áp dụng chặt chẽ đặc tả **[Conventional Commits v1.0.0](https://www.conventionalcommits.org/)**.

### Cấu trúc thông điệp commit:
```text
<loại>(<phạm vi>): <mô tả ngắn bằng tiếng Việt hoặc tiếng Anh>

[Tùy chọn: Thân thông điệp giải thích chi tiết lý do và bối cảnh]

[Tùy chọn: Mã Issue đóng lại, ví dụ: Closes #12]
```

### Các Loại Commit (Types):
- `feat`: Thêm tính năng mới cho người dùng.
- `fix`: Sửa lỗi cho người dùng hoặc hệ thống.
- `docs`: Chỉ thay đổi tài liệu.
- `style`: Thay đổi định dạng code (khoảng trắng, dấu chấm phẩy, căn dòng) không ảnh hưởng logic.
- `refactor`: Thay đổi code không phải fix bug cũng không phải feat mới.
- `perf`: Cải thiện hiệu năng xử lý.
- `test`: Bổ sung hoặc sửa các bài kiểm thử.
- `chore`: Thay đổi quy trình build, cập nhật package phụ thuộc, cấu hình tooling.

### Phạm vi (Scope - Tùy chọn nhưng khuyến khích):
Xác định module hoặc file bị ảnh hưởng, ví dụ: `(vision)`, `(teacher)`, `(voice)`, `(chat)`, `(db)`, `(frontend)`, `(api)`.

### Ví dụ Commit chuẩn:
```text
feat(vision): tích hợp mô hình YOLO11n nhận diện vật thể từ camera
fix(db): xử lý bắt ngoại lệ khi SQL Server mất kết nối để kích hoạt SQLite fallback
docs(contributing): bổ sung quy tắc tạo nhánh và quy chuẩn commit
refactor(voice): tối ưu hàm gọi gTTS và xử lý định dạng audio wav
perf(yolo): cache mô hình nơ-ron trong bộ nhớ sau lần nạp đầu tiên
```

---

## 5. Quy trình Gửi Pull Request (PR Process)

Để duy trì chất lượng mã nguồn cao nhất, mỗi Pull Request phải tuân thủ các bước sau:

### Trước khi tạo PR:
1. Đồng bộ nhánh làm việc của bạn với `main` mới nhất:
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/ten-nhanh-cua-ban
   git rebase main
   ```
2. Kiểm tra không để lọt tệp nhạy cảm (`.env`, khóa API, thư mục `.venv`, ảnh upload tạm thời).
3. Chạy kiểm thử cục bộ đảm bảo không làm gãy các tính năng hiện có.
4. Nếu có chỉnh sửa giao diện, quét anti-pattern qua bộ công cụ `impeccable`:
   ```bash
   cmd.exe /c .agent\skills\impeccable\scripts\impeccable.cmd detect <file-thay-doi>
   ```

### Tạo PR trên GitHub:
1. Đặt tiêu đề PR theo chuẩn Conventional Commits (ví dụ: `feat(ipa): bổ sung tính năng phát lại âm thanh chậm cho người mới`).
2. Điền đầy đủ thông tin theo mẫu **PR Template**:
   ```markdown
   ## 📌 Tóm tắt Thay đổi
   Mô tả ngắn gọn về những thay đổi trong PR này và mục đích thực hiện.

   ## 🛠️ Các thay đổi chính
   - [x] Tích hợp API mới...
   - [x] Sửa lỗi giao diện responsive trên mobile...

   ## 🧪 Cách kiểm thử
   1. Truy cập vào trang `/learn-image`.
   2. Tải lên một ảnh mẫu và xác nhận bounding box hiển thị chính xác.

   ## 🔗 Issue liên quan
   Closes #42
   ```

### Quy trình Review & Merge:
- Mỗi PR cần có ít nhất **01 sự chấp thuận (Approval)** từ Maintainer.
- Tác giả phải giải quyết thỏa đáng tất cả các comment phản hồi trước khi được merge.
- Phương thức merge khuyến khích: **Squash and Merge** để giữ lịch sử nhánh `main` sạch sẽ.

---

## 6. Tiêu chuẩn Chất lượng Mã nguồn

### Đối với Backend (Python):
- Tuân thủ phong cách lập trình **PEP 8**.
- Luôn sử dụng **Type Hinting** cho các tham số hàm và giá trị trả về:
  ```python
  def generate_lesson_summary(word: str, ipa: str) -> dict[str, str]:
      ...
  ```
- Định nghĩa schema đầu vào/đầu ra rõ ràng bằng **Pydantic Models**.
- Bắt và xử lý ngoại lệ cẩn trọng, không sử dụng `except: pass` trống rỗng.

### Đối với Frontend (HTML/CSS/JS):
- Tuân thủ các nguyên tắc thiết kế trong **[AGENTS.md](file:///AGENTS.md)**:
  - **Không dùng emoji** làm biểu tượng tương tác chính (luôn dùng FontAwesome hoặc SVG).
  - Tỉ lệ tương phản màu chữ/nền phải đạt chuẩn **WCAG AA** ($\ge 4.5:1$).
  - Bố cục responsive linh hoạt, không gán chiều cao cứng cho các khối chứa văn bản.
  - Đảm bảo các phần tử nhấp được có `cursor: pointer` và hiệu ứng focus bàn phím rõ ràng.

---

## 7. Báo cáo Lỗi & Đề xuất Tính năng

- **Báo cáo lỗi (Bug Report):** Vui lòng cung cấp hệ điều hành, phiên bản Python, các bước tái hiện lỗi cụ thể và đính kèm thông báo lỗi (Traceback) nếu có.
- **Đề xuất tính năng (Feature Request):** Hãy nêu rõ trường hợp sử dụng (Use case), giải thích vì sao tính năng này hữu ích cho người học tiếng Anh và phác thảo hướng tiếp cận dự kiến.

*Chân thành cảm ơn sự đồng hành và đóng góp của bạn cho Visual Vocabulary Agent!*

