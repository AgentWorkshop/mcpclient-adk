import pytest
import httpx
from fastapi.testclient import TestClient # While httpx.AsyncClient is good for async, TestClient is often simpler for FastAPI sync tests if possible, but main app is async. Let's use AsyncClient as FastAPI supports it well.

# Import the FastAPI app instance from main.py
from main import app

@pytest.mark.asyncio
async def test_read_root():
    # Use httpx.AsyncClient to make requests to the app
    # The app must be run within an lifespan manager for proper startup/shutdown events if it has them.
    # For simple apps like this one, direct client usage is often fine.
    async with httpx.AsyncClient(app=app, base_url="http://127.0.0.1:8000") as client:
        response = await client.get("/")
    assert response.status_code == 200
    # We could also check for some content from index.html if needed,
    # but status code 200 is a good basic check.
    # For example: assert "ADK MCP example" in response.text # Assuming this title is in index.html
