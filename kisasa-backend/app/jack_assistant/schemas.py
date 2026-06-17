from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class JackMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class JackFarmerContext(BaseModel):
    location_name: Optional[str] = Field(default=None, max_length=120)
    location_latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    location_longitude: Optional[float] = Field(default=None, ge=-180, le=180)


class JackChatRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=2000)
    history: Optional[List[JackMessage]] = None
    context_text: Optional[str] = Field(default=None, max_length=12000)
    farmer_context: Optional[JackFarmerContext] = None


class JackChatResponse(BaseModel):
    assistant: str = "Jack"
    reply: str
    created_at: datetime
    source: Optional[str] = None


class JackKnowledgeDocument(BaseModel):
    title: str
    source: str


class JackKnowledgeDocumentDetail(JackKnowledgeDocument):
    content: str


class JackKnowledgeDocumentCreate(BaseModel):
    filename: str = Field(..., min_length=3, max_length=120)
    content: str = Field(..., min_length=10, max_length=50000)
