import uuid

from app.models.session import UserSession
from fastapi import APIRouter, Cookie, Response

router = APIRouter()


@router.get("/init")
async def init_or_update_session(
    response: Response, session_id: str | None = Cookie(default=None)
):
    """
    Initialize or update the user session.
    If the user does not have a cookie with session_id, create a new one stored in the database and return the cookie.
    If cookies are included, update the last_active_at time in the database.
    """
    if session_id:
        try:
            # Try to search for this UUID in the database
            session = await UserSession.get_or_none(session_id=uuid.UUID(session_id))
            if session:
                # If it exists, Tortoise will automatically update last_active_at because auto_now=True
                await session.save()
                return {
                    "status": "success",
                    "message": "The session has been updated.",
                    "session_id": session_id,
                }
        except ValueError:
            # Prevent false UUids with incorrect formats from being sent from the front end
            pass

    # If no Cookie is carried or the record cannot be found in the database, a new session will be created
    new_uuid = uuid.uuid4()
    # Store in the PostgreSQL database
    await UserSession.create(session_id=new_uuid)

    # A new session has been created
    response.set_cookie(
        key="session_id",
        value=str(new_uuid),
        httponly=True,  # Prevent front-end JS from reading and enhance security
        max_age=60 * 60,  # 1 hour
        samesite="lax",
    )

    return {
        "status": "success",
        "message": "A new session has been created",
        "session_id": str(new_uuid),
    }
