"""Script kiem tra ket noi database va thao tac luu/doc log."""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.session import init_db, get_db_info, SessionLocal
from backend.app.db.crud import (
    get_or_create_user,
    log_chat,
    log_image_learning,
    log_pronunciation,
    log_activity,
    get_chat_logs,
    get_image_logs,
    get_pronunciation_logs,
    get_activity_logs,
)


def main():
    print("=" * 60)
    print("KIỂM TRA KẾT NỐI VÀ LƯU LOG DATABASE")
    print("=" * 60)

    # 1. Khoi tao database
    success = init_db()
    info = get_db_info()

    print(f"Trạng thái kết nối: {'THÀNH CÔNG' if info.get('connected') else 'THẤT BẠI'}")
    print(f"Driver CSDL:        {info.get('driver')}")
    print(f"Database:           {info.get('database')}")
    print(f"Dùng Fallback DB:   {info.get('is_fallback')}")
    print(f"Số lượng bảng:      {info.get('table_count')}")
    print(f"Danh sách bảng:     {', '.join(info.get('tables', []))}")
    print("-" * 60)

    if not info.get("connected"):
        print("[LỖI] Không thể kết nối database:", info.get("error"))
        return

    # 2. Test ghi va doc log
    with SessionLocal() as db:
        print("\n[1/4] Test tạo user & lưu chat log...")
        user = get_or_create_user(db, "test_learner")
        chat_entry = log_chat(
            db=db,
            session_id="session_test_001",
            user_message="Hello tutor, how do I pronounce 'phenomenon'?",
            bot_response="Hello! 'Phenomenon' is pronounced /fəˈnɒm.ɪ.nən/.",
            user_id=user.id,
        )
        print(f" -> Đã lưu Chat Log ID: {chat_entry.id}")

        print("\n[2/4] Test lưu image learning log...")
        img_entry = log_image_learning(
            db=db,
            file_name="classroom.jpg",
            detected_labels=["book", "chair", "laptop"],
            annotated_img_url="/uploads/annotated_classroom.jpg",
            lesson_context="Today we learn objects found in a modern classroom.",
            quiz_data={"question": "What is used for typing?", "options": ["book", "laptop"], "answer": "laptop"},
            user_id=user.id,
        )
        print(f" -> Đã lưu Image Log ID: {img_entry.id}")

        print("\n[3/4] Test lưu pronunciation log...")
        pron_entry = log_pronunciation(
            db=db,
            target_word="phenomenon",
            score=92,
            feedback="Phát âm rất tốt, trọng âm rơi đúng vào âm tiết thứ hai.",
            tip="Chú ý lướt nhẹ âm schwa /ə/ ở âm tiết đầu.",
            user_id=user.id,
        )
        print(f" -> Đã lưu Pronunciation Log ID: {pron_entry.id}")

        print("\n[4/4] Test lưu activity log...")
        act_entry = log_activity(
            db=db,
            action="TEST_VERIFICATION",
            status="SUCCESS",
            details="Database verification script executed successfully",
            ip_address="127.0.0.1",
            user_id=user.id,
        )
        print(f" -> Đã lưu Activity Log ID: {act_entry.id}")

        print("\n" + "=" * 60)
        print("KIỂM TRA ĐỌC LOG:")
        chats = get_chat_logs(db, limit=3)
        print(f" - Tổng chat logs mới nhất: {len(chats)}")
        prons = get_pronunciation_logs(db, limit=3)
        print(f" - Tổng pronunciation logs mới nhất: {len(prons)}")
        print("=" * 60)
        print("TẤT CẢ CÁC BƯỚC ĐỀU HOÀN TẤT THÀNH CÔNG!\n")


if __name__ == "__main__":
    main()

