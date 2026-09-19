import os
from typing import List, Dict, Generator
from huggingface_hub import hf_hub_download
from llama_cpp import Llama


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
        formatted = []
        if not messages or messages[0].get("role") != "system":
            formatted.append({"role": "system", "content": self.system_prompt})
        formatted.extend(messages)
        return formatted

    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 512, 
        temperature: float = 0.7
    ) -> str:
        formatted_messages = self._prepare_messages(messages)
        response = self.llm.create_chat_completion(
            messages=formatted_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response["choices"][0]["message"]["content"]

    def stream_response(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """Dùng cho API Streaming kết nối giao diện Frontend"""
        formatted_messages = self._prepare_messages(messages)
        response_stream = self.llm.create_chat_completion(
            messages=formatted_messages,
            max_tokens=max_new_tokens,
            temperature=temperature,
            stream=True
        )
        for chunk in response_stream:
            delta = chunk["choices"][0].get("delta", {})
            if "content" in delta:
                yield delta["content"]


if __name__ == "__main__":
    # Test chạy trực tiếp agent
    agent = ChatAgent(
        repo_id="DeeplearningVN/Chatbot_English",
        filename="meta-llama-3.1-8b.Q4_K_M.gguf"
    )
    test_msg = [{"role": "user", "content": "Làm thế nào để phát âm âm /θ/?"}]
    print("\nAI Tutor Response:")
    print(agent.generate_response(test_msg))