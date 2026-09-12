// static/js/chat.js

document.addEventListener("DOMContentLoaded", () => {
    // Khớp đúng ID theo HTML
    const chatInput = document.getElementById("user-input");
    const messageList = document.getElementById("message-list");
    const welcomeContainer = document.getElementById("welcome-container");
    const chatBody = document.getElementById("chat-body");
    const sendBtn = document.getElementById("send-btn");
    const newChatBtn = document.getElementById("new-chat-btn");

    let chatHistory = [];
    const API_ENDPOINT = "/api/v1/chat-bot";

    function escapeHtml(string) {
        return String(string)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Tự động cuộn xuống cuối khung chat
    function scrollToBottom() {
        if (chatBody) {
            chatBody.scrollTop = chatBody.scrollHeight;
        }
    }

    // Render bubble tin nhắn
    function appendMessage(sender, text) {
        if (!messageList) return null;

        // Ẩn màn hình chào mừng ngay khi có tin nhắn đầu tiên
        if (welcomeContainer && welcomeContainer.style.display !== "none") {
            welcomeContainer.style.display = "none";
        }

        const messageEl = document.createElement("div");
        messageEl.className = `message ${sender}-message`;
        messageEl.style.margin = "12px 0";
        messageEl.style.padding = "12px 18px";
        messageEl.style.borderRadius = "16px";
        messageEl.style.maxWidth = "80%";
        messageEl.style.lineHeight = "1.5";
        messageEl.style.wordBreak = "break-word";

        if (sender === "user") {
            messageEl.style.marginLeft = "auto";
            messageEl.style.backgroundColor = "#2563eb";
            messageEl.style.color = "#ffffff";
            messageEl.innerHTML = `<div>${escapeHtml(text)}</div>`;
        } else if (sender === "bot") {
            messageEl.style.marginRight = "auto";
            messageEl.style.backgroundColor = "#f3f4f6";
            messageEl.style.color = "#1f2937";
            messageEl.innerHTML = `<div><strong>AI Tutor:</strong> <span class="bot-text">${escapeHtml(text)}</span></div>`;
        } else {
            messageEl.style.margin = "8px auto";
            messageEl.style.fontSize = "0.85rem";
            messageEl.style.color = "#ef4444";
            messageEl.innerHTML = `<em>${escapeHtml(text)}</em>`;
        }

        messageList.appendChild(messageEl);
        scrollToBottom();
        return messageEl;
    }

    // Xử lý gửi tin nhắn
    async function handleSendMessage() {
        if (!chatInput) return;
        
        const message = chatInput.value.trim();
        if (!message) return;

        // 1. Hiển thị tin nhắn người dùng và xóa ô nhập
        appendMessage("user", message);
        chatInput.value = "";
        chatInput.style.height = "auto"; // Reset chiều cao textarea

        if (sendBtn) sendBtn.disabled = true;

        // 2. Tạo placeholder bot đang trả lời
        const loadingMessageEl = appendMessage("bot", "Đang suy nghĩ...");

        // 3. Chuẩn bị payload { messages: [...] }
        const currentMessages = [
            ...chatHistory,
            { role: "user", content: message }
        ];

        try {
            const response = await fetch(API_ENDPOINT, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ messages: currentMessages })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                const errDetail = errData.detail ? JSON.stringify(errData.detail) : response.statusText;
                throw new Error(`Lỗi (${response.status}): ${errDetail}`);
            }

            const data = await response.json();
            const botResponse = data.reply || "Không nhận được phản hồi từ mô hình.";

            // 4. Điền câu trả lời vào bong bóng chat
            if (loadingMessageEl) {
                const textSpan = loadingMessageEl.querySelector(".bot-text");
                if (textSpan) textSpan.textContent = botResponse;
            }

            // 5. Cập nhật lịch sử hội thoại
            chatHistory.push({ role: "user", content: message });
            chatHistory.push({ role: "assistant", content: botResponse });

        } catch (error) {
            console.error("Lỗi khi gửi:", error);
            if (loadingMessageEl) loadingMessageEl.remove();
            appendMessage("system", `Lỗi kết nối máy chủ: ${error.message}`);
        } finally {
            if (sendBtn) sendBtn.disabled = false;
            if (chatInput) chatInput.focus();
            scrollToBottom();
        }
    }

    // Lắng nghe phím Enter trong Textarea
    if (chatInput) {
        chatInput.addEventListener("keydown", (e) => {
            // Không ngắt khi gõ tiếng Việt (Telex / VNI)
            if (e.isComposing || e.keyCode === 229) return;

            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });

        // Tự co giãn chiều cao theo số dòng gõ
        chatInput.addEventListener("input", () => {
            chatInput.style.height = "auto";
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
        });
    }

    // Lắng nghe nút Gửi
    if (sendBtn) {
        sendBtn.addEventListener("click", (e) => {
            e.preventDefault();
            handleSendMessage();
        });
    }

    // Nút Tạo cuộc trò chuyện mới
    if (newChatBtn) {
        newChatBtn.addEventListener("click", () => {
            chatHistory = [];
            if (messageList) messageList.innerHTML = "";
            if (welcomeContainer) welcomeContainer.style.display = "block";
            if (chatInput) {
                chatInput.value = "";
                chatInput.focus();
            }
        });
    }
});