"""Background job endpoints (triggered by cron-job.org)."""

import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.job_run import JobRun
from app.models.matchup import ScoringPeriod
from app.services.scoring import fetch_and_store_game_logs, score_matchups_for_period

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _verify_job_secret(secret: str = Query("", alias="secret")):
    """Optional secret to protect job endpoints from unauthorized access."""
    if settings.job_secret and secret != settings.job_secret:
        raise HTTPException(status_code=403, detail="Invalid job secret")


@router.post("/fetch-stats")
async def fetch_stats(
    game_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(_verify_job_secret),
):
    """Fetch NBA stats for a given date (defaults to yesterday)."""
    target_date = game_date or (date.today() - timedelta(days=1))

    job = JobRun(
        job_name="fetch_stats",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.commit()

    try:
        count = await fetch_and_store_game_logs(db, target_date)
        job.status = "completed"
        job.records_processed = count
    except Exception as e:
        logger.exception("fetch_stats failed")
        job.status = "failed"
        job.error_message = str(e)

    job.finished_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "job_id": str(job.id),
        "status": job.status,
        "date": str(target_date),
        "records_processed": job.records_processed,
    }


@router.post("/score-week")
async def score_week(
    period_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(_verify_job_secret),
):
    """Score all matchups for a scoring period."""
    job = JobRun(
        job_name="score_week",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.commit()

    try:
        count = await score_matchups_for_period(db, period_id)
        job.status = "completed"
        job.records_processed = count
    except Exception as e:
        logger.exception("score_week failed")
        job.status = "failed"
        job.error_message = str(e)

    job.finished_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "job_id": str(job.id),
        "status": job.status,
        "matchups_scored": job.records_processed,
    }
