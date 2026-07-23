from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    message: str = Field(..., min_length=2)


class UploadCSVRequest(BaseModel):
    file_type: str
