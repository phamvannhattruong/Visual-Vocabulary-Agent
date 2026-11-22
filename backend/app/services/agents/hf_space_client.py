"""Hugging Face Space Gradio Client integration for conversational tutoring."""
import concurrent.futures
import os
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from gradio_client import Client
from backend.app.core.settings import HF_CHAT_SPACE_ID, HF_CHAT_TIMEOUT, HF_TOKEN

logger = logging.getLogger("backend.app.services.agents.hf_space")

# Default Hugging Face Space configuration
DEFAULT_SPACE_ID = HF_CHAT_SPACE_ID
DEFAULT_SYSTEM_PROMPT = (
    "You are an English-learning tutor. Answer questions about English "
    "vocabulary, grammar, translation, and pronunciation clearly and politely."
)
DEFAULT_TIMEOUT_SECONDS = HF_CHAT_TIMEOUT

_cached_client: Optional[Client] = None
_cached_space_id: Optional[str] = None


def get_hf_token() -> Optional[str]:
    """Retrieve clean Hugging Face API token from environment variables."""
    token = HF_TOKEN or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if token and not token.strip().startswith("your_"):
        return token.strip()
    return None


def get_hf_client(
    space_id: str = DEFAULT_SPACE_ID,
    force_reload: bool = False,
) -> Client:
    """
    Initialize or retrieve cached Gradio Client connected to Hugging Face Space.

    Args:
        space_id: The Hugging Face Space identifier (e.g., 'DeeplearningVN/chatbot-english').
        force_reload: Force recreation of client instance.

    Returns:
        Client: An active Gradio Client connected to the target space.
    """
    global _cached_client, _cached_space_id

    if _cached_client is not None and _cached_space_id == space_id and not force_reload:
        return _cached_client

    token = get_hf_token()
    logger.info(f"Connecting to Hugging Face Space: {space_id} (Authenticated: {bool(token)})")

    try:
        # Client accepts token parameter for private/authenticated spaces
        client = Client(space_id, token=token)
        _cached_client = client
        _cached_space_id = space_id
        return client
    except Exception as exc:
        error_msg = str(exc)
        if "RUNTIME_ERROR" in error_msg:
            logger.error(
                f"Hugging Face Space '{space_id}' is currently in RUNTIME_ERROR state on Hugging Face. "
                f"Please check the Space logs at https://huggingface.co/spaces/{space_id}"
            )
        elif "PAUSED" in error_msg or "SLEEPING" in error_msg:
            logger.warning(f"Hugging Face Space '{space_id}' is paused/sleeping and needs to be woken up.")
        raise RuntimeError(f"Failed to connect to Hugging Face Space '{space_id}': {exc}") from exc


def normalize_history(
    history: Optional[Union[List[Dict[str, str]], List[List[str]], List[Tuple[str, str]]]] = None
) -> List[Dict[str, str]]:
    """
    Normalize diverse chat history formats into standard List[Dict[str, str]] messages format.
    
    Supports:
        - List of dicts: [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]
        - List of pairs: [['User msg 1', 'Bot reply 1'], ['User msg 2', 'Bot reply 2']]
    """
    if not history:
        return []

    normalized: List[Dict[str, str]] = []
    for item in history:
        if isinstance(item, dict):
            role = item.get("role", "user")
            content = item.get("content", "")
            if role in ("user", "assistant") and content:
                normalized.append({"role": role, "content": str(content)})
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            user_msg, bot_msg = item
            if user_msg:
                normalized.append({"role": "user", "content": str(user_msg)})
            if bot_msg:
                normalized.append({"role": "assistant", "content": str(bot_msg)})
    return normalized


def extract_reply_text(result: Any) -> str:
    """
    Extract clean string response from various Gradio return formats.

    Args:
        result: Raw return object from gradio_client predict().

    Returns:
        str: Clean string reply text.
    """
    if result is None:
        return ""

    if isinstance(result, str):
        return result.strip()

    # If result is a list/tuple of chat messages
    if isinstance(result, (list, tuple)) and len(result) > 0:
        last_item = result[-1]
        # Pair format: [user, bot]
        if isinstance(last_item, (list, tuple)) and len(last_item) >= 2:
            return str(last_item[1]).strip()
        # Message dict format: {"role": "assistant", "content": "..."}
        if isinstance(last_item, dict):
            return str(last_item.get("content", last_item.get("text", ""))).strip()
        return str(last_item).strip()

    # If result is a dictionary
    if isinstance(result, dict):
        for key in ("response", "reply", "content", "text", "message", "output"):
            if key in result:
                return str(result[key]).strip()
        return str(result)

    return str(result).strip()


