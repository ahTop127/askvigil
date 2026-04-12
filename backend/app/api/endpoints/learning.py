from fastapi import APIRouter, Query
from typing import List, Optional

from app.schemas.quiz import (
    QuizQuestionOut,
    ScamCategoryOut,
    QuizBatchSubmitIn,
    QuizBatchSummaryOut,
)
from app.services import learning_svc

router = APIRouter()


@router.get(
    "/categories",
    response_model=List[ScamCategoryOut],
    summary="Get all fraud categories",
)
async def fetch_scam_categories():
    categories = await learning_svc.get_all_scam_categories()
    return categories


@router.get(
    "/quizzes/{category_id}",
    response_model=List[QuizQuestionOut],
    summary="Get random quiz questions on specific types of fraud",
    description="""
        It is invoked when the user enters the specific scam type card and clicks 'Practice Detection'.
    
        Randomly return 5 test questions of the corresponding type.
        For anti-cheating and security reasons, the correct answer (is_correct) and explanation (explanation) are not included in the returned result.
        """,
)
async def fetch_quiz_questions(
    category_id: Optional[int] = Path(
        default=None, description="Scam category ID (optional)"
    ),
):

    questions = await learning_svc.get_random_quiz_question(
        category_id=category_id, limit=5
    )
    return questions


@router.post(
    "/quizzes/submit",
    response_model=QuizBatchSummaryOut,
    summary="Submit your test answers and get the result report",
    description="""
    When the user finishes all the Quiz questions, click submit to enter 'Quiz Complete! It is called when the page is on.

    - Receive the user's session_id and the answer list of 5 questions.
    - Record the answer result to the database (quiz_attempts).
    Return a summary report containing the total score (correct_answers/total_questions) and detailed explanations for each question.
    """,
)
async def submit_quiz_answers(payload: QuizBatchSubmitIn):

    summary_report = await learning_svc.submit_quiz_batch_and_get_results(payload)
    return summary_report
