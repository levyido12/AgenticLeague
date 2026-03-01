"""Activity feed and stats endpoints."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.activity_log import ActivityLog
from app.models.agent import Agent

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("")
async def get_activity(db: AsyncSession = Depends(get_db)):
    """Public feed of the last 50 platform actions."""
    result = await db.execute(
        select(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()

    # Resolve agent names
    agent_ids = {l.agent_id for l in logs if l.agent_id}
    agents_map = {}
    if agent_ids:
        agents_result = await db.execute(select(Agent).where(Agent.id.in_(agent_ids)))
        agents_map = {a.id: a.name for a in agents_result.scalars().all()}

    return [
        {
            "id": str(log.id),
            "agent_name": agents_map.get(log.agent_id, "System") if log.agent_id else "System",
            "action": log.action,
            "detail": log.detail,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/stats")
async def get_activity_stats(db: AsyncSession = Depends(get_db)):
    """Platform activity metrics."""
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    week_ago = now - timedelta(days=7)

    # Agents active today
    agents_today_result = await db.execute(
        select(func.count(func.distinct(ActivityLog.agent_id))).where(
            ActivityLog.created_at >= today_start,
            ActivityLog.agent_id.is_not(None),
        )
    )
    agents_today = agents_today_result.scalar() or 0

    # Actions today
    actions_today_result = await db.execute(
        select(func.count()).select_from(ActivityLog).where(
            ActivityLog.created_at >= today_start,
        )
    )
    actions_today = actions_today_result.scalar() or 0

    # Actions this week
    actions_week_result = await db.execute(
        select(func.count()).select_from(ActivityLog).where(
            ActivityLog.created_at >= week_ago,
        )
    )
    actions_week = actions_week_result.scalar() or 0

    return {
        "agents_active_today": agents_today,
        "actions_today": actions_today,
        "actions_this_week": actions_week,
    }
