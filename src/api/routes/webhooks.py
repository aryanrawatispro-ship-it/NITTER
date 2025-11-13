"""
Webhook management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel, HttpUrl

from src.utils.database import get_db
from src.utils.models import Webhook

router = APIRouter()


class WebhookCreate(BaseModel):
    url: HttpUrl
    event_type: str  # new_tweet, user_update, etc.
    username: Optional[str] = None  # Specific user to track
    secret_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


class WebhookResponse(BaseModel):
    id: int
    url: str
    event_type: str
    username: Optional[str]
    is_active: bool
    trigger_count: int
    last_triggered: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", status_code=201)
async def create_webhook(webhook: WebhookCreate, db: Session = Depends(get_db)):
    """Create a new webhook."""
    new_webhook = Webhook(
        url=str(webhook.url),
        event_type=webhook.event_type,
        username=webhook.username,
        secret_key=webhook.secret_key,
        headers=webhook.headers,
        is_active=True
    )

    db.add(new_webhook)
    db.commit()
    db.refresh(new_webhook)

    return {
        "id": new_webhook.id,
        "message": "Webhook created successfully",
        "url": new_webhook.url,
        "event_type": new_webhook.event_type
    }


@router.get("/", response_model=List[WebhookResponse])
async def get_webhooks(
    event_type: Optional[str] = None,
    username: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all webhooks with optional filters."""
    query = db.query(Webhook)

    if event_type:
        query = query.filter_by(event_type=event_type)

    if username:
        query = query.filter_by(username=username)

    webhooks = query.all()

    result = []
    for webhook in webhooks:
        result.append({
            "id": webhook.id,
            "url": webhook.url,
            "event_type": webhook.event_type,
            "username": webhook.username,
            "is_active": webhook.is_active,
            "trigger_count": webhook.trigger_count,
            "last_triggered": webhook.last_triggered.isoformat() if webhook.last_triggered else None
        })

    return result


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Get a specific webhook."""
    webhook = db.query(Webhook).filter_by(id=webhook_id).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {
        "id": webhook.id,
        "url": webhook.url,
        "event_type": webhook.event_type,
        "username": webhook.username,
        "is_active": webhook.is_active,
        "trigger_count": webhook.trigger_count,
        "last_triggered": webhook.last_triggered.isoformat() if webhook.last_triggered else None
    }


@router.patch("/{webhook_id}/toggle")
async def toggle_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Toggle webhook active status."""
    webhook = db.query(Webhook).filter_by(id=webhook_id).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    webhook.is_active = not webhook.is_active
    db.commit()

    return {
        "id": webhook_id,
        "is_active": webhook.is_active,
        "message": f"Webhook {'activated' if webhook.is_active else 'deactivated'}"
    }


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Delete a webhook."""
    webhook = db.query(Webhook).filter_by(id=webhook_id).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(webhook)
    db.commit()

    return {"message": "Webhook deleted successfully"}
