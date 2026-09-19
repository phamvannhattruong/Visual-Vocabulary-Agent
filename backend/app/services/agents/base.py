import os
from dotenv import load_dotenv
from google import genai
# Import thêm module types từ SDK mới để chuẩn hóa dữ liệu gửi đi
from google.genai import types 
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

class Agent:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.api_key = os.getenv("API_KEY_GEMINI")
        self.model_name = model
        self.hf_token = os.getenv("HF_TOKEN") 
        self.model_id = ""

        if not self.api_key:
            raise ValueError("Không tìm thấy API Key của Gemini.")
        
        self.gemini = ChatGoogleGenerativeAI(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.7
        )
        self.native_client = genai.Client(api_key=self.api_key)

    def generate_response(self, contents, **kwargs) -> str:
        """
        Hàm helper sinh nội dung hỗ trợ text và các dữ liệu multi-modal dạng bytes
        """
        processed_contents = []

        # 1. Nếu contents là một danh sách (Ví dụ: [Prompt_Text, Audio_Dict/Bytes])
        if isinstance(contents, list):
            for item in contents:
                # Nếu phần tử là một Dictionary chứa dữ liệu thô (ví dụ: file audio từ Frontend gửi lên)
                if isinstance(item, dict) and "data" in item and "mime_type" in item:
                    # Chuyển đổi một cách tường minh sang đối tượng Part chuẩn của Google GenAI SDK
                    part = types.Part.from_bytes(
                        data=item["data"],
                        mime_type=item["mime_type"]
                    )
                    processed_contents.append(part)
                else:
                    processed_contents.append(item)
        else:
            processed_contents = contents

        # 2. Thực hiện gọi API với dữ liệu đã được chuẩn hóa
        response = self.native_client.models.generate_content(
            model=self.model_name,
            contents=processed_contents,
            **kwargs
        )
        return response.text