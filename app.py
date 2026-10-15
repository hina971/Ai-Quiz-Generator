import json
import os
from difflib import SequenceMatcher

import streamlit as st

from document_reader import extract_text
from quiz_engine import create_quiz

# ============== PAGE CONFIG ==============

st.set_page_config(
    page_title="Quiz AI",
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
# Colour plan:
#   Page background  -> peach gradient
#   Text on peach    -> very dark and bold (maximum contrast)
#   Header, sidebar, footer, buttons -> deep plum/rose with bright white text

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Light page, so built-in widgets match the peach background */
:root {
    color-scheme: light;
}

/* ===== PEACH GRADIENT BACKGROUND ===== */
.stApp {
    background: linear-gradient(
        -45deg,
        #ffe5d0,
        #ffcfb0,
        #ffb99a,
        #ffd6c0,
        #ffe5d0
    );
    background-size: 400% 400%;
    animation: gradientMove 15s ease infinite;
    color: #1a0b2e;
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

[data-testid="stHeader"] {
    background: rgba(255, 229, 208, 0.85);
}

/* ===== SIDEBAR (dark plum, bright white text) ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #4a044e, #701a75, #9d174d);
    border-right: 1px solid #f9a8d4;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #ffffff !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.35);
}

/* ===== TEXT ON THE PEACH PAGE (dark = clearly visible) ===== */

[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em,
[data-testid="stText"],
.stApp p,
.stApp li {
    color: #1a0b2e;
}

h1, h2, h3, h4, h5, h6,
[data-testid="stHeading"],
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    color: #4a044e !important;
    font-weight: 800;
}

/* Widget labels */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
.stApp label,
.stApp label p {
    color: #1a0b2e !important;
    font-weight: 700;
}

/* Radio answer options */
[data-testid="stRadio"] label,
[data-testid="stRadio"] label p,
[data-testid="stRadio"] label span,
[data-testid="stRadio"] div[role="radiogroup"] label div {
    color: #1a0b2e !important;
    font-size: 16px;
    font-weight: 600;
}

/* Sidebar radio must stay white (it is on the dark sidebar) */
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stRadio"] label span,
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label div {
    color: #ffffff !important;
}

/* Captions */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
.stApp small {
    color: #3b0764 !important;
}

/* ===== INPUTS AND DROPDOWNS (white box, dark text) ===== */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="base-input"],
.stTextInput input,
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #1a0b2e !important;
    border-color: #c2410c !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #1a0b2e !important;
}

[data-baseweb="select"] svg {
    fill: #4a044e !important;
}

input::placeholder,
textarea::placeholder {
    color: #6b5876 !important;
    opacity: 1;
}

/* List that opens under a dropdown */
[data-baseweb="popover"],
[data-baseweb="popover"] ul,
[data-baseweb="menu"] {
    background-color: #ffffff !important;
}

[data-baseweb="popover"] li,
[data-baseweb="popover"] li div,
[data-baseweb="popover"] li span,
[data-baseweb="menu"] li,
[data-baseweb="menu"] li div,
[data-baseweb="menu"] li span {
    color: #1a0b2e !important;
}

[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover {
    background-color: #ffd6c0 !important;
}

/* ===== METRICS ===== */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid #fb923c;
    border-radius: 14px;
    padding: 16px;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] div {
    color: #7c2d12 !important;
    font-weight: 700;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color: #1a0b2e !important;
    font-weight: 800;
}

/* ===== MESSAGE BOXES (success / error / info / warning) ===== */
[data-testid="stAlert"] {
    background-color: rgba(255, 255, 255, 0.9) !important;
    border: 2px solid #c2410c;
    border-radius: 12px;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span,
[data-testid="stAlert"] li {
    color: #1a0b2e !important;
    font-weight: 600;
}

/* ===== EXPANDER ===== */
[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid #fb923c;
    border-radius: 12px;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #1a0b2e !important;
    font-weight: 700;
}

/* ===== CODE BLOCKS (dark box, bright text) ===== */
[data-testid="stCode"],
[data-testid="stCode"] pre,
[data-testid="stCode"] code {
    background-color: #2a0e3a !important;
    color: #fde68a !important;
}

/* ===== BORDERED CONTAINERS AND QUIZ FORM ===== */
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.55);
    border-color: #fb923c !important;
    border-radius: 14px;
}

hr {
    border-color: #c2410c;
}

