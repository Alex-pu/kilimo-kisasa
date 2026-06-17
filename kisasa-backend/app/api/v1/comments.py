from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.comment import Comment
from app.models.issue import Issue
from app.models.user import User, UserRole
from app.schemas.comment_schema import CommentCreate, CommentResponse
from app.utils.dependencies import get_current_user
from app.jack_assistant.service import create_reply_if_tagged

router = APIRouter(prefix="/issues/{issue_id}/comments", tags=["comments"])


def require_parent_comment_in_issue(
    db: Session,
    issue_id: str,
    parent_comment_id,
) -> None:
    if parent_comment_id is None:
        return

    parent = (
        db.query(Comment.id)
        .filter(Comment.id == parent_comment_id, Comment.issue_id == issue_id)
        .first()
    )
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent comment must belong to this issue",
        )


@router.post("/", response_model=CommentResponse)
async def create_comment(
    issue_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a comment to an issue."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )

    require_parent_comment_in_issue(db, issue.id, comment_data.parent_comment_id)
    comment = Comment(
        issue_id=issue.id,
        author_id=current_user.id,
        **comment_data.model_dump(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    create_reply_if_tagged(db, issue, comment)
    return comment


@router.get("/", response_model=List[CommentResponse])
async def list_comments(
    issue_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List comments for an issue."""
    issue = db.query(Issue.id).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )

    return (
        db.query(Comment)
        .filter(Comment.issue_id == issue_id)
        .order_by(Comment.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.delete("/{comment_id}")
async def delete_comment(
    issue_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a comment as its author or an admin."""
    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id, Comment.issue_id == issue_id)
        .first()
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only comment author or admin can delete it",
        )

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}
