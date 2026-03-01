"""Activity logging helper."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog


async def log_activity(
    db: AsyncSession,
    agent_id: uuid.UUID | None,
    action: str,
    detail: dict | None = None,
) -> ActivityLog:
    entry = ActivityLog(agent_id=agent_id, action=action, detail=detail)
    db.add(entry)
    await db.flush()
    return entry
