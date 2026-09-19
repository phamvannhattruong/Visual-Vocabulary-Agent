// static/js/chat.js

document.addEventListener("DOMContentLoaded", () => {
    // Khớp đúng ID theo HTML
    const chatInput = document.getElementById("user-input");
    const messageList = document.getElementById("message-list");
    const welcomeContainer = document.getElementById("welcome-container");
    const chatBody = document.getElementById("chat-body");
    const sendBtn = document.getElementById("send-btn");
    const newChatBtn = document.getElementById("new-chat-btn");
    const toggleSidebarBtn = document.getElementById("toggle-sidebar-btn");
    const sidebar = document.getElementById("sidebar");
    const historyList = document.getElementById("history-list");

    let chatHistory = [];
    let currentSessionId = null;
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

    // Cập nhật trạng thái nút gửi dựa trên nội dung nhập
    function updateSendButtonState() {
        if (!chatInput || !sendBtn) return;
        if (chatInput.value.trim().length > 0) {
            sendBtn.classList.add("active");
        } else {
            sendBtn.classList.remove("active");
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

    // --- LOGIC QUẢN LÝ LỊCH SỬ CUỘC TRÒ CHUYỆN (LOCAL STORAGE) ---

    // Đọc tất cả các session từ localStorage
    function getSessions() {
        try {
            const data = localStorage.getItem("vva_chat_sessions");
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.error("Lỗi khi đọc lịch sử từ localStorage:", e);
            return [];
        }
    }

    // Lưu tất cả các session vào localStorage
    function saveSessions(sessions) {
        try {
            localStorage.setItem("vva_chat_sessions", JSON.stringify(sessions));
        } catch (e) {
            console.error("Lỗi khi ghi lịch sử vào localStorage:", e);
        }
    }

    // Tải nội dung của một session lên giao diện
    function loadSession(sessionId) {
        const sessions = getSessions();
        const session = sessions.find(s => s.id === sessionId);
        if (!session) return;

        if (currentSessionId !== sessionId) archiveCurrentSession();
        currentSessionId = sessionId;
        chatHistory = [...session.messages];

        // Xóa sạch khung chat cũ
        if (messageList) {
            messageList.innerHTML = "";
        }

        if (chatHistory.length > 0) {
            if (welcomeContainer) welcomeContainer.style.display = "none";
            // Hiển thị lại toàn bộ tin nhắn
            chatHistory.forEach(msg => {
                const sender = msg.role === "user" ? "user" : (msg.role === "assistant" ? "bot" : "system");
                appendMessage(sender, msg.content);
            });
        } else {
            if (welcomeContainer) welcomeContainer.style.display = "block";
        }

        renderSidebar();
        scrollToBottom();
    }

    // Lưu cuộc trò chuyện hiện tại
    function saveCurrentSession() {
        if (chatHistory.length === 0) return;

        const sessions = getSessions();

        if (!currentSessionId) {
            // Tạo mới một cuộc hội thoại hoàn toàn mới
            currentSessionId = "chat_" + Date.now();

            // Lấy tiêu đề từ tin nhắn đầu tiên của user
            const firstUserMsg = chatHistory.find(msg => msg.role === "user");
            let title = "Cuộc trò chuyện mới";
            if (firstUserMsg) {
                title = firstUserMsg.content.trim();
                if (title.length > 30) {
                    title = title.substring(0, 30) + "...";
                }
            }

            const newSession = {
                id: currentSessionId,
                title: title,
                messages: [...chatHistory],
                timestamp: Date.now()
            };
            sessions.push(newSession);
        } else {
            // Cập nhật cuộc hội thoại hiện có
            const sessionIndex = sessions.findIndex(s => s.id === currentSessionId);
            if (sessionIndex !== -1) {
                sessions[sessionIndex].messages = [...chatHistory];
                sessions[sessionIndex].timestamp = Date.now();
            } else {
                // Đề phòng trường hợp lỗi mất đồng bộ
                const firstUserMsg = chatHistory.find(msg => msg.role === "user");
                let title = "Cuộc trò chuyện mới";
                if (firstUserMsg) {
                    title = firstUserMsg.content.trim();
                    if (title.length > 30) {
                        title = title.substring(0, 30) + "...";
                    }
                }
                sessions.push({
                    id: currentSessionId,
                    title: title,
                    messages: [...chatHistory],
                    timestamp: Date.now()
                });
            }
        }

        saveSessions(sessions);
        renderSidebar();
    }

    // Xóa một cuộc trò chuyện
    function archiveCurrentSession() {
        if (chatHistory.length > 0) saveCurrentSession();
    }

    function createSessionId() {
        return `chat_${globalThis.crypto?.randomUUID?.() || Date.now()}`;
    }

    function startNewChat() {
        // Save the active conversation before replacing it with a new thread.
        archiveCurrentSession();
        chatHistory = [];
        currentSessionId = createSessionId();
        if (messageList) messageList.innerHTML = "";
        if (welcomeContainer) welcomeContainer.style.display = "block";
        if (chatInput) {
            chatInput.value = "";
            chatInput.style.height = "auto";
            chatInput.focus();
        }
        updateSendButtonState();
        renderSidebar();
    }

    function deleteSession(sessionId) {
        let sessions = getSessions();
        sessions = sessions.filter(s => s.id !== sessionId);
        saveSessions(sessions);

        // Nếu cuộc trò chuyện bị xóa đang là cuộc trò chuyện hiện tại, reset màn hình chat
        if (currentSessionId === sessionId) {
            currentSessionId = null;
            chatHistory = [];
            if (messageList) messageList.innerHTML = "";
            if (welcomeContainer) welcomeContainer.style.display = "block";
            if (chatInput) {
                chatInput.value = "";
                chatInput.style.height = "auto";
                chatInput.focus();
            }
            updateSendButtonState();
        }

        renderSidebar();
    }

    // Vẽ danh sách lịch sử lên sidebar
    function renderSidebar() {
        if (!historyList) return;
        historyList.innerHTML = "";

        const sessions = getSessions();
        // Sắp xếp cuộc trò chuyện mới nhất lên đầu
        sessions.sort((a, b) => b.timestamp - a.timestamp);

        if (sessions.length === 0) {
            historyList.innerHTML = `<li style="padding: 12px; font-size: 0.85rem; color: var(--text-muted); text-align: center; list-style: none;">Chưa có lịch sử</li>`;
            return;
        }

        sessions.forEach(session => {
            const li = document.createElement("li");
            li.className = "history-item";
            if (session.id === currentSessionId) {
                li.classList.add("active");
            }

            // Click vào li để tải cuộc trò chuyện
            li.addEventListener("click", (e) => {
                if (e.target.closest(".delete-chat-btn")) return;
                loadSession(session.id);
            });

            li.innerHTML = `
                <div class="history-text-wrapper">
                    <i class="fa-regular fa-message" style="flex-shrink: 0;"></i>
                    <span class="history-title-text">${escapeHtml(session.title)}</span>
                </div>
                <button class="delete-chat-btn" title="Xóa cuộc trò chuyện">
                    <i class="fa-regular fa-trash-can"></i>
                </button>
            `;

            // Lắng nghe nút xóa
            const deleteBtn = li.querySelector(".delete-chat-btn");
            if (deleteBtn) {
                deleteBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    if (confirm(`Bạn có chắc chắn muốn xóa cuộc trò chuyện "${session.title}" không?`)) {
                        deleteSession(session.id);
                    }
                });
            }

            historyList.appendChild(li);
        });
    }

    // --- KẾT THÚC LOGIC QUẢN LÝ LỊCH SỬ ---

    // Xử lý gửi tin nhắn
    async function handleSendMessage() {
        if (!chatInput) return;
        
        const message = chatInput.value.trim();
        if (!message) return;

        // 1. Hiển thị tin nhắn người dùng và xóa ô nhập
        appendMessage("user", message);
        chatInput.value = "";
        chatInput.style.height = "auto"; // Reset chiều cao textarea
        updateSendButtonState();

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

            // 6. Lưu cuộc hội thoại vào localStorage và cập nhật giao diện
            saveCurrentSession();

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
            updateSendButtonState();
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
            startNewChat();
        });
    }

    // Lắng nghe sự kiện thu gọn / mở rộng Sidebar
    if (toggleSidebarBtn && sidebar) {
        toggleSidebarBtn.addEventListener("click", () => {
            sidebar.classList.toggle("collapsed");
            
            // Đổi icon của toggle button tùy thuộc vào sidebar có thu gọn hay không
            const icon = toggleSidebarBtn.querySelector("i");
            if (sidebar.classList.contains("collapsed")) {
                toggleSidebarBtn.title = "Mở rộng";
                if (icon) {
                    icon.className = "fa-solid fa-chevron-right";
                }
            } else {
                toggleSidebarBtn.title = "Thu gọn";
                if (icon) {
                    icon.className = "fa-solid fa-bars";
                }
            }
        });
    }

    // --- KHỞI TẠO BAN ĐẦU ---
    // Vẽ lại sidebar khi trang tải lên lần đầu
    renderSidebar();

    startNewChat();
});
