from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user_sessions" (
    "session_id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_active_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "detection_logs" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "input_type" VARCHAR(20) NOT NULL,
    "input_content" TEXT NOT NULL,
    "risk_score" DECIMAL(5,2),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "session_id" UUID REFERENCES "user_sessions" ("session_id") ON DELETE SET NULL
);
COMMENT ON COLUMN "detection_logs"."input_type" IS 'TEXT: text\nIMAGE: image';
CREATE TABLE IF NOT EXISTS "scam_categories" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "description" TEXT
);
CREATE TABLE IF NOT EXISTS "guidance_steps" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "step_number" INT NOT NULL,
    "action_text" TEXT NOT NULL,
    "category_id" INT NOT NULL REFERENCES "scam_categories" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_guidance_st_categor_b0405c" UNIQUE ("category_id", "step_number")
);
CREATE TABLE IF NOT EXISTS "quiz_questions" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "scenario_text" TEXT NOT NULL,
    "explanation" TEXT,
    "category_id" INT REFERENCES "scam_categories" ("id") ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS "quiz_options" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "option_text" TEXT NOT NULL,
    "is_correct" BOOL NOT NULL DEFAULT False,
    "question_id" INT NOT NULL REFERENCES "quiz_questions" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "quiz_attempts" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "is_correct" BOOL NOT NULL,
    "attempted_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "question_id" INT NOT NULL REFERENCES "quiz_questions" ("id") ON DELETE CASCADE,
    "selected_option_id" INT NOT NULL REFERENCES "quiz_options" ("id") ON DELETE CASCADE,
    "session_id" UUID NOT NULL REFERENCES "user_sessions" ("session_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