/* ===== HEADER BANNER (dark, bright white text) ===== */
.ua-header {
    background: linear-gradient(120deg, #4a044e, #831843, #be185d);
    border: 1px solid #f9a8d4;
    border-radius: 20px;
    padding: 25px 15px;
    margin-bottom: 28px;
    text-align: center;
    box-shadow: 0 12px 35px rgba(74, 4, 78, 0.25);
}

.ua-header h1 {
    font-size: clamp(28px, 5vw, 43px);
    font-weight: 800;
    color: #ffffff !important;
    margin: 0;
}

.ua-header h1 span {
    color: #fed7aa !important;
}

.ua-header p {
    color: #ffffff !important;
    font-size: 15px;
    font-weight: 500;
    line-height: 1.7;
}

/* ===== HERO CARD ===== */
.hero-title {
    font-size: clamp(27px, 4vw, 42px);
    font-weight: 800;
    color: #4a044e !important;
}

.hero-title span {
    color: #be123c !important;
}

.hero-subtitle {
    color: #1a0b2e !important;
    font-size: 16px;
    font-weight: 500;
    line-height: 1.8;
}

/* ===== FEATURE CARDS ===== */
.section-card {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid #fb923c;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
}

.section-card h3 {
    color: #9d174d !important;
}

.section-card p {
    color: #1a0b2e !important;
    font-size: 15px;
    font-weight: 500;
}

/* ===== BUTTONS (deep rose, bright white text) ===== */
div.stButton > button,
div.stFormSubmitButton > button,
div.stDownloadButton > button,
[data-testid="stFileUploaderDropzone"] button {
    background: linear-gradient(100deg, #9d174d, #be123c, #c2410c);
    background-size: 200% 200%;
    border-radius: 12px;
    border: 1px solid #f9a8d4;
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
    border-color: #4a044e;
    color: #ffffff !important;
    transform: translateY(-2px);
}

/* ===== FOOTER (dark, bright white text) ===== */
.ua-footer {
    background: linear-gradient(135deg, #4a044e, #831843);
    border: 1px solid #f9a8d4;
    border-top: 3px solid #fb923c;
    border-radius: 16px;
    padding: 24px 12px;
    text-align: center;
    margin-top: 45px;
}

.ua-footer h3 {
    color: #fed7aa !important;
}

.ua-footer p {
    color: #ffffff !important;
    font-size: 14px;
    line-height: 1.7;
}

.ua-footer .creator {
    color: #fed7aa !important;
    font-size: 18px;
    font-weight: 800;
}

.ua-footer .copyright {
    color: #fce7f3 !important;
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
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid #fb923c;
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 8px 32px rgba(194, 65, 12, 0.15);
    text-align: center;
    transition: all 0.3s ease;
}

.hero-card:hover,
.feature-card:hover,
.stat-card:hover,
.result-card:hover {
    border-color: #be123c;
    box-shadow: 0 12px 35px rgba(190, 18, 60, 0.2);
    transform: translateY(-3px);
}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.6);
    border: 2px dashed #c2410c;
    border-radius: 16px;
    padding: 12px;
}

[data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 12px;
}

[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploaderFileName"] {
    color: #1a0b2e !important;
}

/* The upload button text must stay white */
[data-testid="stFileUploaderDropzone"] button span,
[data-testid="stFileUploaderDropzone"] button p {
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)


# ============== HEADER / HERO / FOOTER ==============

def show_header():
    st.markdown("""
    <div class="ua-header">
        <h1>🧠 Quiz <span>AI</span></h1>
        <p>
            AI-POWERED LEARNING PLATFORM<br>
            Transform Documents into Smart Interactive Quizzes
            <br>
            Learn Smarter. Practice Better. Achieve More.
        </p>
    </div>
    """, unsafe_allow_html=True)


def show_hero(
    title="Welcome to <span>Quiz AI</span> 🧠",
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
        <h3>🧠 Quiz AI</h3>
        <p>AI-Powered Smart Quiz Generator</p>
        <p>Designed &amp; Developed with ❤️ by</p>
        <p class="creator">Hina Ramzan</p>
        <p>Learn Smarter with AI</p>
        <p class="copyright">
            © 2026 Quiz AI. All Rights Reserved.
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
    st.markdown("## 🧠 Quiz AI")
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
    st.caption("Created by Hina Ramzan")


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
                file_name="quiz_ai_results.json",
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
        "ℹ️ About Quiz AI",
        "Your personal AI-powered learning assistant.",
    )

    st.markdown("""
    ### 🧠 What is Quiz AI?

    Quiz AI converts your study documents into interactive quizzes
    to help you learn, practice, and test your knowledge.

    ### ✨ Features

    - 📄 Upload PDF, DOCX, TXT, and Markdown files.
    - 🤖 Generate quizzes using Gemini AI.
    - 🎯 Choose question count, difficulty, and language.
    - ✅ Check answers and view your score.
    - 📥 Download quiz questions and answers as JSON.

    ### 👨‍💻 Created by

    **Hina Ramzan**

    *AI Research • Data Analysis • Research & Problem Solving*
    """)

    st.info(
        "For AI quiz generation, configure your Gemini API key "
        "in Streamlit Secrets."
    )


# ============== FOOTER ==============

show_footer()
