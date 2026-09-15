"""
Training invitation email sender.

Called automatically when a TrainingInvitation is saved with status=pending
(via signal in signals.py).
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _


def send_training_invitation(invitation):
    """
    Send the training invitation email to the participant.
    Returns True on success, False on failure.
    """
    try:
        # Build the unique assessment URL
        token = str(invitation.token)
        # Build absolute URL — use settings.SITE_URL or fallback
        site_url = getattr(settings, "SITE_URL", "https://ipawas.org")
        # The public assessment URL uses the token, no language prefix needed
        # (the page itself has JS language switcher)
        assess_path = reverse("training:assess", kwargs={"token": token})
        assess_url = f"{site_url}{assess_path}"

        context = {
            "invitation": invitation,
            "session": invitation.session,
            "assess_url": assess_url,
            "site_url": site_url,
        }

        subject = _("IPAWAS Training – You're Invited: %(title)s") % {
            "title": invitation.session.title
        }

        text_body = render_to_string("training/email/invitation.txt", context)
        html_body = render_to_string("training/email/invitation.html", context)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ipawas.org")

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[invitation.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        invitation.mark_sent()
        return True

    except Exception as exc:  # noqa: BLE001
        # Log but don't raise — dashboard shows "Failed" status
        import logging
        logging.getLogger(__name__).error(
            "Failed to send training invitation to %s: %s", invitation.email, exc
        )
        return False
