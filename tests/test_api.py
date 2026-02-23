"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "AgenticLeague"


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    resp = await client.post("/users/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 201
    user = resp.json()
    assert user["username"] == "testuser"

    # Login
    resp = await client.post("/users/login", json={
        "username": "testuser",
        "password": "securepass123",
    })
    assert resp.status_code == 200
    token = resp.json()
    assert "access_token" in token


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post("/users/register", json={
        "username": "dup", "email": "dup@test.com", "password": "pass",
    })
    resp = await client.post("/users/register", json={
        "username": "dup", "email": "dup2@test.com", "password": "pass",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient):
    # Register + login
    await client.post("/users/register", json={
        "username": "agentowner", "email": "ao@test.com", "password": "pass",
    })
    login_resp = await client.post("/users/login", json={
        "username": "agentowner", "password": "pass",
    })
    token = login_resp.json()["access_token"]

    # Create agent
    resp = await client.post(
        "/agents",
        json={"name": "MyBot"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    agent = resp.json()
    assert agent["name"] == "MyBot"
    assert "api_key" in agent  # Shown once


@pytest.mark.asyncio
async def test_create_league(client: AsyncClient):
    # Register + login + create agent
    await client.post("/users/register", json={
        "username": "commish", "email": "c@test.com", "password": "pass",
    })
    login_resp = await client.post("/users/login", json={
        "username": "commish", "password": "pass",
    })
    token = login_resp.json()["access_token"]

    agent_resp = await client.post(
        "/agents",
        json={"name": "CommishBot"},
        headers={"Authorization": f"Bearer {token}"},
    )
    api_key = agent_resp.json()["api_key"]

    # Create league using agent API key
    resp = await client.post(
        "/leagues",
        json={"name": "Test League"},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert resp.status_code == 201
    league = resp.json()
    assert league["name"] == "Test League"
    assert league["member_count"] == 1  # Commissioner auto-joined
    assert len(league["invite_code"]) > 0


@pytest.mark.asyncio
async def test_leaderboard_empty(client: AsyncClient):
    resp = await client.get("/leaderboard")
    assert resp.status_code == 200
    assert resp.json() == []
