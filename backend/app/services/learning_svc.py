import random

from fastapi import HTTPException

from app.models.quiz import QuizAttempt, QuizQuestion
from app.models.scam import ScamCategory
from app.models.session import UserSession
from app.schemas.quiz import QuizBatchSubmitIn


async def get_all_scam_categories():
    """
    Get the list of all fraud categories and sort them by ID
    """
    return await ScamCategory.all().order_by("id")


async def get_random_quiz_question(category_id: int | None = None, limit: int = 5):
    """
    Gets a random quiz question
    If category_id is None, sample from all questions.
    """
    base_query = QuizQuestion.all()

    # check the quiz type is exist
    if category_id is not None:
        category = await ScamCategory.get_or_none(id=category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Scam Category not found")
        base_query = base_query.filter(category_id=category_id)

    # get all the question id from this quiz type(flat=True indicates returning a flat list [1001, 1002...] )
    question_ids = await base_query.values_list("id", flat=True)
    if not question_ids:
        return []

    # Randomly select 5 ids (if the question bank is less than 5 questions, all will be selected)
    selected_ids = random.sample(question_ids, min(limit, len(question_ids)))

    # Query the complete question record based on the extracted ID and load the corresponding options in advance through prefetch_related
    questions = await QuizQuestion.filter(id__in=selected_ids).prefetch_related(
        "options"
    )

    # Since the results retrieved by the filter are sorted by primary key by default,
    # let's shuffle the order again to ensure that the order of each question is also different
    questions_list = list(questions)
    random.shuffle(questions_list)

    return questions_list


async def submit_quiz_batch_and_get_results(payload: QuizBatchSubmitIn) -> dict:
    """
    Handle batch test submissions, record attempts, and generate final reports
    """
    # 1. Ensure that the UserSession exists (if a new uuid is passed from the front end, create it silently)
    session, _ = await UserSession.get_or_create(session_id=payload.session_id)

    correct_count = 0
    results_list = []
    attempt_records = []

    # 2. Traverse all the answer records sent from the front end
    for ans in payload.answers:
        # Look up this question and all its options
        question = await QuizQuestion.get(id=ans.question_id).prefetch_related(
            "options"
        )

        # Find the correct option for this question
        correct_option = next((opt for opt in question.options if opt.is_correct), None)

        # Determine whether the user has answered correctly
        is_correct = False
        if correct_option and correct_option.id == ans.selected_option_id:
            is_correct = True
            correct_count += 1

        # Prepare the attempt record to be written into the database
        attempt_records.append(
            QuizAttempt(
                session_id=session.session_id,
                question_id=ans.question_id,
                selected_option_id=ans.selected_option_id,
                is_correct=is_correct,
            )
        )

        # Assemble the data returned to the front end for review
        results_list.append(
            {
                "question_id": question.id,
                "scenario_text": question.scenario_text,
                "user_selected_option_id": ans.selected_option_id,
                "correct_option_id": correct_option.id if correct_option else None,
                "is_correct": is_correct,
                "explanation": question.explanation,
            }
        )

    # 3. Batch write the answer records to the quiz_attempts table
    if attempt_records:
        await QuizAttempt.bulk_create(attempt_records)

    # 4. Return the final summary report
    return {
        "total_questions": len(payload.answers),
        "correct_answers": correct_count,
        "results": results_list,
    }
