import json
import os
import re
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.ai import call_openrouter, call_openrouter_chat
from app.db import db_connection, read_board, validate_board, write_board
from app.schemas import AiKanbanRequest, AiKanbanResponse, BoardData

app = FastAPI()


@app.middleware("http")
async def disable_html_cache(request: Request, call_next):
  response = await call_next(request)
  content_type = response.headers.get("content-type", "")
  # Prevent stale HTML from referencing old hashed Next.js chunks.
  if "text/html" in content_type:
    response.headers["Cache-Control"] = "no-store"
  return response


@app.get("/hello", response_class=HTMLResponse)
def hello_page() -> str:
    return """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>PM MVP</title>
  </head>
  <body>
    <main>
      <h1>Hello from FastAPI</h1>
      <p>Container and API are running.</p>
    </main>
  </body>
</html>"""


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/kanban/{username}", response_model=BoardData)
def get_kanban(username: str) -> BoardData:
  with db_connection() as conn:
    return read_board(conn, username)


@app.put("/api/kanban/{username}", response_model=BoardData)
def update_kanban(username: str, board: BoardData) -> BoardData:
  try:
    with db_connection() as conn:
      return write_board(conn, username, board)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/ai/test")
async def ai_test() -> dict:
  try:
    response = await call_openrouter("2+2")
  except RuntimeError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc
  except httpx.HTTPError as exc:
    raise HTTPException(status_code=502, detail=str(exc)) from exc

  return {"prompt": "2+2", "response": response}


AI_KANBAN_SCHEMA = {
  "name": "kanban_ai_response",
  "schema": {
    "type": "object",
    "properties": {
      "response": {"type": "string"},
      "board_update": {
        "anyOf": [
          {
            "type": "object",
            "properties": {
              "columns": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "cardIds": {
                      "type": "array",
                      "items": {"type": "string"},
                    },
                  },
                  "required": ["id", "title", "cardIds"],
                  "additionalProperties": False,
                },
              },
              "cards": {
                "type": "object",
                "additionalProperties": {
                  "type": "object",
                  "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "details": {"type": "string"},
                  },
                  "required": ["id", "title", "details"],
                  "additionalProperties": False,
                },
              },
            },
            "required": ["columns", "cards"],
            "additionalProperties": False,
          },
          {"type": "null"},
        ]
      },
    },
    "required": ["response"],
    "additionalProperties": False,
  },
  "strict": True,
}


