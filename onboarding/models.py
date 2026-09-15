"""
Onboarding Models — IPAWAS Platform

Two-stage secure self-service onboarding:
  1. Admin creates an OnboardingSession → generates one QR code
  2. Attendee scans QR → fills form → creates OnboardingRequest (status=pending)
  3. HQ admin reviews → approves (fires invitation email) or rejects

Security design:
  - Session token in URL (UUID v4) — unguessable, admin-deactivatable instantly
  - Submission ≠ access: every request needs manual HQ approval
  - One pending request per email (DB constraint)
  - IP + user-agent captured for every submission
  - Invitation is single-use and expires in 7 days (existing Invitation model)
"""

import secrets
import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


_SHORTCODE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def _generate_short_code():
    return "".join(secrets.choice(_SHORTCODE_CHARS) for _ in range(6))


ROLE_CHOICES = [
    ("ipa_director", _("IPA Director")),
    ("ipa_manager", _("IPA Manager")),
    ("ipa_officer", _("IPA Officer")),
    ("ipa_data_entry", _("IPA Data Entry")),
    ("ipa_analyst", _("IPA Analyst")),
]


class OnboardingSession(models.Model):
    """
    Represents a single QR-code campaign (e.g. 'May 2026 Training — Accra').

    One session = one QR code = one public URL.
    Admin can:
      - Deactivate instantly (blocks new submissions, URL shows 'closed')
      - Set an expiry date (auto-closes after date)
      - Set a submission cap (auto-closes after N accepted submissions)

    Old sessions remain in DB for audit; only is_active controls the gate.
    """

    label = models.CharField(
        max_length=200,
        help_text=_("Internal label, e.g. 'May 2026 Training — Accra'"),
    )
    slug_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text=_("UUID embedded in the public URL; unguessable."),
    )
    short_code = models.CharField(
        max_length=8,
        unique=True,
        default=_generate_short_code,
        editable=False,
        help_text=_("6-char short code for the friendly /join/<code>/ URL."),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_(
            "Uncheck to instantly invalidate the QR code. "
            "Existing requests are preserved for review."
        ),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="onboarding_sessions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Optional hard expiry. Leave blank for no automatic expiry."),
    )
    max_submissions = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_(
            "Optional cap on total approved+pending submissions before auto-close. "
            "Leave blank for unlimited."
        ),
    )
    notes = models.TextField(
        blank=True,
        help_text=_("Internal admin notes (not shown publicly)."),
    )

    class Meta:
        verbose_name = _("Onboarding Session")
        verbose_name_plural = _("Onboarding Sessions")
        ordering = ["-created_at"]

    def __str__(self):
        status = "ACTIVE" if self.is_open else "CLOSED"
        return f"[{status}] {self.label}"

    @property
    def is_open(self):
        """True only if the session is fully accepting submissions."""
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.max_submissions is not None:
            live_count = self.requests.filter(
                status__in=["pending", "approved"]
            ).count()
            if live_count >= self.max_submissions:
                return False
        return True

    @property
    def closed_reason(self):
        """Human-readable reason why session is closed (for the invalid_session template)."""
        if not self.is_active:
            return "deactivated"
        if self.expires_at and timezone.now() > self.expires_at:
            return "expired"
        if self.max_submissions is not None:
            live_count = self.requests.filter(status__in=["pending", "approved"]).count()
            if live_count >= self.max_submissions:
                return "capacity_reached"
        return None

    @property
    def pending_count(self):
        return self.requests.filter(status="pending").count()

    @property
    def approved_count(self):
        return self.requests.filter(status="approved").count()

    @property
    def rejected_count(self):
        return self.requests.filter(status="rejected").count()

    @property
    def total_count(self):
        return self.requests.count()

    def get_public_url(self):
        return reverse("onboarding_join", kwargs={"short_code": self.short_code})

    def get_qr_api_url(self, request=None):
        """Return api.qrserver.com URL for this session's QR code."""
        path = self.get_public_url()
        if request:
            abs_url = request.build_absolute_uri(path)
        else:
            domain = getattr(settings, "SITE_DOMAIN", "https://ipawas-d3bdd7a178d1.herokuapp.com")
            abs_url = f"{domain.rstrip('/')}{path}"
        return (
            f"https://api.qrserver.com/v1/create-qr-code/"
            f"?size=400x400&color=1b7a4c&bgcolor=ffffff&qzone=2&data={abs_url}"
        )


class OnboardingRequest(models.Model):
    """
    A self-submitted onboarding request from a prospective IPA staff member.

    Lifecycle:
      pending  → (admin approves) → approved  [Invitation created & emailed]
               → (admin rejects)  → rejected  [Optional rejection email]

    Security notes:
      - DB constraint: only ONE pending request per email at a time
      - IP address logged for every submission
      - Even approved requests need the invitee to click a separate invitation
        link in their email and complete account registration — two separate steps
    """

    STATUS_CHOICES = [
        ("pending", _("Pending Review")),
        ("approved", _("Approved — Invitation Sent")),
        ("rejected", _("Rejected")),
    ]

    session = models.ForeignKey(
        OnboardingSession,
        on_delete=models.PROTECT,
        related_name="requests",
        help_text=_("Which QR session this request came through."),
    )

    # ── Applicant info (self-reported) ─────────────────────────────────────
    full_name = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    member_state = models.ForeignKey(
        "members.MemberStateIPA",
        on_delete=models.PROTECT,
        related_name="onboarding_requests",
    )
    job_title = models.CharField(max_length=200)
    requested_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    organization = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("IPA / ministry name (optional, often same as member state IPA)."),
    )
    phone = models.CharField(max_length=30, blank=True)
    personal_email = models.EmailField(
        blank=True,
        help_text=_("Personal email address (optional, in case work email changes)."),
    )

    # ── Status ─────────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )

    # ── Admin review ───────────────────────────────────────────────────────
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_onboarding_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(
        blank=True,
        help_text=_("Reason shown to the applicant when rejected (optional)."),
    )
    admin_notes = models.TextField(
        blank=True,
        help_text=_("Internal notes — not sent to the applicant."),
    )

    # ── Linked invitation (set on approval) ────────────────────────────────
    invitation = models.OneToOneField(
        "invitations.Invitation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarding_request",
    )

    # ── Security / audit ───────────────────────────────────────────────────
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_("IP address at time of submission."),
    )
    user_agent = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Onboarding Request")
        verbose_name_plural = _("Onboarding Requests")
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["status", "submitted_at"]),
            models.Index(fields=["email", "status"]),
        ]
        constraints = [
            # Prevent the same email from flooding with multiple pending requests.
            # They must wait for admin to process their first one.
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(status="pending"),
                name="unique_pending_onboarding_per_email",
            )
        ]

    def __str__(self):
        return (
            f"{self.full_name} ({self.email}) → "
            f"{self.member_state.ipa_acronym} [{self.get_status_display()}]"
        )

    @property
    def is_pending(self):
        return self.status == "pending"

    @property
    def is_approved(self):
        return self.status == "approved"

    @property
    def is_rejected(self):
        return self.status == "rejected"

    def get_status_badge_class(self):
        return {
            "pending": "warning",
            "approved": "success",
            "rejected": "danger",
        }.get(self.status, "secondary")
