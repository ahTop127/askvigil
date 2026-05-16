"""
Seed scam_categories (Epic 3 & 7 baseline).

Idempotent: safe to run multiple times (matches by name, refreshes description if changed).

Run from backend root:
  ENVIRONMENT=prod python app/scripts/seed_scam_categories.py

CI/CD: after migrations, add a step with working directory `backend` and DATABASE_URL
(or .env.{ENVIRONMENT}) available, same as the FastAPI app.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dotenv import load_dotenv
from tortoise import Tortoise
import logging
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(app_dir)
sys.path.append(project_root)

# 2. Dynamically load environment variables (must be loaded before importing core.database!)
# Read the system environment variable APP_ENV. If it is not set, it defaults to fallback to 'dev'.
app_env = os.getenv("ENVIRONMENT", "dev")
env_filename = f".env.{app_env}"
env_path = os.path.join(project_root, env_filename)

if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    logger.warning(
        f" Warning: The environment variable file {env_path} cannot be found. The system will attempt to rely on the existing system environment variables."
    )


from app.core.database import TORTOISE_ORM
from app.models.scam import ScamCategory

CATEGORIES: list[tuple[str, str]] = [
    (
        "Job Scams",
        "Calls from imposters pretending to be authorities threatening you to make payment.",
    ),
    (
        "Phishing Scams",
        "Fake messages impersonating legitimate organizations to steal your personal data.",
    ),
    (
        "OTP Scams",
        "Scammers trick you into revealing your one-time passwords and verification codes.",
    ),
    (
        "QR Code Scams",
        "Malicious QR codes that lead to fake websites or install harmful apps on your device.",
    ),
    (
        "Suspicious Links",
        "Harmful URLs designed to steal your information or infect your device with malware.",
    ),
]


async def seed() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        created_n = 0
        updated_n = 0
        for name, description in CATEGORIES:
            obj, created = await ScamCategory.get_or_create(
                name=name,
                defaults={"description": description},
            )
            if created:
                created_n += 1
                logger.info(f"  + created: {name}")
            elif (obj.description or "") != description:
                obj.description = description
                await obj.save()
                updated_n += 1
                logger.info(f"  ~ updated description: {name}")
            else:
                logger.info(f"  = unchanged: {name}")
        logger.info(
            f"Done. created={created_n}, description_updated={updated_n}, "
            f"total_defined={len(CATEGORIES)}"
        )
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(seed())
