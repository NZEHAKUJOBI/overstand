"""
Onboarding Public Views — IPAWAS Platform

OnboardingFormView    : public self-service form (rate-limited, honeypot, dedup)
OnboardingSuccessView : post-submission confirmation page
"""

import logging

from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django_ratelimit.decorators import ratelimit

from accounts.models import User
from invitations.models import Invitation
from onboarding.emails import notify_admins_new_request
from onboarding.forms import OnboardingRequestForm
from onboarding.models import OnboardingRequest, OnboardingSession

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    """Extract real client IP (handles Heroku / reverse proxy headers)."""
    try:
        from ipware import get_client_ip
        ip, _ = get_client_ip(request)
        return ip
    except Exception:
        return request.META.get("REMOTE_ADDR")


@method_decorator(
    ratelimit(key="ip", rate="5/h", method="POST", block=False),
    name="post",
)
class OnboardingFormView(View):
    """
    Public self-service onboarding form reachable via the QR code.

    GET  → render the trilingual form (if session is open)
    POST → validate, dedup-check, save OnboardingRequest, notify admins, redirect to success

    Security layers (in order of execution):
      1. Session validity — UUID token must exist, is_active=True, not expired, under cap
      2. Rate limit — 5 POST submissions per IP per hour (django-ratelimit)
      3. Honeypot — hidden `website` field; if filled → silently reject
      4. Form validation — standard Django form validation
      5. Email dedup — no existing active user OR pending invitation OR pending request
         for this email; if any found → friendly error, no duplicate record
    """

    template_name = "onboarding/form.html"
    invalid_template = "onboarding/invalid_session.html"
    rate_limited_template = "onboarding/rate_limited.html"

    def _get_session(self, session_token):
        return get_object_or_404(OnboardingSession, slug_token=session_token)

    def get(self, request, session_token):
        session = self._get_session(session_token)
        if not session.is_open:
            return render(
                request,
                self.invalid_template,
                {"session": session, "reason": session.closed_reason},
            )
        form = OnboardingRequestForm()
        return render(request, self.template_name, {"form": form, "session": session})

    def post(self, request, session_token):
        session = self._get_session(session_token)

        # 1 ── Session gate (re-check on POST, a race condition could close it)
        if not session.is_open:
            return render(
                request,
                self.invalid_template,
                {"session": session, "reason": session.closed_reason},
            )

        # 2 ── Rate limit
        if getattr(request, "limited", False):
            return render(request, self.rate_limited_template, status=429)

        form = OnboardingRequestForm(request.POST)

        # 3 ── Honeypot + form validation (honeypot check is inside form.clean())
        if not form.is_valid():
            # If the only error is the honeypot, return a blank 200 to confuse bots
            if "website" in form.data and form.data["website"]:
                logger.warning(
                    "Honeypot triggered from IP %s", _get_client_ip(request)
                )
                return render(request, "onboarding/success.html", {"session": session})
            return render(request, self.template_name, {"form": form, "session": session})

        cd = form.cleaned_data
        email = cd["email"]
        member_state = cd["member_state"]

        # 4 ── Email dedup checks
        error = self._check_email_conflicts(email, member_state)
        if error:
            form.add_error("email", error)
            return render(request, self.template_name, {"form": form, "session": session})

        # 5 ── Create the OnboardingRequest
        onboarding_request = OnboardingRequest.objects.create(
            session=session,
            full_name=cd["full_name"],
            email=email,
            member_state=member_state,
            job_title=cd["job_title"],
            requested_role=cd["requested_role"],
            organization=cd.get("organization", ""),
            phone=cd.get("phone", ""),
            personal_email=cd.get("personal_email", ""),
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )

        # 6 ── Notify HQ admins (fire-and-forget — don't crash if email fails)
        try:
            review_url = request.build_absolute_uri(
                f"/dashboard/hq/onboarding/requests/{onboarding_request.pk}/"
            )
            notify_admins_new_request(onboarding_request, review_url)
        except Exception as exc:
            logger.error("Admin notification failed for request %d: %s", onboarding_request.pk, exc)

        logger.info(
            "OnboardingRequest #%d created: %s → %s (%s)",
            onboarding_request.pk,
            email,
            member_state.ipa_acronym,
            _get_client_ip(request),
        )

        return redirect("onboarding:success", session_token=session_token)

    @staticmethod
    def _check_email_conflicts(email, member_state):
        """
        Return an error string if the email cannot be used, else None.

        Checks (in order):
          a) Email already has an active user account on the platform
          a2) Email has an inactive user record awaiting invitation acceptance
              (created by UserInvitationService) — prevents a downstream
              IntegrityError when a second invitation path tries to create the
              same email as an active user.
          b) Email already has a pending invitation for this member state
          c) Email already has a pending onboarding request (anywhere)
        """
        # a) Active account already exists
        if User.objects.filter(email=email, is_active=True).exists():
            return (
                "This email address already has an active account on the IPAWAS platform. "
                "If you need help accessing your account, please contact the IPAWAS Secretariat."
            )

        # a2) Inactive user record — a personal invitation link was already sent
        if User.objects.filter(email=email, is_active=False).exists():
            return (
                "An invitation has already been sent to this email address. "
                "Please check your inbox (including spam) for the invitation email. "
                "If you need help, contact the IPAWAS Secretariat."
            )

        # b) Pending invitation already exists for this email+member_state
        if Invitation.objects.filter(
            email=email, member_state=member_state, status="pending"
        ).exists():
            return (
                "An invitation has already been sent to this email address for your member state. "
                "Please check your inbox (including spam) for the invitation email."
            )

        # c) Pending onboarding request already exists for this email
        if OnboardingRequest.objects.filter(email=email, status="pending").exists():
            return (
                "A request for this email address is already under review. "
                "You will receive an email once your request has been processed."
            )

        return None


class OnboardingSuccessView(View):
    """
    Shown after a successful form submission.
    Deliberately shows no data from the submission — prevents information leakage.
    """

    def get(self, request, session_token):
        # Validate session exists (prevents 404 on bad token)
        session = get_object_or_404(OnboardingSession, slug_token=session_token)
        return render(request, "onboarding/success.html", {"session": session})



class ShortLinkView(View):
    """Resolve a short code to the full session UUID URL and redirect.

    Uses a permanent (301) redirect because the short_code → slug_token
    mapping is immutable once created — caching it in browsers and bots
    saves a round-trip on every subsequent scan.
    """

    def get(self, request, short_code):
        session = get_object_or_404(OnboardingSession, short_code=short_code.upper())
        from django.urls import reverse
        return redirect(
            reverse("onboarding:form", kwargs={"session_token": session.slug_token}),
            permanent=True,
        )
