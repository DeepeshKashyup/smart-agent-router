"""Tests for API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_check(client):
    """Health endpoint returns 200 with model info."""
    async with client as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "models" in data
    assert "large" in data["models"]
    assert "small" in data["models"]


@pytest.mark.asyncio
async def test_query_empty_body(client):
    """Empty query returns 422 validation error."""
    async with client as ac:
        response = await ac.post("/api/v1/query", json={"query": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cost_summary_empty(client):
    """Cost summary returns zeros when no queries processed."""
    async with client as ac:
        response = await ac.get("/api/v1/costs")
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 0
    assert data["total_cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_cost_reset(client):
    """Cost reset endpoint returns success."""
    async with client as ac:
        response = await ac.post("/api/v1/costs/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "reset"
