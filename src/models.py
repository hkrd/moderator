from pydantic import BaseModel
from enum import Enum


class Category(str, Enum):
    sexual = "sexual"
    hate = "hate"
    harassment = "harassment"
    self_harm = "self-harm"
    violence = "violence"


class ModerationRequest(BaseModel):
    message_id: str
    content: str
    categories: list[Category]


class ModerationResponse(BaseModel):
    message_id: str
    content: str
    category_scores: dict[Category, float]
