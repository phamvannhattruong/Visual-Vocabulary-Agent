-- ====================================================================
-- Script tạo Database & Bảng lưu trữ Log cho Visual Vocabulary Agent
-- Hệ quản trị CSDL: Microsoft SQL Server
-- ====================================================================

-- 1. Tạo Database nếu chưa tồn tại
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'english_learning_app')
BEGIN
    CREATE DATABASE english_learning_app;
END
GO

USE english_learning_app;
GO

-- 2. Bảng User (Người dùng)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'User')
BEGIN
    CREATE TABLE [User] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) NULL,
        create_at DATETIME DEFAULT GETDATE()
    );
END
GO

-- 3. Bảng chat_logs: Lưu lịch sử trò chuyện với AI Tutor
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'chat_logs')
BEGIN
    CREATE TABLE chat_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        session_id NVARCHAR(100) NULL,
        user_message NVARCHAR(MAX) NOT NULL,
        bot_response NVARCHAR(MAX) NULL,
        created_at DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_chat_logs_User FOREIGN KEY (user_id) REFERENCES [User](id) ON DELETE SET NULL
    );

    CREATE NONCLUSTERED INDEX IX_chat_logs_session_id ON chat_logs(session_id);
    CREATE NONCLUSTERED INDEX IX_chat_logs_created_at ON chat_logs(created_at);
END
GO

-- 4. Bảng image_learning_logs: Lưu kết quả nhận diện ảnh, bài học & câu hỏi trắc nghiệm
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'image_learning_logs')
BEGIN
    CREATE TABLE image_learning_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        file_name NVARCHAR(255) NULL,
        detected_labels NVARCHAR(MAX) NULL,    -- Danh sách nhãn đối tượng (JSON)
        annotated_img_url NVARCHAR(500) NULL,  -- Đường dẫn ảnh đã vẽ bbox
        lesson_context NVARCHAR(MAX) NULL,     -- Nội dung bài học sinh từ AI
        quiz_data NVARCHAR(MAX) NULL,          -- Dữ liệu quiz (JSON)
        created_at DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_image_logs_User FOREIGN KEY (user_id) REFERENCES [User](id) ON DELETE SET NULL
    );

    CREATE NONCLUSTERED INDEX IX_image_logs_created_at ON image_learning_logs(created_at);
END
GO

-- 5. Bảng pronunciation_logs: Lưu lịch sử và điểm số luyện phát âm
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'pronunciation_logs')
BEGIN
    CREATE TABLE pronunciation_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        target_word NVARCHAR(100) NOT NULL,
        score INT NULL,                        -- Điểm số từ 0 - 100
        feedback NVARCHAR(MAX) NULL,          -- Đánh giá chi tiết
        tip NVARCHAR(MAX) NULL,               -- Gợi ý cải thiện
        created_at DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_pronunciation_logs_User FOREIGN KEY (user_id) REFERENCES [User](id) ON DELETE SET NULL
    );

    CREATE NONCLUSTERED INDEX IX_pronunciation_logs_target_word ON pronunciation_logs(target_word);
    CREATE NONCLUSTERED INDEX IX_pronunciation_logs_created_at ON pronunciation_logs(created_at);
END
GO

-- 6. Bảng activity_logs: Nhật ký hoạt động chung của ứng dụng
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'activity_logs')
BEGIN
    CREATE TABLE activity_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        action NVARCHAR(100) NOT NULL,         -- Ví dụ: CHAT, ANALYZE_IMAGE, EVALUATE_PRONUNCIATION
        status NVARCHAR(50) NOT NULL,         -- SUCCESS hoặc ERROR
        details NVARCHAR(MAX) NULL,
        ip_address VARCHAR(50) NULL,
        created_at DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_activity_logs_User FOREIGN KEY (user_id) REFERENCES [User](id) ON DELETE SET NULL
    );

    CREATE NONCLUSTERED INDEX IX_activity_logs_action ON activity_logs(action);
    CREATE NONCLUSTERED INDEX IX_activity_logs_created_at ON activity_logs(created_at);
END
GO
