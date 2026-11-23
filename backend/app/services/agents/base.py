import os
from google import genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.app.core.settings import API_KEY_GEMINI, DEFAULT_GEMINI_MODEL, HF_TOKEN


class Agent:
    def __init__(self, model: str = DEFAULT_GEMINI_MODEL):
        self.api_key = API_KEY_GEMINI or os.getenv("API_KEY_GEMINI")
        self.model_name = model
        self.hf_token = HF_TOKEN or os.getenv("HF_TOKEN")
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

        # 2. Thực hiện gọi API với danh sách candidate models tự động chuyển đổi khi lỗi quota (429) hoặc model không khả dụng (404)
        candidate_models = []
        preferred_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", self.model_name]
        for m in preferred_models:
            if m and m not in candidate_models:
                candidate_models.append(m)

        last_error = None
        for m in candidate_models:
            try:
                response = self.native_client.models.generate_content(
                    model=m,
                    contents=processed_contents,
                    **kwargs
                )
                if response and hasattr(response, "text") and response.text:
                    self.model_name = m  # stick to working model
                    return response.text
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        return ""

    def stream_response(self, contents, **kwargs):
        """
        Sinh nội dung dạng stream thời gian thực (Server-Sent Events / Generator)
        """
        processed_contents = []
        if isinstance(contents, list):
            for item in contents:
                if isinstance(item, dict) and "data" in item and "mime_type" in item:
                    part = types.Part.from_bytes(
                        data=item["data"],
                        mime_type=item["mime_type"]
                    )
                    processed_contents.append(part)
                else:
                    processed_contents.append(item)
        else:
            processed_contents = contents

        response_stream = self.native_client.models.generate_content_stream(
            model=self.model_name,
            contents=processed_contents,
            **kwargs
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
