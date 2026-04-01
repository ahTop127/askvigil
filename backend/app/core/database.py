from app.core.config import settings

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
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
