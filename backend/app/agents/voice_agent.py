import io
import os
from gtts import gTTS
from langchain_core.prompts import PromptTemplate

# Import Agent lớp cha từ base_agent đã chuẩn hóa
from backend.app.agents.base_agent import Agent 

class VoiceAgent(Agent):
    def __init__(self, default_language: str = 'en'):
        # Gọi hàm khởi tạo của lớp cha Agent để kế thừa cấu hình (Native Client & LangChain)
        super().__init__()
        self.default_language = default_language

    def convert_text_to_speech(self, text: str, language: str = 'en'):
        if not text:
            return None
        try:
            tts = gTTS(text=text, lang=language, slow=True)
            audio_stream = io.BytesIO()
            tts.write_to_fp(audio_stream)
            return audio_stream.getvalue()
        except Exception as e:
            print(f"Error in Voice Agent TTS: {e}")
            return None

    def create_vocabulary_audio(self, vocab_list: list):
        combined_text = ", ".join(vocab_list)
        return self.convert_text_to_speech(combined_text, language=self.default_language)

    def create_lesson_audio(self, lesson_md: str):
        combined_text = lesson_md.replace("#", "").replace("*", "").replace("-", "").strip()
        return self.convert_text_to_speech(combined_text, language=self.default_language)

    def check_speech(self, target_word: str, audio_bytes: bytes) -> str:
        """
        Sử dụng hàm generate_response từ lớp cha để đánh giá phát âm.
        """
        # 1. Cấu hình Prompt chi tiết
        prompt = f"""
        As an English Pronunciation Coach, listen to the user's audio and evaluate their pronunciation.
        Target word: "{target_word}"

        Instructions:
        1. Listen carefully to the audio provided.
        2. Compare it with the correct pronunciation of the target word.
        3. Return a JSON object with:
           - "score": (int 0-100)
           - "feedback": (string in Vietnamese, e.g., "Thiếu âm cuối 's'", "Phát âm sai nguyên âm 'a'")
           - "tip": (string in Vietnamese, how to fix it)
        """

        # 2. Đóng gói dữ liệu đầu vào (gồm prompt chữ và dữ liệu âm thanh)
        # Định dạng dict này sẽ tự động được base_agent.py parse thành types.Part.from_bytes hợp lệ
        contents = [
            prompt,
            {
                "mime_type": "audio/wav",
                "data": audio_bytes
            }
        ]

        # 3. Gọi hàm generate_response của lớp cha BaseAgent
        try:
            # Sửa từ generate_content thành generate_response theo đúng lớp cha
            # Thêm cấu hình sinh cấu trúc JSON sạch từ Gemini API
            response_text = self.generate_response(
                contents=contents,
                config={
                    "response_mime_type": "application/json"
                }
            )
            return response_text
        except Exception as e:
            print(f"Error in Voice Agent check_speech: {e}")
            return "{}"