def call_hf_chatbot(
    message: str,
    history: Optional[Union[List[Dict[str, str]], List[List[str]]]] = None,
    system_message: str = DEFAULT_SYSTEM_PROMPT,
    max_tokens: int = 128,
    temperature: float = 0.7,
    top_p: float = 0.9,
    space_id: str = DEFAULT_SPACE_ID,
    client: Optional[Client] = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """
    Send a user question and chat history to the Hugging Face Space chatbot and return its response.
    Enforces a strict timeout to prevent blocking the application when Space is sleeping.
    """
    if not message or not message.strip():
        return ""

    active_client = client or get_hf_client(space_id=space_id)
    clean_history = normalize_history(history)

    def _execute_predict() -> str:
        # Strategy 1: Attempt standard Gradio ChatInterface /respond endpoint
        try:
            raw_result = active_client.predict(
                message=message.strip(),
                system_message=system_message,
                max_tokens=float(max_tokens),
                temperature=float(temperature),
                top_p=float(top_p),
                api_name="/respond",
            )
            return extract_reply_text(raw_result)
        except Exception as err_respond:
            logger.debug(f"/respond endpoint call failed ({err_respond}), attempting /chat...")

        # Strategy 2: Attempt /chat endpoint
        try:
            raw_result = active_client.predict(
                message=message.strip(),
                system_message=system_message,
                max_tokens=float(max_tokens),
                temperature=float(temperature),
                top_p=float(top_p),
                api_name="/chat",
            )
            return extract_reply_text(raw_result)
        except Exception as err_chat:
            logger.debug(f"/chat endpoint call failed ({err_chat}), attempting positional call...")

        # Strategy 3: Attempt positional call with history parameter
        raw_result = active_client.predict(
            message.strip(),
            clean_history,
            system_message,
            float(max_tokens),
            float(temperature),
            float(top_p),
        )
        return extract_reply_text(raw_result)

    # Execute prediction with timeout safeguard
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_execute_predict)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as timeout_err:
            logger.warning(
                f"Hugging Face Space '{space_id}' timed out after {timeout}s (likely cold sleeping or queue congested)."
            )
            raise TimeoutError(
                f"Hugging Face Space '{space_id}' request timed out after {timeout} seconds."
            ) from timeout_err
        except Exception as err:
            raise RuntimeError(
                f"Error invoking chatbot on Hugging Face Space '{space_id}': {err}"
            ) from err


class HFSpaceChatAgent:
    """
    Object-oriented Chat Agent wrapper providing interface compatibility
    with existing system agents (e.g. backend/app/services/agents/chat.py).
    """

    def __init__(
        self,
        space_id: str = DEFAULT_SPACE_ID,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_tokens: int = 128,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ):
        self.space_id = space_id
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_hf_client(space_id=self.space_id)
        return self._client

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response given a list of conversation messages.
        Extracts latest user question and previous messages as history.
        """
        if not messages:
            return ""

        # Extract latest user message
        last_user_message = ""
        history: List[Dict[str, str]] = []
        for msg in messages:
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
            if msg != messages[-1]:
                history.append(msg)

        return call_hf_chatbot(
            message=last_user_message,
            history=history,
            system_message=self.system_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            space_id=self.space_id,
            client=self.client,
        )


if __name__ == "__main__":
    # Example manual test script
    logging.basicConfig(level=logging.INFO)
    print("Testing Hugging Face Space Chatbot Integration...")

    sample_question = "How do I pronounce the word 'schedule' in British and American English?"
    sample_history = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there! How can I help you learn English today?"},
    ]

    try:
        reply = call_hf_chatbot(
            message=sample_question,
            history=sample_history,
            system_message=DEFAULT_SYSTEM_PROMPT,
        )
        print("\n[Chatbot Reply]:\n", reply)
    except Exception as e:
        print("\n[Error Calling Space]:\n", e)
