"""Seed NBA players into the database from nba_api."""

import asyncio
import ssl
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Base
from app.models.player import Player

# Position mapping: nba_api uses short forms like "G", "F", "C", "G-F", "F-C"
# We convert to our sport-scoped format: "nba:PG", "nba:SG", etc.
import math


def _safe_float(val) -> float:
    """Convert to float, treating NaN/None as 0."""
    try:
        f = float(val)
        return 0.0 if math.isnan(f) else f
    except (TypeError, ValueError):
        return 0.0


POSITION_MAP = {
    "G": "nba:PG-nba:SG",
    "F": "nba:SF-nba:PF",
    "C": "nba:C",
    "G-F": "nba:SG-nba:SF",
    "F-G": "nba:SF-nba:SG",
    "F-C": "nba:PF-nba:C",
    "C-F": "nba:C-nba:PF",
}


def fetch_nba_players() -> list[dict]:
    """Fetch all active NBA players using nba_api PlayerIndex."""
    from nba_api.stats.endpoints import playerindex

    print("Fetching players from NBA.com...")
    time.sleep(2)  # Rate limit
    idx = playerindex.PlayerIndex(season="2025-26")
    df = idx.get_data_frames()[0]

    players = []
    for _, row in df.iterrows():
        position_raw = str(row.get("POSITION", "")).strip()
        position = POSITION_MAP.get(position_raw, f"nba:{position_raw}" if position_raw else "nba:SF")

        team = str(row.get("TEAM_ABBREVIATION", "")).strip()
        if not team or team == "None":
            continue  # Skip players without a team

        first = str(row.get("PLAYER_FIRST_NAME", "")).strip()
        last = str(row.get("PLAYER_LAST_NAME", "")).strip()
        full_name = f"{first} {last}".strip()

        players.append({
            "external_id": str(row["PERSON_ID"]),
            "full_name": full_name,
            "position": position,
            "nba_team": team,
            "sport": "nba",
            "status": "active",
            "season_stats": {
                "pts": _safe_float(row.get("PTS", 0)),
                "reb": _safe_float(row.get("REB", 0)),
                "ast": _safe_float(row.get("AST", 0)),
            },
        })

    print(f"Fetched {len(players)} players")
    return players


async def seed(players: list[dict]):
    """Insert players into the database, skipping duplicates."""
    import certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    engine = create_async_engine(
        settings.database_url,
        connect_args={"ssl": ssl_context},
    )

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        inserted = 0
        skipped = 0

        for p in players:
            # Check if player already exists
            result = await db.execute(
                select(Player).where(Player.external_id == p["external_id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update team/position/status in case they changed
                existing.nba_team = p["nba_team"]
                existing.position = p["position"]
                existing.status = p["status"]
                existing.season_stats = p["season_stats"]
                skipped += 1
            else:
                db.add(Player(**p))
                inserted += 1

        await db.commit()
        print(f"Done! Inserted: {inserted}, Updated: {skipped}")

    await engine.dispose()


def main():
    players = fetch_nba_players()
    asyncio.run(seed(players))


if __name__ == "__main__":
    main()
