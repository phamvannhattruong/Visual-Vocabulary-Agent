import os
import spaces
import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ID = "DeeplearningVN/Chatbot_English"
GGUF_FILE = "meta-llama-3.1-8b.Q4_K_M.gguf"
TOKENIZER_ID = "unsloth/meta-llama-3.1-8b-instruct"

token = os.getenv("HF_TOKEN")

# Dummy function to satisfy ZeroGPU supervisor requirements
@spaces.GPU
def _satisfy_zero_gpu():
    return True


print(f"[STARTUP] Initializing tokenizer: {TOKENIZER_ID}...", flush=True)
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_ID, token=token)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print(f"[STARTUP] Pre-loading fine-tuned GGUF model: {REPO_ID}/{GGUF_FILE} on CPU...", flush=True)
model = AutoModelForCausalLM.from_pretrained(
    REPO_ID,
    gguf_file=GGUF_FILE,
    dtype=torch.float32,
    token=token,
)
print("[STARTUP] Fine-tuned model is fully loaded and ready in RAM!", flush=True)


def extract_text(content) -> str:
    """Safely extract plain text from diverse Gradio message formats."""
    if not content:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(str(part.get("text", part.get("content", ""))))
            else:
                parts.append(str(part))
        return " ".join(parts).strip()
    if isinstance(content, dict):
        return str(content.get("text", content.get("content", content.get("value", "")))).strip()
    return str(content).strip()


def respond(
    message,
    history: list,
    system_message: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
) -> str:
    try:
        messages = [{"role": "system", "content": system_message}]

        if history:
            for item in history:
                if isinstance(item, dict):
                    role = item.get("role", "user")
                    clean_c = extract_text(item.get("content", ""))
                    if clean_c:
                        messages.append({"role": role, "content": clean_c})
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    u, b = item
                    clean_u = extract_text(u)
                    clean_b = extract_text(b)
                    if clean_u:
                        messages.append({"role": "user", "content": clean_u})
                    if clean_b:
                        messages.append({"role": "assistant", "content": clean_b})

        clean_message = extract_text(message)
        if not clean_message:
            return "Xin vui lòng nhập nội dung câu hỏi."

        messages.append({"role": "user", "content": clean_message})

        enc = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"]
        attention_mask = enc.get("attention_mask")

        with torch.no_grad():
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=min(int(max_tokens), 128),
                do_sample=True if float(temperature) > 0.05 else False,
                temperature=max(float(temperature), 0.01),
                top_p=float(top_p),
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        generated_tokens = outputs[0][len(input_ids[0]):]
        reply = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        return reply.strip()

    except Exception as e:
        print(f"[ERROR in respond]: {e}", flush=True)
        return f"⚠️ Lỗi xử lý: {str(e)}"


chatbot = gr.ChatInterface(
    respond,
    additional_inputs=[
        gr.Textbox(
            value="You are an English-learning tutor. Answer only questions about English vocabulary, grammar, translation, or pronunciation. Politely redirect unrelated questions in Vietnamese.",
            label="System message",
            lines=2
        ),
        gr.Slider(minimum=32, maximum=256, value=96, step=16, label="Max new tokens"),
        gr.Slider(minimum=0.1, maximum=1.5, value=0.7, step=0.1, label="Temperature"),
        gr.Slider(minimum=0.1, maximum=1.0, value=0.9, step=0.05, label="Top-p (nucleus sampling)"),
    ],
    title="💬 English AI Tutor (DeeplearningVN Fine-tuned GGUF)",
    description="Chatbot luyện phát âm và học tiếng Anh sử dụng mô hình Fine-tuned của DeeplearningVN (meta-llama-3.1-8b.Q4_K_M.gguf).",
)

if __name__ == "__main__":
    chatbot.launch()
