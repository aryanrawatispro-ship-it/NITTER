"""
Webhook notification handler.
"""

import httpx
import json
import hashlib
import hmac
from typing import Dict, Optional
from datetime import datetime
from loguru import logger

from src.utils.database import get_db_context
from src.utils.models import Webhook


class WebhookHandler:
    """Handle webhook notifications."""

    @staticmethod
    async def trigger_webhook(event_type: str, data: Dict, username: Optional[str] = None):
        """
        Trigger webhooks for a specific event.

        Args:
            event_type: Type of event (new_tweet, user_update, etc.)
            data: Event data to send
            username: Optional username filter
        """
        with get_db_context() as db:
            # Find matching webhooks
            query = db.query(Webhook).filter_by(
                event_type=event_type,
                is_active=True
            )

            if username:
                # Get webhooks for this specific user or general webhooks
                webhooks = query.filter(
                    (Webhook.username == username) | (Webhook.username.is_(None))
                ).all()
            else:
                webhooks = query.filter(Webhook.username.is_(None)).all()

            # Trigger each webhook
            for webhook in webhooks:
                await WebhookHandler._send_webhook(webhook, data, db)

    @staticmethod
    async def _send_webhook(webhook: Webhook, data: Dict, db):
        """
        Send a single webhook notification.

        Args:
            webhook: Webhook model instance
            data: Data to send
            db: Database session
        """
        try:
            # Prepare payload
            payload = {
                "event_type": webhook.event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Nitter-Scraper-Webhook/1.0"
            }

            # Add custom headers if specified
            if webhook.headers:
                headers.update(webhook.headers)

            # Add signature if secret key is set
            if webhook.secret_key:
                signature = WebhookHandler._generate_signature(
                    payload,
                    webhook.secret_key
                )
                headers["X-Webhook-Signature"] = signature

            # Send webhook
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers
                )

                if response.status_code in [200, 201, 202, 204]:
                    # Success
                    webhook.last_triggered = datetime.utcnow()
                    webhook.trigger_count += 1
                    db.commit()
                    logger.info(f"Webhook triggered successfully: {webhook.url} ({response.status_code})")
                else:
                    logger.warning(f"Webhook returned non-success status: {webhook.url} ({response.status_code})")

        except httpx.TimeoutException:
            logger.error(f"Webhook timeout: {webhook.url}")
        except httpx.RequestError as e:
            logger.error(f"Webhook request error: {webhook.url} - {e}")
        except Exception as e:
            logger.error(f"Webhook error: {webhook.url} - {e}")

    @staticmethod
    def _generate_signature(payload: Dict, secret: str) -> str:
        """
        Generate HMAC signature for webhook payload.

        Args:
            payload: Payload dictionary
            secret: Secret key

        Returns:
            Hex digest of signature
        """
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    @staticmethod
    async def notify_new_tweet(tweet_data: Dict):
        """
        Notify webhooks about a new tweet.

        Args:
            tweet_data: Tweet data dictionary
        """
        username = tweet_data.get('username')
        await WebhookHandler.trigger_webhook(
            event_type='new_tweet',
            data=tweet_data,
            username=username
        )

    @staticmethod
    async def notify_user_update(user_data: Dict):
        """
        Notify webhooks about a user profile update.

        Args:
            user_data: User data dictionary
        """
        username = user_data.get('username')
        await WebhookHandler.trigger_webhook(
            event_type='user_update',
            data=user_data,
            username=username
        )

    @staticmethod
    async def notify_scrape_complete(job_data: Dict):
        """
        Notify webhooks about completed scraping job.

        Args:
            job_data: Job data dictionary
        """
        await WebhookHandler.trigger_webhook(
            event_type='scrape_complete',
            data=job_data
        )

    @staticmethod
    async def notify_scrape_failed(job_data: Dict):
        """
        Notify webhooks about failed scraping job.

        Args:
            job_data: Job data dictionary
        """
        await WebhookHandler.trigger_webhook(
            event_type='scrape_failed',
            data=job_data
        )


# Helper function to be called from Celery tasks
async def trigger_new_tweet_webhooks(tweet_data: Dict):
    """Trigger webhooks for new tweets (called from Celery tasks)."""
    await WebhookHandler.notify_new_tweet(tweet_data)


async def trigger_user_update_webhooks(user_data: Dict):
    """Trigger webhooks for user updates (called from Celery tasks)."""
    await WebhookHandler.notify_user_update(user_data)
