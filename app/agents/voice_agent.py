import io
from app.agents.base_agent import Agent
from gtts import gTTS
from langchain_core.prompts import PromptTemplate
import os

class VoiceAgent(Agent):
    def __init__(self, default_language: str = 'en'):
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
            print (f"Error in Voice Agent {e}")

    def create_vocabulary_audio(self, vocab_list: list):
        combined_text = ", ".join(vocab_list)
        return self.convert_text_to_speech(combined_text, language=self.default_language)

    def create_lesson_audio(self, lesson_md: str):
        combined_text = lesson_md.replace("#", "").replace("*", "").replace("-", "").strip()
        return self.convert_text_to_speech(combined_text, language=self.default_language)

    def check_speech(self, target_word, audio_bytes):
        # Cấu hình Prompt hướng dẫn chi tiết
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

        # Gửi cả Text và Audio cho Gemini 2.5 Flash
        response = self.native_model.generate_content([
            prompt,
            {
                "mime_type": "audio/wav",
                "data": audio_bytes
            }
        ])

        return response.text


