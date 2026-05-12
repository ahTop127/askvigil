import uuid
from app.models.session import UserSession

async def get_or_create_session_from_cookie(
    session_id: str | None,
) -> UserSession:

    if session_id:
        try:
            session_uuid = uuid.UUID(session_id)
            session = await UserSession.get_or_none(session_id=session_uuid)
            if session:
                await session.save()
                return session
        except ValueError:
            pass

    return await UserSession.create()
