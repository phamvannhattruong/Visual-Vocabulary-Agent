"""
Conversational AI Tutor Agent using Hugging Face Space (Zero local model download).
Eliminates heavy 5GB GGUF downloads to save disk, memory, and launch time.
"""
from collections import OrderedDict
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

# Quick FAQ / Greeting dictionary for instantaneous response (0ms)
QUICK_FAQ_RESPONSES = {
    "hi": "Xin chào! Tôi là Gia sư AI (AI English Tutor). Bạn muốn tìm hiểu về từ vựng, bảng phiên âm IPA hay luyện tập ngữ pháp tiếng Anh hôm nay?",
    "hello": "Hello! Rất vui được đồng hành cùng bạn trên hành trình học tiếng Anh. Bạn có câu hỏi nào về từ vựng hay phát âm cần giải đáp không?",
    "xin chào": "Xin chào bạn! Tôi là Gia sư AI hỗ trợ học tiếng Anh. Hãy đặt câu hỏi về từ vựng, ngữ pháp hoặc phát âm để chúng ta cùng luyện tập nhé!",
    "chào bạn": "Chào bạn! Hôm nay bạn muốn luyện phát âm âm nào hay muốn học từ vựng theo chủ đề gì?",
    "bạn là ai": "Tôi là Gia sư AI của Visual Vocabulary Agent, được xây dựng để hỗ trợ bạn học từ vựng qua hình ảnh, sửa phát âm IPA và luyện giao tiếp tiếng Anh.",
    "who are you": "I am your AI English Tutor from Visual Vocabulary Agent, here to help you master pronunciation, vocabulary, and grammar effectively!"
}

# In-memory LRU cache for identical queries
_QUERY_CACHE: OrderedDict[str, str] = OrderedDict()
_CACHE_MAX_SIZE = 128


def get_cached_response(prompt_text: str) -> Optional[str]:
    """Retrieve quick answer from FAQ or LRU cache."""
    clean_key = prompt_text.strip().lower().rstrip("?.! ")
    if clean_key in QUICK_FAQ_RESPONSES:
        return QUICK_FAQ_RESPONSES[clean_key]
    if clean_key in _QUERY_CACHE:
        _QUERY_CACHE.move_to_end(clean_key)
        return _QUERY_CACHE[clean_key]
    return None


def store_cached_response(prompt_text: str, response_text: str):
    """Store generated response into LRU cache."""
    clean_key = prompt_text.strip().lower().rstrip("?.! ")
    if not clean_key or len(clean_key) > 120 or not response_text:
        return
    _QUERY_CACHE[clean_key] = response_text
    if len(_QUERY_CACHE) > _CACHE_MAX_SIZE:
        _QUERY_CACHE.popitem(last=False)


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

    def _stream_fallback_agent(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Stream phản hồi thời gian thực trực tiếp từ Gemini Native Client."""
        try:
            from backend.app.services.agents.base import Agent

            gemini_agent = Agent()
            dialogue = [f"System instruction: {self.system_prompt}"]
            for msg in messages:
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                dialogue.append(f"{role}: {content}")
            prompt = "\n\n".join(dialogue)

            collected = []
            for chunk in gemini_agent.stream_response(prompt):
                if chunk:
                    collected.append(chunk)
                    yield chunk
            
            # Store in cache when finished
            if collected:
                user_msg, _ = self._extract_user_message_and_history(messages)
                store_cached_response(user_msg, "".join(collected))
        except Exception as fallback_err:
            logger.warning(f"Fallback Gemini streaming failed: {fallback_err}")
            yield "Hiện tại dịch vụ Chatbot đang bận. Vui lòng kiểm tra lại kết nối hoặc API_KEY_GEMINI."

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
        Tích hợp Cache tức thì cho các câu hỏi phổ biến.
        """
        user_message, history = self._extract_user_message_and_history(messages)
        if not user_message:
            return "Tôi có thể giúp gì cho bạn về học tiếng Anh hôm nay?"

        # 0. Kiểm tra Quick FAQ / LRU cache (0ms latency)
        cached_ans = get_cached_response(user_message)
        if cached_ans:
            return cached_ans

        preferred_provider = os.getenv("CHAT_PROVIDER", "hf_space").lower()

        # Nếu cấu hình ưu tiên Gemini, gọi trực tiếp Gemini không cần chờ HF Space
        if preferred_provider == "gemini":
            reply = self._call_fallback_agent(messages)
            cleaned = truncate_repetition_loop(reply)
            store_cached_response(user_message, cleaned)
            return cleaned

        # 1. Thử gọi Hugging Face Space với timeout bảo vệ
        try:
            reply = self._call_hf_space(
                message=user_message,
                history=history,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            cleaned_reply = truncate_repetition_loop(reply)
            if cleaned_reply and cleaned_reply.strip():
                store_cached_response(user_message, cleaned_reply)
                return cleaned_reply
        except Exception as hf_err:
            logger.warning(
                f"[ChatAgent] Không thể kết nối tới Hugging Face Space '{self.space_id}' ({hf_err}). "
                f"Đang kích hoạt cơ chế fallback an toàn sang Gemini..."
            )

        # 2. Fallback sang Gemini Agent
        fallback_reply = self._call_fallback_agent(messages)
        cleaned_fallback = truncate_repetition_loop(fallback_reply)
        store_cached_response(user_message, cleaned_fallback)
        return cleaned_fallback

    def stream_response(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """
        Stream câu trả lời phục vụ Server-Sent Events (SSE) cho frontend.
        Hỗ trợ True Streaming qua Gemini và Quick-cache streaming tức thì.
        """
        user_message, history = self._extract_user_message_and_history(messages)
        if not user_message:
            yield "Tôi có thể giúp gì cho bạn về học tiếng Anh hôm nay?"
            return

        # 0. Trả lời tức thì nếu có trong Cache
        cached_ans = get_cached_response(user_message)
        if cached_ans:
            words = re.split(r"(\s+)", cached_ans)
            for w in words:
                if w:
                    yield w
                    time.sleep(0.005)
            return

        preferred_provider = os.getenv("CHAT_PROVIDER", "hf_space").lower()

        # Nếu ưu tiên Gemini, thực hiện True Streaming trực tiếp
        if preferred_provider == "gemini":
            for chunk in self._stream_fallback_agent(messages):
                yield chunk
            return

        # Thử gọi Space, nếu lỗi hoặc timeout lập tức chuyển sang True Streaming Gemini
        try:
            full_response = self._call_hf_space(
                message=user_message,
                history=history,
                max_tokens=max_new_tokens,
                temperature=temperature,
            )
            cleaned_response = truncate_repetition_loop(full_response)
            if cleaned_response and cleaned_response.strip():
                store_cached_response(user_message, cleaned_response)
                words = re.split(r"(\s+)", cleaned_response)
                for word in words:
                    if word:
                        yield word
                        time.sleep(0.008)
                return
        except Exception as hf_err:
            logger.warning(
                f"[ChatAgent.stream] HF Space không khả dụng ({hf_err}), chuyển sang Gemini stream trực tiếp..."
            )

        # Fallback sang Gemini Real-time Streaming
        for chunk in self._stream_fallback_agent(messages):
            yield chunk


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = ChatAgent(space_id="DeeplearningVN/chatbot-english")
    test_msg = [{"role": "user", "content": "Làm thế nào để phát âm âm /θ/?"}]
    print("\n[AI Tutor Response]:")
    print(agent.generate_response(test_msg))
