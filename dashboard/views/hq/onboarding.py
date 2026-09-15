"""
HQ Admin Onboarding Views — IPAWAS Platform

Manage onboarding QR sessions and review/approve/reject incoming requests.
All views require user_type='ipawas_admin'.

Views:
  OnboardingIndexView         — dashboard overview (sessions + pending count)
  OnboardingSessionCreateView — create a new QR session
  OnboardingSessionQRView     — display/print the QR code for a session
  OnboardingSessionToggleView — activate / deactivate a session
  OnboardingRequestListView   — list all requests, filterable by status
  OnboardingRequestDetailView — view a single request
  OnboardingApproveView       — approve → create Invitation → send email
  OnboardingRejectView        — reject (with optional email to applicant)
"""

import logging
import urllib.request as _urllib_request

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from core.email.services import get_invitation_email_service
from invitations.models import Invitation
from onboarding.emails import notify_admins_new_request, send_rejection_email
from onboarding.forms import OnboardingRejectForm, OnboardingSessionForm
from onboarding.models import OnboardingRequest, OnboardingSession

logger = logging.getLogger(__name__)


class HQAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict view to ipawas_admin users only."""

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and getattr(self.request.user, "user_type", "") == "ipawas_admin"
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect("accounts:login")
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied


# ────────────────────────────────────────────────────────────────────────────
# Sessions
# ────────────────────────────────────────────────────────────────────────────

class OnboardingIndexView(HQAdminRequiredMixin, View):
    """Overview: active sessions + total pending requests."""

    def get(self, request):
        sessions = OnboardingSession.objects.prefetch_related("requests").order_by("-created_at")
        pending_total = OnboardingRequest.objects.filter(status="pending").count()
        return render(request, "dashboard/hq_admin/onboarding/index.html", {
            "sessions": sessions,
            "pending_total": pending_total,
        })


class OnboardingSessionCreateView(HQAdminRequiredMixin, View):
    """Create a new QR onboarding session."""

    def get(self, request):
        form = OnboardingSessionForm()
        return render(request, "dashboard/hq_admin/onboarding/session_create.html", {"form": form})

    def post(self, request):
        form = OnboardingSessionForm(request.POST)
        if not form.is_valid():
            return render(
                request, "dashboard/hq_admin/onboarding/session_create.html", {"form": form}
            )

        cd = form.cleaned_data
        session = OnboardingSession.objects.create(
            label=cd["label"],
            expires_at=cd.get("expires_at"),
            max_submissions=cd.get("max_submissions"),
            notes=cd.get("notes", ""),
            created_by=request.user,
        )
        messages.success(request, f"QR session '{session.label}' created successfully.")
        return redirect("dashboard:hq:onboarding:session_qr", pk=session.pk)


class OnboardingSessionQRView(HQAdminRequiredMixin, View):
    """Display the printable QR code for a session."""

    def get(self, request, pk):
        session = get_object_or_404(OnboardingSession, pk=pk)
        abs_public_url = request.build_absolute_uri(session.get_public_url())
        qr_api_url = session.get_qr_api_url(request)
        return render(request, "dashboard/hq_admin/onboarding/session_qr.html", {
            "session": session,
            "abs_public_url": abs_public_url,
            "qr_api_url": qr_api_url,
            # Larger version for printing
            "qr_api_url_print": qr_api_url.replace("400x400", "600x600"),
        })


class OnboardingSessionQRImageView(HQAdminRequiredMixin, View):
    """
    Proxy the external QR image through our origin so the browser canvas
    can capture it without CORS tainting (used by the client-side PNG download).
    """

    def get(self, request, pk):
        session = get_object_or_404(OnboardingSession, pk=pk)
        # Use 600×600 for a crisp high-res download
        qr_url = session.get_qr_api_url(request).replace("400x400", "600x600")
        try:
            req = _urllib_request.Request(qr_url, headers={"User-Agent": "IPAWAS/1.0"})
            with _urllib_request.urlopen(req, timeout=8) as resp:
                image_data = resp.read()
            response = HttpResponse(image_data, content_type="image/png")
            response["Cache-Control"] = "public, max-age=86400"
            return response
        except Exception as exc:
            logger.warning("QR image proxy failed for session %d: %s", pk, exc)
            return HttpResponseServerError("QR service temporarily unavailable")


class OnboardingSessionToggleView(HQAdminRequiredMixin, View):
    """Activate or deactivate a QR session (instantly kills / restores the QR)."""

    def post(self, request, pk):
        session = get_object_or_404(OnboardingSession, pk=pk)
        session.is_active = not session.is_active
        session.save(update_fields=["is_active"])
        state = "activated" if session.is_active else "deactivated"
        messages.success(request, f"Session '{session.label}' {state}.")
        return redirect("dashboard:hq:onboarding:index")


# ────────────────────────────────────────────────────────────────────────────
# Requests
# ────────────────────────────────────────────────────────────────────────────

class OnboardingRequestListView(HQAdminRequiredMixin, View):
    """List all onboarding requests, filterable by status."""

    def get(self, request):
        status_filter = request.GET.get("status", "pending")
        valid_statuses = ["pending", "approved", "rejected", "all"]
        if status_filter not in valid_statuses:
            status_filter = "pending"

        qs = OnboardingRequest.objects.select_related(
            "member_state", "session", "reviewed_by"
        ).order_by("-submitted_at")

        if status_filter != "all":
            qs = qs.filter(status=status_filter)

        counts = {
            "pending": OnboardingRequest.objects.filter(status="pending").count(),
            "approved": OnboardingRequest.objects.filter(status="approved").count(),
            "rejected": OnboardingRequest.objects.filter(status="rejected").count(),
            "all": OnboardingRequest.objects.count(),
        }

        # Build tabs as list of (key, label, count) so template doesn't need |get_item
        tabs = [
            ("pending", "Pending Review", counts["pending"]),
            ("approved", "Approved", counts["approved"]),
            ("rejected", "Rejected", counts["rejected"]),
            ("all", "All", counts["all"]),
        ]

        return render(request, "dashboard/hq_admin/onboarding/requests.html", {
            "requests": qs,
            "status_filter": status_filter,
            "counts": counts,
            "tabs": tabs,
        })


class OnboardingRequestDetailView(HQAdminRequiredMixin, View):
    """View a single onboarding request with approve/reject actions."""

    def get(self, request, pk):
        req = get_object_or_404(
            OnboardingRequest.objects.select_related(
                "member_state", "session", "reviewed_by", "invitation"
            ),
            pk=pk,
        )
        reject_form = OnboardingRejectForm()
        return render(request, "dashboard/hq_admin/onboarding/request_detail.html", {
            "req": req,
            "reject_form": reject_form,
        })


class OnboardingApproveView(HQAdminRequiredMixin, View):
    """
    Approve an onboarding request:
      1. Create an Invitation for the applicant
      2. Send the invitation email (with their personal registration link)
      3. Mark the OnboardingRequest as approved
      4. Link the Invitation to the OnboardingRequest
    """

    def post(self, request, pk):
        req = get_object_or_404(OnboardingRequest, pk=pk, status="pending")

        try:
            with transaction.atomic():
                # Create the invitation — uses the reviewing admin as invited_by
                invitation = Invitation.objects.create_invitation(
                    email=req.email,
                    member_state=req.member_state,
                    role=req.requested_role,
                    invited_by=request.user,
                    invitation_message=(
                        f"Dear {req.full_name},\n\n"
                        f"Your request to join the IPAWAS platform has been approved. "
                        f"Please use the link below to complete your registration."
                    ),
                    expires_in_days=7,
                )

                # Send invitation email via existing email service
                email_svc = get_invitation_email_service()
                email_sent = email_svc.send_invitation_email(invitation)

                if not email_sent:
                    logger.warning(
                        "Invitation email failed for onboarding request %d (email: %s)",
                        req.pk, req.email,
                    )
                    messages.warning(
                        request,
                        f"Request approved and invitation created, but the email to "
                        f"{req.email} could not be sent. Please resend from the Invitations page.",
                    )

                # Mark request as approved, link invitation
                req.status = "approved"
                req.reviewed_by = request.user
                req.reviewed_at = timezone.now()
                req.invitation = invitation
                req.save(update_fields=["status", "reviewed_by", "reviewed_at", "invitation"])

                if email_sent:
                    messages.success(
                        request,
                        f"Approved — invitation email sent to {req.email}. "
                        f"They have 7 days to complete registration.",
                    )

        except Exception as exc:
            logger.error("OnboardingApproveView failed for request %d: %s", pk, exc)
            messages.error(request, f"Error approving request: {exc}")

        return redirect("dashboard:hq:onboarding:requests")


class OnboardingRejectView(HQAdminRequiredMixin, View):
    """
    Reject an onboarding request.
    Optionally emails the applicant with the rejection reason.
    """

    def post(self, request, pk):
        req = get_object_or_404(OnboardingRequest, pk=pk, status="pending")
        form = OnboardingRejectForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Invalid rejection form.")
            return redirect("dashboard:hq:onboarding:request_detail", pk=pk)

        cd = form.cleaned_data

        req.status = "rejected"
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.rejection_reason = cd.get("rejection_reason", "")
        req.admin_notes = cd.get("admin_notes", "")
        req.save(update_fields=[
            "status", "reviewed_by", "reviewed_at",
            "rejection_reason", "admin_notes",
        ])

        if cd.get("notify_applicant", True):
            send_rejection_email(req)

        messages.success(request, f"Request from {req.email} rejected.")
        return redirect("dashboard:hq:onboarding:requests")
