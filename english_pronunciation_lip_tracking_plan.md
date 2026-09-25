# Kế hoạch phát triển tính năng: Theo dõi khẩu hình miệng khi phát âm tiếng Anh

## 1. Giới thiệu & Mục tiêu
Xây dựng một hệ thống phân tích và đánh giá khẩu hình miệng theo thời gian thực (real-time) sử dụng Computer Vision nhằm hỗ trợ người học tiếng Anh so sánh khẩu hình của họ với người bản xứ.

---

## 2. Kiến trúc hệ thống & Công nghệ (Tech Stack & Architecture)

### A. Tech Stack đề xuất
*   **Computer Vision & Face Mesh:** MediaPipe Face Mesh (Google) – tối ưu vì nhẹ, chạy tốt trên cả CPU/GPU, cung cấp sẵn 468 điểm landmark (trong đó có vùng môi và miệng cực kỳ chi tiết).
*   **Xử lý số liệu & Toán học:** NumPy, SciPy (để tính toán khoảng cách Euclidean, góc mở miệng, tỷ lệ co giãn của môi).
*   **Mô hình phân loại (nếu cần nâng cao):** PyTorch hoặc Scikit-learn (dùng mô hình chuỗi thời gian như LSTM hoặc Random Forest để phân loại đúng/sai âm tiết dựa trên chuỗi landmark).
*   **Backend & Giao diện:** FastAPI (Python) hoặc WebRTC/React (nếu chạy trực tiếp trên browser qua TensorFlow.js / MediaPipe Tasks Vision).

### B. Luồng dữ liệu (Data Pipeline)
1.  **Capture:** Nhận luồng video từ Camera (Webcam/Mobile).
2.  **Detection & Extraction:** MediaPipe trích xuất tọa độ 3D các điểm mốc vùng môi (Lip Landmarks).
3.  **Feature Engineering:** Tính toán các chỉ số đặc trưng (ví dụ: khoảng cách giữa môi trên và môi dưới, độ rộng miệng khi phát âm âm /æ/ hay /u:/).
4.  **Comparison / Evaluation:** So sánh với bộ dữ liệu chuẩn (Template Matching) hoặc đưa qua mô hình Machine Learning để chấm điểm.
5.  **Feedback:** Trả về kết quả trực quan cho người dùng (Màu xanh: Đúng khẩu hình; Màu đỏ: Cần mở rộng miệng/mím môi hơn).

---

## 3. Phân rã tác vụ (Task Breakdown / Milestones)

### Giai đoạn 1: Khởi tạo và Trích xuất Landmark (2-3 ngày)
*   [ ] Thiết lập môi trường Python, cài đặt OpenCV và MediaPipe.
*   [ ] Viết script cơ bản bắt hình từ Webcam và hiển thị lưới điểm khuôn mặt (Face Mesh).
*   [ ] Lọc và cô lập riêng các điểm landmark thuộc vùng môi (Outer lips và Inner lips).

### Giai đoạn 2: Xây dựng thuật toán đánh giá đặc trưng (3-4 ngày)
*   [ ] Định nghĩa các âm khó trong tiếng Anh (ví dụ: /θ/, /ð/, /æ/, /ʊ/).
*   [ ] Tính toán các thông số hình học (Geometric features): Tỷ lệ chiều cao/chiều rộng miệng ($Aspect Ratio$), khoảng cách môi.
*   [ ] Xây dựng rule-based logic ban đầu cho 2-3 âm cơ bản để kiểm tra độ chính xác.

### Giai đoạn 3: Tích hợp và Tối ưu hiệu năng (2-3 ngày)
*   [ ] Đảm bảo tốc độ xử lý đạt tối thiểu 25-30 FPS (real-time) không bị giật lag.
*   [ ] Xây dựng giao diện hiển thị kết quả trực quan (Overlay hướng dẫn khẩu hình lên màn hình video).

### Giai đoạn 4: Kiểm thử và Đánh giá (2 ngày)
*   [ ] Viết Unit Test cho các hàm tính toán khoảng cách toán học.
*   [ ] Thực hiện thử nghiệm thực tế với các điều kiện ánh sáng khác nhau và tinh chỉnh độ nhạy.

---

## 4. Rủi ro kỹ thuật & Giải pháp phòng ngừa

1.  **Rủi ro 1: Sai lệch do góc máy quay (Angle & Pose Variation)**
    *   *Biểu hiện:* Người dùng nghiêng đầu hoặc ngồi lệch góc khiến tọa độ landmark bị biến dạng.
    *   *Giải pháp:* Chuẩn hóa tọa độ (Normalization) dựa trên khoảng cách giữa hai mắt hoặc chóp mũi trước khi tính toán vùng miệng, hoặc cảnh báo người dùng đưa mặt về chính diện.
2.  **Rủi ro 2: Điều kiện ánh sáng yếu (Poor Lighting)**
    *   *Biểu hiện:* MediaPipe mất track hoặc nhận diện sai điểm mốc môi.
    *   *Giải pháp:* Thêm bộ lọc kiểm tra độ sáng khung hình (Brightness threshold check), nếu tối quá sẽ hiển thị thông báo yêu cầu bật thêm đèn.
3.  **Rủi ro 3: Độ trễ (Latency) trên thiết bị yếu**
    *   *Biểu hiện:* Video bị giật, không đạt thời gian thực.
    *   *Giải pháp:* Giảm độ phân giải video đầu vào xuống mức 720p hoặc 480p, tinh chỉnh cấu hình MediaPipe ở chế độ `refine_landmarks=False` nếu không cần thiết.

---

## 5. Hướng dẫn chỉnh sửa & Tự kiểm định (Self-Correction & Review)

*   **Điểm yếu tiềm ẩn của kế hoạch:** Việc dùng Pure Rule-based (quy luật toán học thủ công) ở Giai đoạn 2 có thể không đủ độ chính xác với các âm phức tạp có khẩu hình biến đổi nhanh.
*   **Phương án thay thế / Nâng cấp:** Nếu dự án cần độ chính xác cao dạng AI thông minh, từ **Giai đoạn 2** nên chuyển hướng sang thu thập dataset nhỏ (video quay khẩu hình đúng của chính bạn/giáo viên) và huấn luyện một mô hình Lightweight Classifier (như Random Forest hoặc Neural Network nhỏ) thay vì chỉ dùng công thức toán học tĩnh.