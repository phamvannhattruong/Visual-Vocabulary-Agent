# Visual Vocabulary Agent

Một ứng dụng học từ vựng tiếng Anh theo hướng trực quan, kết hợp giữa nhận diện vật thể bằng computer vision, AI tutor và đánh giá phát âm. Dự án hiện tại đang hoạt động theo mô hình FastAPI + Jinja templates + static frontend, với các AI agent xử lý chuyên biệt cho hình ảnh, bài học và giọng nói.

## Tóm tắt dự án

Visual Vocabulary Agent giúp người học:

- Tải lên ảnh và nhận diện các đối tượng trong hình bằng YOLO
- Tạo nội dung học từ vựng theo đối tượng được phát hiện
- Sinh câu ví dụ song ngữ, IPA và câu hỏi trắc nghiệm
- Luyện phát âm với audio đầu vào và nhận phản hồi từ AI
- Truy cập giao diện web để học theo nhiều chế độ: dashboard, học theo ảnh, chatbot, IPA

## Công nghệ sử dụng

- Backend: FastAPI
- Frontend: HTML / CSS / JavaScript + Jinja templates
- AI: Google Gemini via `google-genai` và `langchain-google-genai`
- Computer Vision: Ultralytics YOLO
- Text-to-Speech: gTTS
- Cấu hình: Python dotenv
- Data training: scripts trong thư mục `training/`

## Cấu trúc project hiện tại

```text
Visual_Vocabulary_Agent/
├── Dockerfile
├── README.md
├── requirements.txt
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── chat.py
│   │   │       └── learning.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── settings.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py
│   │   │   └── pronunciation.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── agents/
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── chat.py
│   │   │       ├── teacher.py
│   │   │       ├── vision.py
│   │   │       └── voice.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── content.py
│   └── resources/
│       └── models/
│           └── yolo11n.pt
├── frontend/
│   ├── assets/
│   │   ├── scripts/
│   │   │   ├── app.js
│   │   │   ├── chat.js
│   │   │   └── ipa.js
│   │   └── styles/
│   │       ├── chatbot.css
│   │       ├── dashboard.css
│   │       ├── imagelearn.css
│   │       └── ipa.css
│   ├── static/
│   │   └── uploads/
│   └── templates/
│       ├── chatbot.html
│       ├── dashboard.html
│       ├── imagelearn.html
│       └── ipa.html
└── training/
    ├── data/
    │   ├── train_dataset.jsonl
    │   └── raw/
    │       ├── ipa_data.json
    │       └── ipa_knowledge.txt
    └── scripts/
        ├── craw_44_ipa.py
        └── generate_chat.py
```

## Thành phần chính

### 1. Backend API

- `backend/app/main.py`: khởi tạo ứng dụng FastAPI và routing chính
- `backend/app/api/routes/learning.py`: xử lý ảnh upload, nhận diện vật thể, sinh nội dung học tập
- `backend/app/api/routes/chat.py`: API chatbot giáo viên AI

### 2. AI agents

- `backend/app/services/agents/base.py`: lớp base cho các agent, cấu hình Gemini và xử lý content
- `backend/app/services/agents/vision.py`: nhận diện đối tượng bằng YOLO
- `backend/app/services/agents/teacher.py`: tạo bài học, ví dụ và quiz từ danh sách đối tượng phát hiện
- `backend/app/services/agents/voice.py`: chuyển văn bản thành giọng nói và đánh giá phát âm
- `backend/app/services/agents/chat.py`: tạo phản hồi chatbot cho người học

### 3. Frontend

- `frontend/templates/`: giao diện dashboard, học theo ảnh, chatbot, IPA
- `frontend/assets/styles/`: file CSS cho từng màn hình
- `frontend/assets/scripts/`: logic JavaScript tương tác
- `frontend/static/uploads/`: thư mục lưu ảnh người dùng upload

### 4. Training data

- `training/data/`: dữ liệu huấn luyện và raw data cho IPA
- `training/scripts/`: script crawl / generate dataset

## Môi trường và cài đặt

### Yêu cầu

- Python 3.10+
- pip
- Git

### 1. Clone project

```bash
git clone <repository-url>
cd Visual_Vocabulary_Agent
```

### 2. Tạo môi trường ảo

Trên Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Trên macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Cài đặt dependency

```bash
pip install -r requirements.txt
```

### 4. Cấu hình biến môi trường

Tạo file `.env` ở thư mục gốc và thêm các biến sau:

```env
API_KEY_GEMINI=your_gemini_api_key_here
HF_TOKEN=your_huggingface_token_optional
```

> `API_KEY_GEMINI` là bắt buộc nếu bạn dùng Gemini trong các agent. Một số module có thể cần `HF_TOKEN` tùy theo cách tích hợp mô hình local.

## Chạy ứng dụng

### Khởi động backend

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Sau khi chạy, truy cập:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/learn-image
- http://127.0.0.1:8000/chat-bot
- http://127.0.0.1:8000/ipa

## Quy trình hoạt động của hệ thống

1. Người dùng upload ảnh hoặc chọn chế độ học.
2. `Vision Agent` phân tích hình ảnh bằng YOLO và trả về danh sách nhãn đối tượng.
3. `Teacher Agent` xử lý danh sách nhãn và tạo bài học, ví dụ, IPA, quiz.
4. `Voice Agent` nhận file âm thanh để đánh giá phát âm theo từ mục tiêu.
5. Frontend hiển thị kết quả lên dashboard hoặc giao diện học tương ứng.

## API chính

### Chatbot

- `POST /api/v1/chat`
- `POST /api/v1/chat-bot`
- `POST /api/v1/chat/stream`

### Learning

- `POST /api/v1/analyze`
  - Upload ảnh để phát hiện đối tượng và sinh bài học
- `POST /api/v1/evaluate-pronunciation`
  - Upload file audio để đánh giá phát âm của người dùng

## Lưu ý

- Mô hình YOLO sẽ được tự động tải về thư mục `backend/resources/models/` nếu chưa có.
- Dự án đang triển khai dạng local app, chưa có hệ thống auth, database hoặc deployment production hoàn chỉnh.
- Một số tính năng AI có thể phụ thuộc vào khả năng kết nối mạng và API key hợp lệ.

## Gợi ý phát triển tiếp theo

- Thêm xác thực người dùng và lưu tiến độ học tập
- Kết nối database để lưu lịch sử bài học
- Cải thiện pipeline đánh giá phát âm với audio preprocessing rõ ràng hơn
- Tách service AI thành worker hoặc background queue cho scalability
- Thêm các module quiz, luyện từ theo chủ đề, và dashboard thống kê tiến độ

## License

Dự án này đang được quản lý theo quy định nội bộ của repository hiện tại. Nếu cần, bạn có thể cập nhật phần license phù hợp với mục đích triển khai của nhóm/đơn vị.
