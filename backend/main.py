from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.router import api_router
from tortoise.contrib.fastapi import register_tortoise
from app.core.database import TORTOISE_ORM
from app.core.lifespan import lifespan

app = FastAPI(title="AskVigil API", lifespan = lifespan)

# Add this block immediately after creating the 'app'
# Necessary to stop backend and frontend from being blocked from each other
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sleepunderflow.duckdns.org", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# 注册 Tortoise ORM
register_tortoise(
    app,
    config=TORTOISE_ORM,
    # Set it to False because we are going to use Aerich to manage table structure changes
    generate_schemas=False,
    # Whether SQL statements are printed in the console when an exception occurs for convenient debugging
    # Do not turn on the production environment
    add_exception_handlers=True,
)


@app.get("/")
async def health_check():
    return {"status": "ok", "project": "AskVigil Backend"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
