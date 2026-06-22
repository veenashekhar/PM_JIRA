from typing import Literal, Optional

from pydantic import BaseModel


class Card(BaseModel):
    id: str
    title: str
    details: str


class Column(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardData(BaseModel):
    columns: list[Column]
    cards: dict[str, Card]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AiKanbanRequest(BaseModel):
    username: str
    board: BoardData
    history: list[ChatMessage] = []
    message: str
    mock: bool = False


class AiKanbanResponse(BaseModel):
    response: str
    board: Optional[BoardData] = None
