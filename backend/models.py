from pydantic import BaseModel
from typing import Optional


class CaseCreate(BaseModel):
    name: str


class Case(BaseModel):
    id: str
    name: str
    document_count: int
