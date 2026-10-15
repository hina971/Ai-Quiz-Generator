import json
import os
from difflib import SequenceMatcher

import streamlit as st

from document_reader import extract_text
from quiz_engine import create_quiz

# ============== PAGE CONFIG ==============

st.set_page_config(
    page_title="UA Quiz AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============== SESSION STATE ==============

defaults = {
    "quiz": None,
    "answers": {},
    "submitted": False,
    "last_result": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============== CUSTOM DESIGN ==============

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Tell the browser this is a dark page so built-in widgets match */
:root {
    color-scheme: dark;
}

/* Animated Gradient Background */
.stApp {
    background: linear-gradient(
        -45deg,
        #0f172a,
        #312e81,
        #581c87,
        #164e63,
        #0f172a
    );
    background-size: 400% 400%;
    animation: gradientMove 15s ease infinite;
    color: #ffffff;
    font-family: 'Inter', sans-serif;
}

@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

[data-testid="stMainBlockContainer"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827, #1e1b4b, #3b0764);
    border-right: 1px solid #273451;
}

[data-testid="stHeader"] {
    background: rgba(11, 16, 32, 0.85);
}

/* ===== BRIGHT TEXT EVERYWHERE ===== */

/* Normal text, lists, bold, italic */
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em,
[data-testid="stText"],
.stApp p,
.stApp li {
    color: #ffffff;
}

/* Headings */
h1, h2, h3, h4, h5, h6,
[data-testid="stHeading"],
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    color: #ffffff !important;
}

/* Widget labels (selectbox, radio, file uploader, text input, ...) */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
.stApp label,
.stApp label p {
    color: #ffffff !important;
    font-weight: 600;
}

/* Radio and checkbox answer options */
[data-testid="stRadio"] label,
[data-testid="stRadio"] label p,
[data-testid="stRadio"] label span,
[data-testid="stRadio"] div[role="radiogroup"] label div {
    color: #ffffff !important;
    font-size: 16px;
}

/* Captions (small grey text) */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
.stApp small {
    color: #e2e8f0 !important;
}

/* Sidebar text */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: #ffffff;
}

/* Input boxes and dropdowns: dark box, white text */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="base-input"],
.stTextInput input,
.stTextArea textarea {
    background-color: rgba(15, 23, 42, 0.85) !important;
    color: #ffffff !important;
    border-color: #6754a5 !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #ffffff !important;
}

[data-baseweb="select"] svg {
    fill: #ffffff !important;
}

input::placeholder,
textarea::placeholder {
    color: #cbd5e1 !important;
    opacity: 1;
}

/* Dropdown list that opens under a selectbox */
[data-baseweb="popover"],
[data-baseweb="popover"] ul,
[data-baseweb="menu"] {
    background-color: #1e1b4b !important;
}

[data-baseweb="popover"] li,
[data-baseweb="popover"] li div,
[data-baseweb="popover"] li span,
[data-baseweb="menu"] li,
[data-baseweb="menu"] li div,
[data-baseweb="menu"] li span {
    color: #ffffff !important;
}

[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover {
    background-color: #4f46e5 !important;
}

/* Metrics (Score, Percentage, ...) */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] div {
    color: #e2e8f0 !important;
    font-weight: 600;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color: #ffffff !important;
    font-weight: 800;
}

/* Message boxes (success, error, info, warning): dark box, white text */
[data-testid="stAlert"] {
    background-color: rgba(15, 23, 42, 0.88) !important;
    border: 1px solid #67e8f9;
    border-radius: 12px;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span,
[data-testid="stAlert"] li {
    color: #ffffff !important;
}

/* Expander (Technical Details) */
[data-testid="stExpander"] {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid #6754a5;
    border-radius: 12px;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #ffffff !important;
}

/* Code blocks */
[data-testid="stCode"],
[data-testid="stCode"] pre,
[data-testid="stCode"] code {
    background-color: #0b1020 !important;
    color: #a5f3fc !important;
}

/* Bordered containers (quiz result cards) and the quiz form */
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stForm"] {
    background: rgba(15, 23, 42, 0.45);
    border-color: #6754a5 !important;
    border-radius: 14px;
}

