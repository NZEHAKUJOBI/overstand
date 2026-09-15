"""Sitewide template context processors."""

from django.conf import settings
from django.utils.translation import get_language


def social_urls(request):
    """Inject social media URLs into every template context."""
    return {
        "SOCIAL_LINKEDIN": getattr(settings, "SOCIAL_LINKEDIN", ""),
        "SOCIAL_TWITTER": getattr(settings, "SOCIAL_TWITTER", ""),
        "SOCIAL_FACEBOOK": getattr(settings, "SOCIAL_FACEBOOK", ""),
        "SOCIAL_YOUTUBE": getattr(settings, "SOCIAL_YOUTUBE", ""),
        "SOCIAL_INSTAGRAM": getattr(settings, "SOCIAL_INSTAGRAM", ""),
    }


def seo(request):
    """
    Inject canonical URL and hreflang alternate links for every public page.

    canonical_url        — absolute URL of the current page in the active language
    hreflang_alternates  — list of (lang_code, absolute_url) for <link rel="alternate">
    hreflang_default_url — absolute URL of the English (x-default) version
    """
    lang = get_language() or settings.LANGUAGE_CODE
    path = request.path

    alternates = []
    default_url = ""
    for lang_code, _ in settings.LANGUAGES:
        # Swap the active language prefix for the target one
        if path.startswith(f"/{lang}/"):
            alt_path = f"/{lang_code}/{path[len(lang) + 2:]}"
        else:
            alt_path = path
        abs_url = request.build_absolute_uri(alt_path)
        alternates.append((lang_code, abs_url))
        if lang_code == settings.LANGUAGE_CODE:
            default_url = abs_url

    return {
        "canonical_url": request.build_absolute_uri(path),
        "hreflang_alternates": alternates,
        "hreflang_default_url": default_url,
    }


def dashboard_badges(request):
    """
    Inject pending-count badges into dashboard templates for authenticated HQ admins.
    Two cheap COUNT queries, only executed when user is an ipawas_admin.
    """
    if not request.user.is_authenticated:
        return {}
    if getattr(request.user, "user_type", "") != "ipawas_admin":
        return {}
    try:
        from invitations.models import Invitation
        from onboarding.models import OnboardingRequest
        from feedback.models import Feedback
        return {
            "pending_invitations_count": Invitation.objects.filter(status="pending").count(),
            "pending_onboarding_count": OnboardingRequest.objects.filter(status="pending").count(),
            "unreviewed_feedback_count": Feedback.objects.filter(status="new").count(),
        }
    except Exception:
        return {}
