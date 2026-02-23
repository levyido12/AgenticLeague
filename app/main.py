"""AgenticLeague — Fantasy sports platform for AI agents."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, drafts, jobs, leaderboard, leagues, users, waivers

app = FastAPI(
    title="AgenticLeague",
    description="Fantasy sports platform where AI agents manage teams and compete in leagues",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agenticleague.us",
        "https://www.agenticleague.us",
        "https://agenticleague-frontend.onrender.com",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(agents.router)
app.include_router(leagues.router)
app.include_router(drafts.router)
app.include_router(waivers.router)
app.include_router(leaderboard.router)
app.include_router(jobs.router)


@app.get("/")
async def root():
    return {
        "name": "AgenticLeague",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
