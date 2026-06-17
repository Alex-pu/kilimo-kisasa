from fastapi import APIRouter, Depends, HTTPException, status

from app.jack_assistant.knowledge_base import (
    delete_document,
    get_document,
    list_documents,
    save_document,
)
from app.jack_assistant.schemas import (
    JackChatRequest,
    JackChatResponse,
    JackKnowledgeDocumentCreate,
    JackKnowledgeDocumentDetail,
    JackKnowledgeDocument,
)
from app.jack_assistant.service import chat
from app.models.user import User, UserRole
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/jack", tags=["jack-assistant"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage Jack knowledge",
        )
    return current_user


@router.post("/chat", response_model=JackChatResponse)
async def chat_with_jack(payload: JackChatRequest):
    """Ask Jack a farm question."""
    history = [message.model_dump() for message in payload.history or []]
    farmer_context = payload.farmer_context.model_dump() if payload.farmer_context else None
    return chat(
        payload.prompt,
        context_text=payload.context_text,
        history=history,
        farmer_context=farmer_context,
    )


@router.get("/knowledge", response_model=list[JackKnowledgeDocument])
async def list_jack_knowledge():
    """List local documents Jack can use for answers."""
    return list_documents()


@router.get("/knowledge/{filename}", response_model=JackKnowledgeDocumentDetail)
async def get_jack_knowledge_document(
    filename: str,
    _: User = Depends(require_admin),
):
    """Read a Jack knowledge document as an admin."""
    document = get_document(filename)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jack knowledge document not found",
        )
    return document


@router.post("/knowledge", response_model=JackKnowledgeDocumentDetail)
async def save_jack_knowledge_document(
    payload: JackKnowledgeDocumentCreate,
    _: User = Depends(require_admin),
):
    """Create or update a Jack knowledge document as an admin."""
    try:
        return save_document(payload.filename, payload.content)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("/knowledge/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_jack_knowledge_document(
    filename: str,
    _: User = Depends(require_admin),
):
    """Delete a Jack knowledge document as an admin."""
    if not delete_document(filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jack knowledge document not found",
        )
