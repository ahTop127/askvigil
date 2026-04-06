from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "open_dataset" ADD "text_embedding" public.vector(384);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "open_dataset" DROP COLUMN "text_embedding";"""


MODELS_STATE = (
    "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"
)
