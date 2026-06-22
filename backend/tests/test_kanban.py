import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_kanban_returns_default_board(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "kanban.db"
    monkeypatch.setenv("PM_DB_PATH", str(db_path))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/kanban/user")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["columns"]) == 5
    assert payload["columns"][0]["title"] == "Backlog"
    assert len(payload["cards"]) >= 1


@pytest.mark.asyncio
async def test_put_kanban_persists_changes(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "kanban.db"
    monkeypatch.setenv("PM_DB_PATH", str(db_path))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/kanban/user")
        payload = response.json()

        payload["columns"][0]["title"] = "Renamed"
        payload["cards"]["card-1"]["title"] = "Updated title"
        payload["cards"]["card-1"]["details"] = "Updated details"

        put_response = await client.put("/api/kanban/user", json=payload)
        assert put_response.status_code == 200

        get_response = await client.get("/api/kanban/user")

    updated = get_response.json()
    assert updated["columns"][0]["title"] == "Renamed"
    assert updated["cards"]["card-1"]["title"] == "Updated title"
