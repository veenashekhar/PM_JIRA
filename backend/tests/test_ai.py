import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_ai_test_endpoint(monkeypatch) -> None:
    async def fake_call(prompt: str) -> str:
        assert prompt == "2+2"
        return "4"

    monkeypatch.setattr("app.main.call_openrouter", fake_call)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/ai/test")

    assert response.status_code == 200
    assert response.json() == {"prompt": "2+2", "response": "4"}


@pytest.mark.asyncio
async def test_ai_kanban_endpoint_updates_board(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "kanban.db"
    monkeypatch.setenv("PM_DB_PATH", str(db_path))

    async def fake_call(messages: list[dict], response_format: dict) -> str:
        update = {
            "columns": [
                {"id": "col-backlog", "title": "Inbox", "cardIds": ["card-1"]},
                {"id": "col-discovery", "title": "Discovery", "cardIds": []},
                {"id": "col-progress", "title": "In Progress", "cardIds": []},
                {"id": "col-review", "title": "Review", "cardIds": []},
                {"id": "col-done", "title": "Done", "cardIds": []},
            ],
            "cards": {
                "card-1": {
                    "id": "card-1",
                    "title": "Updated",
                    "details": "Updated details",
                }
            },
        }
        return json.dumps({"response": "Updated the board.", "board_update": update})

    monkeypatch.setattr("app.main.call_openrouter_chat", fake_call)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        initial = await client.get("/api/kanban/user")
        payload = {
            "username": "user",
            "board": initial.json(),
            "history": [],
            "message": "Rename backlog",
        }
        response = await client.post("/api/ai/kanban", json=payload)
        assert response.status_code == 200

        updated = await client.get("/api/kanban/user")

    body = response.json()
    assert body["response"] == "Updated the board."
    assert body["board"]["columns"][0]["title"] == "Inbox"
    assert updated.json()["columns"][0]["title"] == "Inbox"


@pytest.mark.asyncio
async def test_ai_kanban_rejects_invalid_output(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "kanban.db"
    monkeypatch.setenv("PM_DB_PATH", str(db_path))

    async def fake_call(messages: list[dict], response_format: dict) -> str:
        return "not-json"

    monkeypatch.setattr("app.main.call_openrouter_chat", fake_call)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        initial = await client.get("/api/kanban/user")
        payload = {
            "username": "user",
            "board": initial.json(),
            "history": [],
            "message": "Anything",
        }
        response = await client.post("/api/ai/kanban", json=payload)

    assert response.status_code == 502
