"""
Conversational AI Tutor Agent using Hugging Face Space (Zero local model download).
Eliminates heavy 5GB GGUF downloads to save disk, memory, and launch time.
"""
import os
import re
import time
import logging
from typing import List, Dict, Generator, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("backend.app.services.agents.chat")

try:
    import spaces
except ImportError:
    class _SpacesMock:
        @staticmethod
        def GPU(func=None, **kwargs):
            if func is not None:
                return func
            return lambda fn: fn
    spaces = _SpacesMock()

DEFAULT_MAX_TOKENS = 128
DEFAULT_SPACE_ID = os.getenv("HF_CHAT_SPACE_ID", "DeeplearningVN/VVA")
DEFAULT_SYSTEM_PROMPT = (
    "You are an English-learning tutor. Answer only questions about English "
    "vocabulary, grammar, translation, or pronunciation. Politely redirect "
    "unrelated questions in Vietnamese."
)

LOOP_MIN_WORDS = 16
LOOP_CONSECUTIVE_REPEATS = 8


def repetition_loop_start(text: str) -> Optional[int]:
    """Locate a sustained repeated-word loop, ignoring short normal replies."""
    words = list(re.finditer(r"\b\w+\b", text, re.UNICODE))
    if len(words) < LOOP_MIN_WORDS:
        return None

    repeated_word = ""
    repeats = 0
    run_start = 0
    for match in words:
        word = match.group().casefold()
        if word == repeated_word:
            repeats += 1
        else:
            repeated_word = word
            repeats = 1
            run_start = match.start()

        if repeats >= LOOP_CONSECUTIVE_REPEATS:
            return run_start
    return None


def truncate_repetition_loop(text: str) -> str:
    """Keep the useful portion of a reply and remove a detected token loop."""
    loop_start = repetition_loop_start(text)
    return text[:loop_start].rstrip() if loop_start is not None else text


class ChatAgent:
    """
    ChatAgent tích hợp trực tiếp với Hugging Face Space (DeeplearningVN/chatbot-english).
    Hoàn toàn KHÔNG tải file model GGUF nặng (~5GB) về máy cục bộ.
    Tiết kiệm 100% dung lượng ổ cứng, RAM và hỗ trợ triển khai tức thì lên Hugging Face Space.
    """

    def __init__(
        self,
        space_id: str = DEFAULT_SPACE_ID,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        repo_id: Optional[str] = None,       # Giữ tương thích ngược
        filename: Optional[str] = None,      # Giữ tương thích ngược
        n_ctx: Optional[int] = None,         # Giữ tương thích ngược
        n_gpu_layers: Optional[int] = None,  # Giữ tương thích ngược
    ):
        self.space_id = space_id or DEFAULT_SPACE_ID
        self.system_prompt = system_prompt
        logger.info(
            f"-> [ChatAgent] Khởi tạo ChatAgent kết nối Hugging Face Space: {self.space_id} "
            f"(Zero-download, không tải model cục bộ)."
        )

    def _extract_user_message_and_history(
        self, messages: List[Dict[str, str]]
    ) -> tuple[str, List[Dict[str, str]]]:
        """Tách câu hỏi gần nhất của user và danh sách lịch sử hội thoại trước đó."""
        user_message = ""
        history: List[Dict[str, str]] = []

        for msg in reversed(messages):
            if msg.get("role") == "user" and not user_message:
                user_message = msg.get("content", "")
                continue

        for msg in messages:
            if msg.get("role") != "system":
                # Không đưa câu hỏi cuối cùng của user vào history
                if msg.get("role") == "user" and msg.get("content") == user_message:
                    continue
                history.append(msg)

        return user_message, history

    def _call_hf_space(
        self,
        message: str,
        history: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Thực hiện gọi API của Hugging Face Space."""
        from backend.app.services.agents.hf_space_client import call_hf_chatbot

        return call_hf_chatbot(
            message=message,
            history=history,
            system_message=self.system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            space_id=self.space_id,
        )

    def _call_fallback_agent(self, messages: List[Dict[str, str]]) -> str:
        """
        Dự phòng: Nếu HF Space đang sleep hoặc lỗi runtime,
        tự động chuyển tiếp sang Gemini AI Agent có sẵn trong dự án.
        """
        try:
            from backend.app.services.agents.base import Agent

            gemini_agent = Agent()
            # Ghép prompt hội thoại
            dialogue = [f"System instruction: {self.system_prompt}"]
            for msg in messages:
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                dialogue.append(f"{role}: {content}")
            prompt = "\n\n".join(dialogue)
            return gemini_agent.generate_response(prompt)
        except Exception as fallback_err:
            logger.warning(f"Fallback Gemini call failed: {fallback_err}")
            return (
                "Hiện tại dịch vụ Chatbot trên Hugging Face Space đang bảo trì. "
                "Vui lòng kiểm tra trạng thái Space hoặc cấu hình API_KEY_GEMINI trong file .env."
            )

    @spaces.GPU
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.7,
    ) -> str:
        """
        Sinh câu trả lời cho danh sách tin nhắn hội thoại.
        Thực hiện qua Hugging Face Space API, tự động fallback nếu Space không khả dụng.
        """
        user_message, history = self._extract_user_message_and_history(messages)
        if not user_message:
            return "Tôi có thể giúp gì cho bạn về học tiếng Anh hôm nay?"

        # 1. Thử gọi Hugging Face Space
        try:
            reply = self._call_hf_space(
                message=user_message,
                history=history,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            cleaned_reply = truncate_repetition_loop(reply)
            if cleaned_reply and cleaned_reply.strip():
                return cleaned_reply
        except Exception as hf_err:
            logger.warning(
                f"[ChatAgent] Không thể kết nối tới Hugging Face Space '{self.space_id}' ({hf_err}). "
                f"Đang kích hoạt cơ chế fallback an toàn..."
            )

        # 2. Fallback sang Gemini Agent
        fallback_reply = self._call_fallback_agent(messages)
        return truncate_repetition_loop(fallback_reply)

    def stream_response(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """
        Stream câu trả lời phục vụ Server-Sent Events (SSE) cho frontend.
        """
        full_response = self.generate_response(
            messages=messages,
            max_tokens=max_new_tokens,
            temperature=temperature,
        )

        # Mô phỏng stream mượt mà theo từng cụm từ/từ cho frontend
        words = re.split(r"(\s+)", full_response)
        buffer = ""
        for word in words:
            if not word:
                continue
            buffer += word
            if repetition_loop_start(buffer) is not None:
                break
            yield word
            time.sleep(0.015)  # Hiệu ứng gõ mượt mà nhẹ nhàng


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = ChatAgent(space_id="DeeplearningVN/chatbot-english")
    test_msg = [{"role": "user", "content": "Làm thế nào để phát âm âm /θ/?"}]
    print("\n[AI Tutor Response]:")
    print(agent.generate_response(test_msg))
