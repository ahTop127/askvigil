from app.core.config import settings

import logging

logging.basicConfig(level=logging.DEBUG)

# The core configuration dictionary of Tortoise ORM
TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            # "Aerich.models" must be added. This is the internal table used by Aerich to record migration history
            "models": [
                "app.models.session",
                "app.models.scam",
                "app.models.quiz",
                "app.models.open_data",
                "app.models.scam_case",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
    "log_queries": True,  # print sql log in the control
}
