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
CREATE TABLE IF NOT EXISTS "open_dataset" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "source" VARCHAR(50) NOT NULL,
    "label" VARCHAR(20) NOT NULL,
    "original_text" TEXT NOT NULL,
    "clean_text" TEXT NOT NULL,
    "has_url" INT NOT NULL DEFAULT 0,
    "raw_length" INT NOT NULL DEFAULT 0,
    "clean_length" INT NOT NULL DEFAULT 0,
    "text_embedding" public.vector(384)
);
COMMENT ON COLUMN "open_dataset"."has_url" IS '1 if contains URL, 0 otherwise';
COMMENT ON COLUMN "open_dataset"."raw_length" IS 'Character length of original text';
COMMENT ON COLUMN "open_dataset"."clean_length" IS 'Character length of cleaned text';
CREATE TABLE IF NOT EXISTS "phishing_url" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "source" VARCHAR(50) NOT NULL,
    "is_malicious" BOOL NOT NULL DEFAULT True,
    "original_url" TEXT NOT NULL,
    "resolved_url" TEXT,
    "domain" VARCHAR(255),
    "path" TEXT,
    "preview_title" VARCHAR(500),
    "url_embedding" public.vector(768),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_phishing_ur_domain_6bb096" ON "phishing_url" ("domain");
COMMENT ON COLUMN "phishing_url"."source" IS 'dataset source';
COMMENT ON COLUMN "phishing_url"."is_malicious" IS 'True=Phishing website, False=Safe website';
COMMENT ON COLUMN "phishing_url"."original_url" IS 'The original URL might be a bit.ly short link';
COMMENT ON COLUMN "phishing_url"."resolved_url" IS 'Redirect the real long link after expansion';
COMMENT ON COLUMN "phishing_url"."domain" IS 'Clean the extracted core domain names, such as scam.com';
COMMENT ON COLUMN "phishing_url"."path" IS 'URL path, such as /login';
COMMENT ON COLUMN "phishing_url"."preview_title" IS 'The title of the captured web page (used for Link Preview)';
COMMENT ON COLUMN "phishing_url"."url_embedding" IS 'The feature vector extracted by URLBERT (768-dim)';
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
    "P1/ke4A="
)
