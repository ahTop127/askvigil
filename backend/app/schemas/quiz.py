from pydantic import UUID4, BaseModel, ConfigDict, Field


class QuizOptionOut(BaseModel):
    id: int
    option_text: str

    class Config:
        # Allow data to be read from Tortoise ORM models
        from_attribute = True


class QuizQuestionOut(BaseModel):
    id: int
    scenario_text: str
    options: list[QuizOptionOut]

    model_config = ConfigDict(from_attributes=True)


class ScamCategoryOut(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Receive front-end input parameters: Answer records of individual questions
# ==========================================
class AnswerItemIn(BaseModel):
    question_id: int = Field(..., description="The unique ID of the test question")
    selected_option_id: int = Field(
        ...,
        description="The option ID selected by the user",
    )


# ==========================================
# Receive front-end input parameters: Batch submit 5 questions
# ==========================================
class QuizBatchSubmitIn(BaseModel):
    session_id: UUID4 = Field(
        ...,
        description="The user's Cookie UUID",
    )
    category_id: int = Field(
        ...,
        description="The corresponding Scam type ID (optional for convenient subsequent statistics)",
    )
    answers: list[AnswerItemIn] = Field(
        ..., description="An array of answers containing 5 questions"
    )


# ==========================================
# Return to the front end: The review result of a single question
# ==========================================
class QuizResultItemOut(BaseModel):
    question_id: int = Field(..., description="Title ID")
    scenario_text: str = Field(
        ..., description="The scene description text of the title"
    )
    user_selected_option_id: int = Field(
        ..., description="The actual option ID selected by the user"
    )
    correct_option_id: int = Field(
        ..., description="The correct option ID for this question"
    )
    is_correct: bool = Field(
        ...,
        description="Whether the user answers correctly: true means correct, false means incorrect",
    )
    explanation: str = Field(
        ...,
        description="A detailed explanation of the answer is provided to popularize anti-fraud knowledge among users",
    )


# ==========================================
# Return to the front end: The final Quiz summary report
# ==========================================
class QuizBatchSummaryOut(BaseModel):
    total_questions: int = Field(
        ..., description="The total number of questions in this test"
    )
    correct_answers: int = Field(
        ..., description="The total number of correct answers in this test"
    )
    results: list[QuizResultItemOut] = Field(
        ..., description="A detailed list of review results for each question"
    )
