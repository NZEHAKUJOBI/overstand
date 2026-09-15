"""
Celery tasks for the opportunities app.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="opportunities.tasks.send_expiry_reminders")
def send_expiry_reminders():
    """
    Send reminder notifications for opportunities that have been sitting in
    draft status for more than 30 days without being published.
    Runs daily via Celery Beat.
    """
    from opportunities.models import InvestmentOpportunity

    cutoff = timezone.now() - timedelta(days=30)
    stale_drafts = InvestmentOpportunity.objects.filter(
        status="draft",
        created_at__lte=cutoff,
    ).select_related("member_state")

    count = stale_drafts.count()
    if not count:
        return 0

    logger.info(
        "send_expiry_reminders: %d stale draft opportunity/ies found (>30 days unpublished)",
        count,
    )

    from django.conf import settings
    from django.core.mail import send_mail

    # Group stale drafts by member state so each IPA gets a single digest email
    from collections import defaultdict

    grouped: dict = defaultdict(list)
    for opp in stale_drafts:
        grouped[opp.member_state].append(opp)

    sent = 0
    for member_state, opps in grouped.items():
        recipient = getattr(member_state, "contact_email", None)
        if not recipient:
            continue

        lines = "\n".join(
            f"  • {opp.title} (created {opp.created_at.strftime('%Y-%m-%d')})"
            for opp in opps
        )
        try:
            send_mail(
                subject=f"[IPAWAS] {len(opps)} opportunity draft(s) pending publication — {member_state.ipa_full_name}",
                message=(
                    f"Dear {member_state.ipa_full_name} team,\n\n"
                    f"The following investment opportunities have been in draft status for more than 30 days "
                    f"without being published. Please review and publish or update them:\n\n"
                    f"{lines}\n\n"
                    f"Log in to your dashboard to manage these opportunities.\n\n"
                    f"This is an automated reminder from the IPAWAS platform."
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ipawas.org"),
                recipient_list=[recipient],
                fail_silently=True,
            )
            sent += 1
        except Exception:
            logger.exception(
                "send_expiry_reminders: failed to send email to %s", recipient
            )

    logger.info("send_expiry_reminders: sent %d digest email(s)", sent)
    return count
