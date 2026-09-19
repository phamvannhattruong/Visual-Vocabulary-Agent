import os
import re
from typing import List, Dict, Generator
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

DEFAULT_MAX_TOKENS = 256
STOP_SEQUENCES = ["<|eot_id|>", "<|end_of_text|>", "</s>"]
LOOP_MIN_WORDS = 16
LOOP_CONSECUTIVE_REPEATS = 8


def repetition_loop_start(text: str) -> int | None:
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
    ChatAgent tối ưu tốc độ nạp mô hình bằng định dạng GGUF qua llama-cpp
    Tự động tải & cache từ Hugging Face Hub.
    """

    def __init__(
        self,
        repo_id: str = "DeeplearningVN/Chatbot_English",
        filename: str = "meta-llama-3.1-8b.Q4_K_M.gguf",  # Đổi đúng tên file .gguf trên repo của bạn
        system_prompt: str = "Bạn là AI Tutor của hệ thống hỗ trợ học phát âm tiếng Anh chuẩn IPA.",
        n_ctx: int = 2048,
        n_gpu_layers: int = 0  # Đặt -1 nếu máy chạy có GPU CUDA, 0 nếu chỉ dùng CPU
    ):
        self.system_prompt = system_prompt
        
        print(f"-> [ChatAgent] Đang kiểm tra/tải GGUF model từ Hugging Face: {repo_id}/{filename}")
        
        # hf_hub_download sẽ tải về ~/.cache/huggingface/ (chỉ tải lần đầu, lần sau nạp ngay lập tức)
        self.model_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            token=os.getenv("HF_TOKEN")  # Đọc token từ .env nếu repo là Private
        )
        
        print(f"-> [ChatAgent] Nạp model từ cache: {self.model_path}")
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=False
        )
        print("-> [ChatAgent] Sẵn sàng hoạt động!")

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Build one chat template without accepting or duplicating system prompts."""
        return [
            {"role": "system", "content": self.system_prompt},
            *(message for message in messages if message.get("role") != "system"),
        ]

    def _create_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        repeat_penalty: float = 1.15,
        frequency_penalty: float = 0.3,
        stream: bool = False,
    ):
        return self.llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            top_k=40,
            repeat_penalty=repeat_penalty,
            presence_penalty=0.1,
            frequency_penalty=frequency_penalty,
            stop=STOP_SEQUENCES,
            stream=stream,
        )

    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.7,
    ) -> str:
        formatted_messages = self._prepare_messages(messages)
        response = self._create_completion(formatted_messages, max_tokens, temperature)
        content = response["choices"][0]["message"]["content"]
        truncated_content = truncate_repetition_loop(content)
        if truncated_content != content and truncated_content.strip():
            return truncated_content
        if truncated_content != content:
            # A loop at the start has no useful text to keep. Retry once with
            # stronger penalties before returning a fallback response.
            retry = self._create_completion(
                formatted_messages,
                max_tokens,
                min(temperature, 0.5),
                repeat_penalty=1.25,
                frequency_penalty=0.5,
            )
            retry_content = truncate_repetition_loop(
                retry["choices"][0]["message"]["content"]
            )
            return retry_content or "I’m sorry, please try your question again."
        return content

    def stream_response(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Dùng cho API Streaming kết nối giao diện Frontend"""
        formatted_messages = self._prepare_messages(messages)
        response_stream = self._create_completion(
            formatted_messages, max_new_tokens, temperature, stream=True
        )
        generated_text = ""
        for chunk in response_stream:
            delta = chunk["choices"][0].get("delta", {})
            if "content" in delta:
                content = delta["content"]
                generated_text += content
                if repetition_loop_start(generated_text) is not None:
                    break
                yield content


if __name__ == "__main__":
    # Test chạy trực tiếp agent
    agent = ChatAgent(
        repo_id="DeeplearningVN/Chatbot_English",
        filename="meta-llama-3.1-8b.Q4_K_M.gguf"
    )
    test_msg = [{"role": "user", "content": "Làm thế nào để phát âm âm /θ/?"}]
    print("\nAI Tutor Response:")
    print(agent.generate_response(test_msg))
