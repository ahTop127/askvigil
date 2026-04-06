from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "open_dataset" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "source" VARCHAR(50) NOT NULL,
    "label" VARCHAR(20) NOT NULL,
    "original_text" TEXT NOT NULL,
    "clean_text" TEXT NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "open_dataset";"""


MODELS_STATE = (
    "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"
)
