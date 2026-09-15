"""
Membership inquiry view — handles the Join IPAWAS form submission.
"""
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)


class MemberJoinView(TemplateView):
    """Renders the IPA membership application page."""
    template_name = "core/members/join.html"


class MemberPortalView(TemplateView):
    """
    Member portal landing page — redirects visitors to the real Django login.
    The old portal.html was a static stub with hardcoded demo credentials;
    this view simply renders the clean redirect page.
    """
    template_name = "core/members/portal.html"


@csrf_protect
@require_POST
@ratelimit(key="ip", rate="3/m", method="POST", block=True)
def membership_inquiry(request):
    """
    Process membership application form submission from join.html.

    Validates required fields, logs the inquiry, and sends a notification
    email to the IPAWAS contact inbox. Returns JSON so the Alpine.js form
    can show a success state without a full page reload.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"success": False, "error": "Invalid request format."}, status=400)

    # Required fields validation
    required = ["organizationName", "country", "contactName", "contactEmail"]
    missing = [f for f in required if not body.get(f, "").strip()]
    if missing:
        return JsonResponse(
            {"success": False, "error": f"Missing required fields: {', '.join(missing)}"},
            status=400,
        )

    org_name = body.get("organizationName", "").strip()
    country = body.get("country", "").strip()
    contact_name = body.get("contactName", "").strip()
    contact_email = body.get("contactEmail", "").strip()
    contact_phone = body.get("contactPhone", "").strip()
    mandate = body.get("mandate", "").strip()

    logger.info(
        "Membership inquiry received from %s (%s) — %s <%s>",
        org_name,
        country,
        contact_name,
        contact_email,
    )

    # Send notification email to IPAWAS inbox
    try:
        from core.email.services import get_system_email_service
        email_service = get_system_email_service()
        subject = f"New IPA Membership Inquiry — {org_name} ({country})"
        body_text = (
            f"A new membership inquiry has been submitted via the IPAWAS website.\n\n"
            f"Organisation: {org_name}\n"
            f"Country: {country}\n"
            f"Contact: {contact_name}\n"
            f"Email: {contact_email}\n"
            f"Phone: {contact_phone}\n\n"
            f"Mandate / Description:\n{mandate}\n\n"
            f"---\nFull submission data:\n{json.dumps(body, indent=2)}"
        )
        contact_email_addr = getattr(settings, "CONTACT_EMAIL", "infodesk@ipawas.org")
        email_service.send_plain(
            to=[contact_email_addr],
            subject=subject,
            body=body_text,
        )
    except Exception as exc:
        # Non-fatal — log but do not fail the submission
        logger.error("Failed to send membership inquiry notification email: %s", exc, exc_info=True)

    return JsonResponse({"success": True})
