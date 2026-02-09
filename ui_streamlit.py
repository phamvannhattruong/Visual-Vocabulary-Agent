import io
import streamlit as st
import requests
from gtts import gTTS
from audio_recorder_streamlit import audio_recorder

# --- 1. CẤU HÌNH & HẰNG SỐ ---
API_URL = "http://127.0.0.1:8000/api/v1/analyze"
eval_url = "http://127.0.0.1:8000/api/v1/evaluate-pronunciation"


def init_settings():
    st.set_page_config(page_title="Visual Vocabulary Agent", page_icon="🤖", layout="wide")
    if "api_result" not in st.session_state:
        st.session_state.api_result = None


# --- 2. CÁC HÀM TIỆN ÍCH (UTILITIES) ---
def play_audio(text, lang='en'):
    """Hàm dùng chung cho Voice Agent sau này"""
    try:
        tts = gTTS(text=text, lang=lang)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        st.audio(audio_fp.getvalue(), format='audio/mp3')
    except Exception as e:
        st.error(f"Lỗi âm thanh: {e}")


# --- 3. CÁC THÀNH PHẦN GIAO DIỆN (COMPONENTS) ---
def render_sidebar():
    st.sidebar.header("🛠️ Tùy chọn đầu vào")
    method = st.sidebar.radio("Chọn cách nhập ảnh:", ("Tải ảnh lên", "Sử dụng Webcam"))
    return method

def vocabulary_column(result):
    agent_vision(result)
    vocabulary_practice(result)


def lesson_column(result):
    teacher_agent(result)

# --- 4. GỌI CÁC AGENT ---
def agent_vision(result):
    """Cột hiển thị của Vision Agent"""
    st.subheader("🔍 Vật thể nhận diện")
    objects = result.get("detected_label", [])
    st.info(f"Vật thể: {', '.join(objects)}")
    if objects:
        st.write("**Nghe phát âm:**")
        play_audio(", ".join(objects))

def teacher_agent(result):
    st.subheader("📖 Bài học từ AI")
    st.markdown(result.get('lesson_context', ''))

    # Hiển thị Quiz nếu có
    quiz = result.get('quiz')
    if quiz and isinstance(quiz, dict):
        render_quiz_section(quiz)


def vocabulary_practice(result):
    st.divider()
    st.subheader("🎤 Luyện phát âm cùng AI")

    # Lấy danh sách từ vựng từ Vision Agent
    objects = result.get("detected_label", [])

    if not objects:
        st.write("Chưa có từ vựng nào để luyện tập.")
        return

    # Tạo giao diện danh sách từ vựng kèm nút bấm
    st.write("Chọn một từ để bắt đầu thử thách phát âm:")

    # Sử dụng Session State để lưu từ đang được chọn luyện tập
    if "active_word" not in st.session_state:
        st.session_state.active_word = None

    # Hiển thị danh sách từ vựng theo gạch đầu dòng
    for word in objects:
        col_text, col_btn = st.columns([3, 1])
        with col_text:
            st.markdown(f"**• {word.capitalize()}**")
        with col_btn:
            if st.button("Luyện tập", key=f"practice_{word}", use_container_width=True):
                st.session_state.active_word = word

    # Khu vực tương tác thu âm
    if st.session_state.active_word:
        target = st.session_state.active_word
        st.info(f"Đang luyện tập từ: **{target}**")

        # Widget thu âm
        audio_bytes = audio_recorder(
            text="Nhấn để bắt đầu nói...",
            recording_color="#e8b62c",
            neutral_color="#6aa36f",
            icon_size="2x",
        )

        if audio_bytes:
            # 1. Hiển thị lại âm thanh người dùng vừa nói
            st.audio(audio_bytes, format="audio/wav")

            # 2. Gửi dữ liệu đến Backend để đánh giá
            with st.spinner(f"Gemini đang lắng nghe và phân tích từ '{target}'..."):
                try:
                    # Gửi file audio và từ mục tiêu lên server
                    files = {"audio_file": ("recorded_audio.wav", audio_bytes, "audio/wav")}
                    data = {"target_word": target}

                    response = requests.post(eval_url, files=files, data=data, timeout=30)

                    if response.status_code == 200:
                        eval_result = response.json()

                        # Hiển thị kết quả đánh giá từ Gemini
                        st.metric("Độ chính xác", f"{eval_result.get('score', 0)}%")
                        st.write(f"💬 **Nhận xét:** {eval_result.get('feedback', '')}")
                        st.success(f"🌟 **Mẹo:** {eval_result.get('tip', '')}")

                        if eval_result.get('score', 0) >= 80:
                            st.balloons()
                    else:
                        st.error("Không thể kết nối với Agent đánh giá.")
                except Exception as e:
                    st.error(f"Lỗi phân tích: {e}")



def render_quiz_section(quiz):
    """Thành phần Quiz tương tác"""
    st.divider()
    st.subheader("🧠 Quiz Time!")
    st.write(f"**{quiz.get('question')}**")
    options = quiz.get('options', [])
    cols = st.columns(len(options))
    for i, option in enumerate(options):
        if cols[i].button(option, key=f"btn_{i}", use_container_width=True):
            if option == quiz.get('answer'):
                st.success("Chính xác! 🎉")
                st.balloons()
            else:
                st.error(f"Sai rồi! Đáp án là {quiz.get('answer')} 💡")


# --- 5. LUỒNG CHÍNH (MAIN APP) ---
def main():
    init_settings()
    st.title("🤖 Visual Vocabulary Agent")

    input_method = render_sidebar()
    uploaded_file = st.file_uploader("Chọn ảnh...") if input_method == "Tải ảnh lên" else st.camera_input("Chụp ảnh")

    if uploaded_file:
        st.image(uploaded_file, width=400)
        if st.button("Bắt đầu học ngay!", type="primary"):
            with st.spinner("Đang liên hệ các Agent..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(API_URL, files=files)
                    if response.status_code == 200:
                        st.session_state.api_result = response.json()
                    else:
                        st.error("Backend không phản hồi.")
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")

    # Hiển thị kết quả theo bố cục Agent
    if st.session_state.api_result:
        c1, c2 = st.columns(2)
        with c1: vocabulary_column(st.session_state.api_result)
        with c2: lesson_column(st.session_state.api_result)

    st.divider()
    st.caption("Dự án Multi-Agent Visual Learning - 2026")


if __name__ == "__main__":
    main()