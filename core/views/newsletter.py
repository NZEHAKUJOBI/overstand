"""Newsletter subscription endpoint."""

import logging

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from ipware import get_client_ip

logger = logging.getLogger(__name__)


@require_POST
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def newsletter_subscribe(request):
    """Handle newsletter subscription via AJAX POST."""
    from core.models import NewsletterSubscriber

    email = request.POST.get("email", "").strip().lower()
    if not email or len(email) > 254:
        return JsonResponse({"success": False, "error": "A valid email address is required."}, status=400)

    ip, _ = get_client_ip(request)

    try:
        _, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={"ip_address": ip, "is_active": True},
        )
        if created:
            from core.email.services import MailjetService
            MailjetService().add_to_newsletter_list(email)
            return JsonResponse({"success": True, "message": "You've successfully subscribed!"})
        return JsonResponse({"success": True, "message": "You're already on our list."})
    except Exception as e:
        logger.exception("newsletter_subscribe: database error for email %s: %s", email, e)
        return JsonResponse(
            {"success": False, "error": "Something went wrong. Please try again."}, status=500
        )
