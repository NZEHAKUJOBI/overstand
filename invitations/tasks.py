"""
Celery tasks for the invitations app.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="invitations.tasks.cleanup_expired_invitations")
def cleanup_expired_invitations():
    """
    Mark all pending invitations that have passed their expiry date as 'expired'.
    Runs every 6 hours via Celery Beat.
    """
    from invitations.models import Invitation

    count = Invitation.objects.cleanup_expired()
    logger.info("cleanup_expired_invitations: marked %d invitation(s) as expired", count)
    return count
