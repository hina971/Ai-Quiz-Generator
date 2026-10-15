import json
import re
import time
import random

from google import genai


MODEL_NAME = "gemini-3.8-flash"


def create_quiz(
    api_key,
    document_text,
    question_count=10,
    question_type="MCQ",
    language="English",
    difficulty="Medium"
):
    if not api_key:
        raise ValueError(
            "Gemini API key missing. Streamlit Secrets check karein."
        )

    if not document_text or not document_text.strip():
        raise ValueError(
            "Uploaded file se readable text nahi mila."
        )

    if not 1 <= question_count <= 50:
        raise ValueError(
            "Questions ki tadaad 1 se 50 ke darmiyan honi chahiye."
        )

    client = genai.Client(api_key=api_key)

    source_text = document_text[:60000]

    prompt = f"""
You are an expert educational quiz generator.

Read the source material carefully and create a quiz based ONLY
on the information provided in the source material.

REQUIREMENTS:
- Number of questions: {question_count}
- Question type: {question_type}
- Language: {language}
- Difficulty: {difficulty}

Return ONLY valid JSON. Do not use Markdown code fences.

Use this exact JSON structure:

{{
  "title": "Quiz title",
  "questions": [
    {{
      "question": "Write the question here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option",
      "explanation": "Explain why this answer is correct"
    }}
  ]
}}

RULES:
1. Generate exactly {question_count} questions.
2. For MCQ, provide exactly four distinct options.
3. For True/False, options must be ["True", "False"].
4. For Short Answer, options must be an empty list [].
5. The answer must be correct and supported by the source.
6. For MCQ and True/False, answer must exactly match one option.
7. Do not repeat questions.
8. Keep explanations clear and useful.
9. Return valid JSON without extra text.

SOURCE MATERIAL:
{source_text}
"""

    # Retry temporarily unavailable Gemini service
    max_attempts = 4
    last_error = None

    for attempt in range(max_attempts):
        try:
            response = client.interactions.create(
                model=MODEL_NAME,
                input=prompt
            )

            response_text = response.output_text

            if not response_text:
                raise ValueError(
                    "Gemini ne koi quiz text return nahi kiya."
                )

            # Remove Markdown fences if Gemini adds them
            response_text = re.sub(
                r"^\s*```(?:json)?\s*|\s*```\s*$",
                "",
                response_text.strip(),
                flags=re.IGNORECASE
            )

            quiz = json.loads(response_text)
            break

        except Exception as error:
            last_error = error
            error_message = str(error).lower()

            temporary_error = any(
                term in error_message
                for term in [
                    "503",
                    "service_unavailable",
                    "unavailable",
                    "429",
                    "resource_exhausted",
                    "500",
                    "502",
                    "504",
                    "timeout",
                    "timed out",
                    "connection"
                ]
            )

            if not temporary_error:
                raise RuntimeError(
                    f"Quiz generate nahi hua: {error}"
                ) from error

            if attempt == max_attempts - 1:
                break

            # Wait progressively longer before retrying
            wait_seconds = min(
                2 ** (attempt + 1) + random.uniform(0, 1),
                20
            )

            time.sleep(wait_seconds)

    else:
        raise RuntimeError(
            f"Quiz generate nahi hua: {last_error}"
        )

    if last_error is not None and "quiz" not in locals():
        raise RuntimeError(
            "Gemini service abhi busy hai. Kuch der baad try karein."
        ) from last_error

    if not isinstance(quiz, dict):
        raise ValueError(
            "Gemini ka response valid JSON object nahi hai."
        )

    questions = quiz.get("questions", [])

    if not isinstance(questions, list):
        raise ValueError(
            "Quiz questions ki format ghalat hai."
        )

    if len(questions) != question_count:
        raise ValueError(
            f"Gemini ne {len(questions)} questions banaye, "
            f"jabke {question_count} required thay. Dobara try karein."
        )

    validated_questions = []

    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"Question {index} ki format ghalat hai."
            )

        question = item.get("question", "")
        options = item.get("options", [])
        answer = item.get("answer", "")
        explanation = item.get("explanation", "")

        if not isinstance(question, str) or not question.strip():
            raise ValueError(
                f"Question {index} ka text missing hai."
            )

        if not isinstance(options, list):
            raise ValueError(
                f"Question {index} ke options ghalat hain."
            )

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError(
                f"Question {index} ka answer missing hai."
            )

        if question_type == "MCQ":
            if len(options) != 4:
                raise ValueError(
                    f"Question {index} mein 4 options nahi hain."
                )

            if len(set(options)) != 4:
                raise ValueError(
                    f"Question {index} mein duplicate options hain."
                )

            if answer not in options:
                raise ValueError(
                    f"Question {index} ka answer options mein nahi hai."
                )

        elif question_type == "True/False":
            if options != ["True", "False"]:
                raise ValueError(
                    f"Question {index} ke True/False options ghalat hain."
                )

            if answer not in options:
                raise ValueError(
                    f"Question {index} ka answer True ya False hona chahiye."
                )

        elif question_type == "Short Answer":
            if options:
                raise ValueError(
                    f"Question {index} ke Short Answer options empty hone chahiye."
                )

        validated_questions.append({
            "question": question.strip(),
            "options": options,
            "answer": answer.strip(),
            "explanation": str(explanation).strip()
        })

    quiz["questions"] = validated_questions

    if not quiz.get("title"):
        quiz["title"] = "Generated Quiz"

    return quiz
