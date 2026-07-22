🤖 **Visual Vocabulary Agent: Multi-Agent GenAI Learning System**

**Visual Vocabulary Agent** là một ứng dụng học tiếng Anh thông minh dựa trên công nghệ **Generative AI**. Hệ thống cho phép người dùng học từ vựng trực tiếp thông qua hình ảnh thực tế và luyện phát âm với sự đánh giá thời gian thực từ AI.

🌟 **Tính năng nổi bật**
* AI Vision Detection: Nhận diện vật thể từ ảnh tải lên hoặc webcam bằng mô hình YOLOv11.

* Multi-Agent Workflow: Phối hợp nhiều Agent (Vision, Teacher, Voice) để xử lý các tác vụ chuyên biệt.

* GenAI Lesson Generation: Tự động biên soạn bài học, ví dụ song ngữ và phiên âm IPA dựa trên ngữ cảnh hình ảnh.

* Interactive Quiz: Tạo câu hỏi trắc nghiệm tương tác để củng cố kiến thức ngay lập tức.

* Pronunciation Coach: Đánh giá phát âm trực tiếp từ file âm thanh của người dùng bằng khả năng đa phương thức của Gemini 1.5 Flash.

🏗️ **Kiến trúc hệ thống**
Dự án được xây dựng theo mô hình Client-Server tách biệt, giúp dễ dàng mở rộng và bảo trì:

* Backend: FastAPI (Python) điều phối các Agent và xử lý logic nghiệp vụ.

* Frontend: Streamlit cung cấp giao diện người dùng tương tác mượt mà.

* AI Models: * Gemini 1.5 Flash: "Bộ não" chính để soạn bài và đánh giá âm thanh.

* YOLO: Chuyên trách nhận diện vật thể thị giác.

* gTTS: Chuyển đổi văn bản thành giọng nói mẫu.

🚀 Hướng dẫn cài đặt

- git clone https://github.com/yourusername/Visual_Vocabulary_Agent.git

- cd Visual_Vocabulary_Agent

**Thiết lập môi trường ảo**:

- python -m venv .vva

- source .vva/bin/activate  # On Windows: .vva\Scripts\activate

**Cài đặt thư viện**:

- pip install -r requirements.txt

**Cấu hình API Key:**

- Tạo file .env ở thư mục gốc và thêm:

- API_KEY_GEMINI=your_gemini_api_key_here

🛠️ Cách chạy ứng dụng

* Khởi động Backend (FastAPI):

  - uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

* Khởi động Frontend (Streamlit):

  - streamlit run ui_streamlit.py

📝 Quy trình xử lý của Agent

User tải ảnh lên giao diện Streamlit.

Vision Agent nhận diện vật thể và trả về danh sách nhãn.

Teacher Agent nhận danh sách nhãn, soạn bài học và Quiz dưới dạng JSON.

Voice Agent nhận file ghi âm từ người dùng, so sánh với từ mục tiêu và trả về điểm số qua Gemini Multimodal.
