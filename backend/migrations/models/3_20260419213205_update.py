from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
COMMENT ON COLUMN "phishing_url"."url_embedding" IS 'The feature vector extracted by URLBERT (768-dim)';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "phishing_url";"""


MODELS_STATE = (
    "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"
    "L1DxjRmrDy/3/wMS6zgE"
)
