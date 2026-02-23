"""Background job endpoints (triggered by cron-job.org)."""

import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.job_run import JobRun
from app.models.league import League
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
    """Score all matchups for a specific scoring period."""
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


@router.post("/nightly")
async def nightly_job(
    game_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(_verify_job_secret),
):
    """All-in-one nightly job: fetch yesterday's stats, then score all active weeks.

    This is the endpoint cron-job.org should hit daily at 5 AM ET.
    """
    target_date = game_date or (date.today() - timedelta(days=1))

    job = JobRun(
        job_name="nightly",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.commit()

    stats_count = 0
    matchups_scored = 0
    errors = []

    # Step 1: Fetch stats
    try:
        stats_count = await fetch_and_store_game_logs(db, target_date)
        logger.info("Fetched %d game logs for %s", stats_count, target_date)
    except Exception as e:
        logger.exception("nightly: fetch_stats failed")
        errors.append(f"fetch_stats: {e}")

    # Step 2: Score all active leagues' current scoring periods
    try:
        leagues_result = await db.execute(
            select(League).where(League.status.in_(["active", "playoffs"]))
        )
        active_leagues = leagues_result.scalars().all()

        for league in active_leagues:
            # Find scoring periods that contain the target date
            periods_result = await db.execute(
                select(ScoringPeriod).where(
                    and_(
                        ScoringPeriod.league_id == league.id,
                        ScoringPeriod.start_date <= target_date,
                        ScoringPeriod.end_date >= target_date,
                    )
                )
            )
            periods = periods_result.scalars().all()

            for period in periods:
                try:
                    count = await score_matchups_for_period(db, period.id)
                    matchups_scored += count
                except Exception as e:
                    logger.exception(
                        "nightly: score_week failed for period %s", period.id
                    )
                    errors.append(f"score period {period.id}: {e}")

    except Exception as e:
        logger.exception("nightly: league scoring failed")
        errors.append(f"league_scoring: {e}")

    job.status = "completed" if not errors else "completed_with_errors"
    job.records_processed = stats_count
    job.error_message = "; ".join(errors) if errors else None
    job.finished_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "job_id": str(job.id),
        "status": job.status,
        "date": str(target_date),
        "stats_fetched": stats_count,
        "matchups_scored": matchups_scored,
        "active_leagues": len(active_leagues) if "active_leagues" in dir() else 0,
        "errors": errors if errors else None,
    }
