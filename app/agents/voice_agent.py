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

    def check_speech(self, target_word, user_said):
        prompts = f"""
        As an English Pronunciation Coach, evaluate the user's attempt.
        Target word: "{target_word}"
        User actually said: "{user_said}"
        
        Please provide:
        1. Accuracy Score (0-100%).
        2. Brief feedback in Vietnamese explaining why it's wrong (e.g., missed ending sounds, wrong vowel).
        3. A tip to improve.
        
        Format the response as JSON:
        {{
            "score": 85,
            "feedback": "Bạn phát âm khá tốt nhưng bị thiếu âm 's' ở cuối.",
            "tip": "Hãy chú ý xì nhẹ ở cuối lưỡi khi kết thúc từ này."
        }}
        """
        prompt = PromptTemplate(input_variables=["target", "user_said"], template=prompts)
        chain = prompt | self.gemini

        return chain.invoke({"target": target_word, "user_said": user_said}).content


