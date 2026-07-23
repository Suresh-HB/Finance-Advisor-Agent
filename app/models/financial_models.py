from pydantic import BaseModel, Field


class User(BaseModel):
    user_id: int = Field(..., gt=0)
    name: str
    age: int = Field(..., gt=0)
    city: str


class Transaction(BaseModel):
    transaction_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    date: str
    type: str
    category: str
    description: str
    amount: float = Field(..., ge=0)


class Budget(BaseModel):
    budget_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    month: str
    budget_limit: float = Field(..., ge=0)