@app.post("/api/ai/kanban", response_model=AiKanbanResponse)
async def ai_kanban(payload: AiKanbanRequest) -> AiKanbanResponse:
  try:
    validate_board(payload.board)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc

  if payload.mock or os.environ.get("PM_AI_MOCK", "").lower() == "true":
    board_dict = payload.board.model_dump()
    columns = board_dict.get("columns", [])
    cards = board_dict.get("cards", {})
    raw_message = payload.message
    message = payload.message.lower()

    def save_board(next_board: dict) -> AiKanbanResponse:
      updated_board = BoardData.model_validate(next_board)
      with db_connection() as conn:
        saved_board = write_board(conn, payload.username, updated_board)
      return AiKanbanResponse(response=mock_response, board=saved_board)

    mock_response = "Mock response"

    if "summarize" in message or "summarise" in message or "summary" in message:
      lines = []
      for column in columns:
        card_titles = [
          cards[card_id]["title"]
          for card_id in column.get("cardIds", [])
          if card_id in cards
        ]
        card_list = ", ".join(card_titles) if card_titles else "(no cards)"
        lines.append(f"{column['title']}: {card_list}")
      mock_response = "Board summary: " + " | ".join(lines)
      return AiKanbanResponse(response=mock_response, board=payload.board)

    if "add" in message and "card" in message:
      title_match = re.search(
        r"(?:title|card\s+title|heading)\s+(.+?)(?:\s+and\s+|\s+description\s+|\s+details\s+|\s+definition\s+|\s+to\s+column\s+|\s+column\s+|$)",
        raw_message,
        re.IGNORECASE,
      )
      desc_match = re.search(
        r"(?:description|details|definition)\s+(.+?)(?:\s+to\s+column\s+|\s+column\s+|$)",
        raw_message,
        re.IGNORECASE,
      )
      column_match = re.search(
        r"(?:to\s+column|column)\s+(.+)$",
        raw_message,
        re.IGNORECASE,
      )

      title = title_match.group(1).strip() if title_match else "Mock task"
      details = desc_match.group(1).strip() if desc_match else "Generated by mock assistant."

      target = columns[0] if (columns and not column_match) else None
      if column_match:
        raw_column = column_match.group(1).strip().rstrip(".!")
        column_name = re.sub(r"[^a-z0-9\s-]", "", raw_column).strip().lower()
        for column in columns:
          title_value = column.get("title", "").lower()
          if title_value == column_name:
            target = column
            break
        if target is None and column_name:
          for column in columns:
            title_value = column.get("title", "").lower()
            if column_name in title_value:
              target = column
              break
        if target is None and columns:
          target = columns[0]

      if target is None:
        return AiKanbanResponse(response="No columns available.", board=payload.board)

      next_id = f"mock-card-{len(cards) + 1}"
      cards[next_id] = {
        "id": next_id,
        "title": title,
        "details": details,
      }
      target["cardIds"] = [next_id, *target.get("cardIds", [])]
      for index, column in enumerate(columns):
        if column.get("id") == target.get("id"):
          columns[index] = target
          break
      board_dict["columns"] = columns
      board_dict["cards"] = cards
      mock_response = f"Added {title} to {target['title']}."
      return save_board(board_dict)

    if "rename" in message and columns:
      new_title = None
      match = re.search(r"rename\s+(?:column\s+)?(.+?)\s+(?:to|as)\s+(.+)", message)
      if match:
        source_phrase = match.group(1).strip()
        if source_phrase.endswith(" column"):
          source_phrase = source_phrase[: -len(" column")].strip()
        new_title = match.group(2).strip().title()
        for column in columns:
          if column.get("title", "").lower() == source_phrase.lower():
            column["title"] = new_title
            board_dict["columns"] = columns
            mock_response = f"Renamed {source_phrase} to {new_title}."
            return save_board(board_dict)
      return AiKanbanResponse(response="Could not find that column.", board=payload.board)

    if "move" in message and len(columns) > 1:
      target_column = None
      target_card_id = None

      for column in columns:
        if column.get("title", "").lower() in message:
          target_column = column
          break

      for card_id, card in cards.items():
        if card.get("title", "").lower() in message:
          target_card_id = card_id
          break

      if target_column and target_card_id:
        for column in columns:
          if target_card_id in column.get("cardIds", []):
            column["cardIds"] = [
              cid for cid in column.get("cardIds", []) if cid != target_card_id
            ]
        target_column["cardIds"] = [
          target_card_id,
          *target_column.get("cardIds", []),
        ]
        board_dict["columns"] = columns
        mock_response = (
          f"Moved {cards[target_card_id]['title']} to {target_column['title']}."
        )
        return save_board(board_dict)

      source = columns[0]
      dest = columns[1]
      if source["cardIds"]:
        card_id = source["cardIds"].pop(0)
        dest["cardIds"] = [card_id, *dest.get("cardIds", [])]
        columns[0] = source
        columns[1] = dest
        board_dict["columns"] = columns
        mock_response = "Moved the first card to the next column."
        return save_board(board_dict)
      return AiKanbanResponse(response="No cards to move.", board=payload.board)

    mock_response = "I can add cards, rename a column, move a card, or summarize the board."
    return AiKanbanResponse(response=mock_response, board=payload.board)

  history_messages = [
    {"role": message.role, "content": message.content}
    for message in payload.history
  ]
  board_json = json.dumps(payload.board.model_dump(), ensure_ascii=True)
  messages = [
    {
      "role": "system",
      "content": (
        "You are a Kanban assistant. Respond with JSON that matches the schema. "
        "If no board change is needed, set board_update to null."
      ),
    },
    *history_messages,
    {
      "role": "user",
      "content": f"Board JSON: {board_json}\nUser request: {payload.message}",
    },
  ]

  try:
    content = await call_openrouter_chat(
      messages=messages,
      response_format={"type": "json_schema", "json_schema": AI_KANBAN_SCHEMA},
    )
    parsed = json.loads(content)
  except json.JSONDecodeError as exc:
    raise HTTPException(status_code=502, detail="Invalid AI response format") from exc
  except RuntimeError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc
  except httpx.HTTPError as exc:
    raise HTTPException(status_code=502, detail=str(exc)) from exc

  response_text = parsed.get("response", "")
  board_update = parsed.get("board_update")

  if board_update is not None:
    try:
      updated_board = BoardData.model_validate(board_update)
      with db_connection() as conn:
        saved_board = write_board(conn, payload.username, updated_board)
    except ValueError as exc:
      raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AiKanbanResponse(response=response_text, board=saved_board)

  return AiKanbanResponse(response=response_text, board=payload.board)


static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