/* ===== CUSTOM CARDS ===== */

.ua-header {
    background: linear-gradient(120deg, #111827, #312e81, #6d28d9);
    border: 1px solid #6754a5;
    border-radius: 20px;
    padding: 25px 15px;
    margin-bottom: 28px;
    text-align: center;
    box-shadow: 0 12px 35px rgba(0,0,0,0.22);
}

.ua-header h1 {
    font-size: clamp(28px, 5vw, 43px);
    font-weight: 800;
    color: #ffffff !important;
    margin: 0;
}

.ua-header h1 span {
    color: #a5f3fc !important;
}

.ua-header p {
    color: #f5f3ff !important;
    font-size: 15px;
    line-height: 1.7;
}

.hero-title {
    font-size: clamp(27px, 4vw, 42px);
    font-weight: 800;
    color: #ffffff !important;
}

.hero-title span {
    color: #c4b5fd !important;
}

.hero-subtitle {
    color: #f1f5f9 !important;
    font-size: 15px;
    line-height: 1.8;
}

.section-card {
    background: rgba(24,36,65,0.78);
    border: 1px solid #33446b;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
}

.section-card h3 {
    color: #e9d5ff !important;
}

.section-card p {
    color: #f1f5f9 !important;
    font-size: 15px;
}

div.stButton > button,
div.stFormSubmitButton > button,
div.stDownloadButton > button,
[data-testid="stFileUploaderDropzone"] button {
    background: linear-gradient(100deg, #7c3aed, #4f46e5, #06b6d4);
    background-size: 200% 200%;
    border-radius: 12px;
    border: 1px solid #8b5cf6;
    color: #ffffff !important;
    font-weight: 700;
    min-height: 44px;
    transition: all 0.3s ease;
}

div.stButton > button p,
div.stFormSubmitButton > button p,
div.stDownloadButton > button p,
[data-testid="stFileUploaderDropzone"] button span {
    color: #ffffff !important;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover,
div.stDownloadButton > button:hover,
[data-testid="stFileUploaderDropzone"] button:hover {
    background-position: 100% 50%;
    border-color: #67e8f9;
    color: #ffffff !important;
    transform: translateY(-2px);
}

div[data-testid="stMetric"] {
    background: rgba(24,36,65,0.78);
    border: 1px solid #33446b;
    border-radius: 14px;
    padding: 16px;
}

hr {
    border-color: #4b5d8a;
}

.ua-footer {
    background: linear-gradient(135deg, #111827, #1e1b4b);
    border: 1px solid #373064;
    border-top: 3px solid #8b5cf6;
    border-radius: 16px;
    padding: 24px 12px;
    text-align: center;
    margin-top: 45px;
}

.ua-footer h3 {
    color: #a5f3fc !important;
}

.ua-footer p {
    color: #f1f5f9 !important;
    font-size: 14px;
    line-height: 1.7;
}

.ua-footer .creator {
    color: #a5f3fc !important;
    font-size: 18px;
    font-weight: 800;
}

.ua-footer .copyright {
    color: #cbd5e1 !important;
    font-size: 12px;
}

@media (max-width: 640px) {
    .ua-header { padding: 20px 10px; }
    .hero-card { padding: 22px 12px; }
    .section-card { padding: 14px; }
}

.hero-card,
.feature-card,
.stat-card,
.result-card {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.20);
    text-align: center;
    transition: all 0.3s ease;
}

.hero-card:hover,
.feature-card:hover,
.stat-card:hover,
.result-card:hover {
    border-color: rgba(34, 211, 238, 0.65);
    box-shadow: 0 12px 35px rgba(34, 211, 238, 0.12);
    transform: translateY(-3px);
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px dashed rgba(34, 211, 238, 0.65);
    border-radius: 16px;
    padding: 12px;
}

[data-testid="stFileUploaderDropzone"] {
    background: rgba(15, 23, 42, 0.6);
    border-radius: 12px;
}

[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploaderFileName"] {
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)


# ============== HEADER / HERO / FOOTER ==============

def show_header():
    st.markdown("""
    <div class="ua-header">
        <h1>🧠 UA <span>Quiz AI</span></h1>
        <p>
            AI-POWERED LEARNING PLATFORM<br>
            Transform Documents into Smart Interactive Quizzes
            <br>
            Learn Smarter. Practice Better. Achieve More.
        </p>
    </div>
    """, unsafe_allow_html=True)


def show_hero(
    title="Welcome to <span>UA Quiz AI</span> 🧠",
    subtitle=(
        "Turn your study material into interactive quizzes."
        "<br>Test your knowledge and track your performance."
    ),
):
    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def show_footer():
    st.markdown("""
    <div class="ua-footer">
        <h3>🧠 UA Quiz AI</h3>
        <p>AI-Powered Smart Quiz Generator</p>
        <p>Designed &amp; Developed with ❤️ by</p>
        <p class="creator">Ubaid Ur Rehman</p>
        <p>Learn Smarter with AI</p>
        <p class="copyright">
            © 2026 UA Quiz AI. All Rights Reserved.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ============== HELPERS ==============

def go_to_generator():
    st.session_state["ua_navigation"] = "📝 Quiz Generator"


def is_answer_correct(user_answer, correct_answer, has_options):
    if not isinstance(user_answer, str) or not user_answer.strip():
        return False

    user = user_answer.strip().casefold().rstrip(".!? ")
    correct = correct_answer.strip().casefold().rstrip(".!? ")

    if user == correct:
        return True

    if has_options:
        return False

    return SequenceMatcher(None, user, correct).ratio() >= 0.85


def validate_quiz(quiz):
    if not isinstance(quiz, dict):
        raise ValueError("The quiz engine did not return a valid quiz.")

    questions = quiz.get("questions", [])

    if not isinstance(questions, list) or not questions:
        raise ValueError("No valid questions were generated.")

    for index, item in enumerate(questions):
        if not isinstance(item, dict):
            raise ValueError(f"Question {index + 1} has invalid format.")

        if not item.get("question"):
            raise ValueError(f"Question {index + 1} is missing its text.")

        if not isinstance(item.get("answer"), str):
            raise ValueError(f"Question {index + 1} has no valid answer.")


# ============== API KEY ==============

try:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    api_key = ""

api_key = api_key or os.getenv("GEMINI_API_KEY", "")


# ============== SIDEBAR ==============

with st.sidebar:
    st.markdown("## 🧠 UA Quiz AI")
    st.caption("Your AI-powered learning companion")
    st.divider()

    navigation_options = [
        "🏠 Home",
        "📝 Quiz Generator",
        "📊 My Results",
        "ℹ️ About",
    ]

    page = st.radio(
        "NAVIGATION",
        navigation_options,
        key="ua_navigation",
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**⚡ Powered by Gemini AI**")
    st.caption("Upload. Generate. Learn.")
    st.divider()
    st.caption("Created by Ubaid Ur Rehman")


# ============== GLOBAL HEADER ==============

show_header()


# ============== HOME PAGE ==============

if page == "🏠 Home":

    show_hero()

    st.subheader("Welcome to Your AI Learning Workspace")

    st.write(
        "Generate quizzes from your study materials, "
        "test your knowledge, and review your performance."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="section-card">
            <h3>📄 Smart Upload</h3>
            <p>Upload PDF, Word, text and Markdown documents.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="section-card">
            <h3>🤖 AI Quiz Generator</h3>
            <p>Turn your documents into interactive quizzes.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="section-card">
            <h3>📊 Instant Results</h3>
            <p>Check your score and review correct answers.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🚀 Ready to Get Started?")

    st.write("Open the quiz generator to create your first quiz.")

    st.button(
        "🚀 Open Quiz Generator",
        use_container_width=True,
        on_click=go_to_generator,
    )


# ============== QUIZ GENERATOR ==============

elif page == "📝 Quiz Generator":

    show_hero()

    st.subheader("📝 Create Your Quiz")

    st.caption(
        "Upload your study material and customize your quiz settings."
    )

    if not api_key:
        st.warning(
            "Gemini API key missing. Add GEMINI_API_KEY "
            "to your Streamlit app Secrets."
        )

    uploaded_file = st.file_uploader(
        "📂 Upload Your Document",
        type=["pdf", "docx", "txt", "md"],
        help="Supported formats: PDF, Word, TXT and Markdown.",
        key="ua_document_upload",
    )

    if uploaded_file:
        st.success(f"Selected file: {uploaded_file.name}")

    st.markdown("### ⚙️ Customize Your Quiz")

    col1, col2 = st.columns(2)

    with col1:
        question_count = st.selectbox(
            "Number of Questions",
            [5, 10, 15, 20, 30, 50],
            index=1,
        )

        question_type = st.selectbox(
            "Question Type",
            ["MCQ", "True/False", "Short Answer"],
        )

    with col2:
        language = st.selectbox(
            "Quiz Language",
            ["English", "Urdu"],
        )

        difficulty = st.selectbox(
            "Difficulty Level",
            ["Easy", "Medium", "Hard"],
        )

    if st.button(
        "✨ Generate My Quiz",
        use_container_width=True,
        key="generate_quiz_button",
    ):

        if not uploaded_file:
            st.error("Please upload a document first.")

        elif not api_key:
            st.error("Please configure your Gemini API key first.")

        else:
            try:
                with st.spinner("📖 Reading your document..."):
                    document_text = extract_text(uploaded_file)

                if not document_text or not document_text.strip():
                    raise ValueError(
                        "No readable text found. "
                        "Please upload a text-based document."
                    )

                with st.spinner("🤖 AI is creating your quiz..."):
                    quiz = create_quiz(
                        api_key=api_key,
                        document_text=document_text,
                        question_count=question_count,
                        question_type=question_type,
                        language=language,
                        difficulty=difficulty,
                    )

                validate_quiz(quiz)

                st.session_state["quiz"] = quiz
                st.session_state["answers"] = {}
                st.session_state["submitted"] = False
                st.session_state["last_result"] = None

                st.success("🎉 Your quiz is ready!")

            except Exception as exc:
                st.error(
                    "Unable to generate your quiz. "
                    "Please check your settings and try again."
                )

                with st.expander("Technical Details"):
                    st.code(str(exc))

    # ============== DISPLAY QUIZ ==============

    quiz = st.session_state.get("quiz")

    if quiz:

        st.divider()

        st.subheader(f"📚 {quiz.get('title', 'Your Quiz')}")

        questions = quiz.get("questions", [])

        if not st.session_state.get("submitted", False):

            with st.form("ua_quiz_form"):

                selected_answers = {}

                for index, item in enumerate(questions):

                    st.markdown(f"### Question {index + 1}")
                    st.write(item["question"])

                    options = item.get("options", [])

                    if options:
                        selected_answers[index] = st.radio(
                            "Choose Your Answer",
                            options,
                            key=f"ua_question_{index}",
                            index=None,
                        )
                    else:
                        selected_answers[index] = st.text_input(
                            "Write Your Answer",
                            key=f"ua_question_{index}",
                        )

                    st.divider()

                submitted = st.form_submit_button(
                    "✅ Submit My Quiz",
                    use_container_width=True,
                )

                if submitted:
                    st.session_state["answers"] = selected_answers
                    st.session_state["submitted"] = True
                    st.rerun()

        else:

            answers = st.session_state.get("answers", {})
            score = 0

            st.subheader("📊 Your Quiz Results")

            for index, item in enumerate(questions):

                user_answer = answers.get(index)
                correct_answer = item["answer"]

                if isinstance(user_answer, str):
                    user_answer = user_answer.strip()

                is_correct = is_answer_correct(
                    user_answer,
                    correct_answer,
                    bool(item.get("options")),
                )

                if is_correct:
                    score += 1

                with st.container(border=True):

                    st.markdown(f"### Question {index + 1}")
                    st.write(item["question"])

                    st.write(
                        "**Your Answer:** "
                        f"{user_answer if user_answer else 'Not answered'}"
                    )

                    st.write(f"**Correct Answer:** {correct_answer}")

                    if is_correct:
                        st.success("✅ Correct!")
                    else:
                        st.error("❌ Incorrect")

                    explanation = item.get("explanation", "")

                    if explanation:
                        st.info(f"💡 Explanation: {explanation}")

            total = len(questions)
            percentage = score / total * 100 if total else 0

            st.divider()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Score", f"{score}/{total}")

            with col2:
                st.metric("Percentage", f"{percentage:.1f}%")

            with col3:
                st.metric("Incorrect", str(total - score))

            st.progress(int(percentage))

            if percentage >= 80:
                st.success("🌟 Excellent work!")
            elif percentage >= 50:
                st.info("💪 Good effort! Keep practising.")
            else:
                st.warning("📚 Review the material and try again.")

            result_data = {
                "quiz": quiz,
                "answers": {
                    str(key): value
                    for key, value in answers.items()
                },
                "score": score,
                "total": total,
                "percentage": round(percentage, 2),
            }

            st.session_state["last_result"] = result_data

            st.download_button(
                "📥 Download Results (JSON)",
                data=json.dumps(
                    result_data,
                    ensure_ascii=False,
                    indent=2,
                ),
                file_name="ua_quiz_ai_results.json",
                mime="application/json",
                use_container_width=True,
            )

            if st.button(
                "🔄 Take Quiz Again",
                use_container_width=True,
            ):
                st.session_state["answers"] = {}
                st.session_state["submitted"] = False
                st.rerun()


# ============== MY RESULTS ==============

elif page == "📊 My Results":

    show_hero(
        "📊 My Results",
        "Review your latest quiz performance.",
    )

    if st.session_state.get("last_result"):
        result = st.session_state["last_result"]

        st.success("Your latest quiz result")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Score", f"{result['score']} / {result['total']}")

        with col2:
            st.metric("Percentage", f"{result['percentage']}%")

        with col3:
            st.metric("Correct Answers", result["score"])

        st.progress(min(max(result["percentage"] / 100, 0.0), 1.0))

        st.write("**Quiz:**", result["quiz"].get("title", "Your Quiz"))

    else:
        st.info(
            "No quiz results yet. Generate a quiz and submit your answers "
            "to see your performance here."
        )


# ============== ABOUT ==============

elif page == "ℹ️ About":

    show_hero(
        "ℹ️ About UA Quiz AI",
        "Your personal AI-powered learning assistant.",
    )

    st.markdown("""
    ### 🧠 What is UA Quiz AI?

    UA Quiz AI converts your study documents into interactive quizzes
    to help you learn, practice, and test your knowledge.

    ### ✨ Features

    - 📄 Upload PDF, DOCX, TXT, and Markdown files.
    - 🤖 Generate quizzes using Gemini AI.
    - 🎯 Choose question count, difficulty, and language.
    - ✅ Check answers and view your score.
    - 📥 Download quiz questions and answers as JSON.

    ### 👨‍💻 Created by

    **Ubaid Ur Rehman**

    *AI Research • Data Analysis • Research & Problem Solving*
    """)

    st.info(
        "For AI quiz generation, configure your Gemini API key "
        "in Streamlit Secrets."
    )


# ============== FOOTER ==============

show_footer()
