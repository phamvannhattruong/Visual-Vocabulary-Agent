import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

# 1. Xác định đường dẫn tương đối tới file .env và thư mục dữ liệu
CURRENT_FILE = Path(__file__).resolve()
ROOT_DIR = CURRENT_FILE.parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_FILE = os.path.join(BASE_DIR, "..", "data", "raw", "ipa_data.json")
OUTPUT_JSONL = os.path.join(BASE_DIR, "..", "data", "train_dataset.jsonl")

# 2. Khởi tạo Groq Client
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError(f"[!] Không tìm thấy GROQ_API_KEY trong file .env tại: {ENV_PATH}")

client = Groq(api_key=groq_api_key)

# 3. Định nghĩa Schema Pydantic để kiểm tra dữ liệu trả về
class Message(BaseModel):
    role: str = Field(description="'system', 'user', hoặc 'assistant'")
    content: str

class Conversation(BaseModel):
    messages: list[Message]

class DatasetBatch(BaseModel):
    conversations: list[Conversation]

def chunk_text(text: str, max_chars=2500):
    """Chia nhỏ văn bản dài thành các đoạn vừa phải để LLM xử lý chi tiết."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0

    for p in paragraphs:
        if current_len + len(p) > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [p]
            current_len = len(p)
        else:
            current_chunk.append(p)
            current_len += len(p)
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    return chunks

def process_raw_to_chatml():
    if not os.path.exists(RAW_FILE):
        print(f"[!] Không tìm thấy file {RAW_FILE}. Hãy kiểm tra lại!")
        return

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Gom toàn bộ content nếu file raw là một List chứa nhiều bài viết
    if isinstance(raw_data, list):
        full_content = "\n\n".join([item.get("content", "") for item in raw_data if isinstance(item, dict)])
    elif isinstance(raw_data, dict):
        full_content = raw_data.get("content", "")
    else:
        full_content = ""

    chunks = chunk_text(full_content)
    print(f"[*] Đã chia nội dung thành {len(chunks)} phần nhỏ. Bắt đầu gọi Groq API...")

    system_instruction = (
        "Bạn là chuyên gia thiết kế dữ liệu huấn luyện Chatbot học tiếng Anh và IPA.\n"
        "Nhiệm vụ: Tạo ra các cặp hội thoại tự nhiên giữa Người học (user) và AI Tutor (assistant) dựa trên đoạn văn bản được cung cấp.\n\n"
        "Yêu cầu:\n"
        "1. Câu hỏi của user đa dạng: hỏi cách đọc âm, phân biệt 2 âm giống nhau, ví dụ từ vựng, mẹo đặt lưỡi/răng.\n"
        "2. Câu trả lời của assistant phải chuẩn xác, chi tiết, giải thích khẩu hình rõ ràng và thân thiện.\n"
        "3. System message cố định là: 'Bạn là AI Tutor của hệ thống Visual Vocabulary Agent, chuyên hướng dẫn phát âm chuẩn quốc tế và phân tích bảng phiên âm IPA.'\n"
        "4. BẮT BUỘC trả về đúng cấu trúc JSON sau:\n"
        "{\n"
        '  "conversations": [\n'
        "    {\n"
        '      "messages": [\n'
        '        {"role": "system", "content": "..."},\n'
        '        {"role": "user", "content": "..."},\n'
        '        {"role": "assistant", "content": "..."}\n'
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    all_conversations = []

    for idx, chunk in enumerate(chunks, 1):
        print(f" -> Đang xử lý đoạn {idx}/{len(chunks)} bằng Groq (Llama 3.3)...")
        prompt = f"Dựa vào nội dung kiến thức sau, hãy tạo từ 4 đến 6 cuộc hội thoại chất lượng:\n\n{chunk}"

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            response_json_str = chat_completion.choices[0].message.content
            
            # Parse và validate dữ liệu
            batch = DatasetBatch.model_validate_json(response_json_str)
            for conv in batch.conversations:
                all_conversations.append(conv.model_dump())

            print(f"    [+] Đoạn {idx}: Tạo thành công {len(batch.conversations)} hội thoại.")

        except Exception as e:
            print(f"    [!] Lỗi tại đoạn {idx}: {e}")

        # Tạm nghỉ 1s để giữ Rate Limit an toàn
        time.sleep(1)

    # 4. Ghi ra file JSONL chuẩn Fine-tune
    os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for conv in all_conversations:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")

    print(f"\n🎉 HOÀN THÀNH! Đã tạo được tổng cộng {len(all_conversations)} mẫu hội thoại.")
    print(f" -> File sẵn sàng Fine-tune: {OUTPUT_JSONL}")

if __name__ == "__main__":
    process_raw_to_chatml()