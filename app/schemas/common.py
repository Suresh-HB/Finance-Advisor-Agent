from datetime import datetime
from pydantic import BaseModel


class ConversationEntry(BaseModel):
    timestamp: datetime
    user_id: int
    user_message: str
    assistant_answer: str
    analysis: dict
