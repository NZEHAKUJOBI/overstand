"""
HQ Admin dashboard views for Training Session & Assessment management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView

from training.emails import send_training_invitation
from training.forms import InvitationBulkForm, TrainingSessionForm
from training.models import (
    PostTrainingFeedback,
    PreTrainingAssessment,
    TrainingInvitation,
    TrainingSession,
)


class HQAdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_staff or getattr(request.user, "user_type", "") == "ipawas_admin"):
            messages.error(request, _("HQ admin access required."))
            return redirect("dashboard:hq:overview")
        return super().dispatch(request, *args, **kwargs)


# ──────────────────────────────────────────────────────────────
# Training session list / create
# ──────────────────────────────────────────────────────────────

class TrainingIndexView(HQAdminRequiredMixin, TemplateView):
    template_name = "dashboard/hq_admin/training/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sessions"] = TrainingSession.objects.prefetch_related("invitations").order_by("-training_date")
        ctx["session_form"] = TrainingSessionForm()
        return ctx

    def post(self, request, *args, **kwargs):
        form = TrainingSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.save()
            messages.success(request, _("Training session created."))
            return redirect("dashboard:hq:training:detail", pk=session.pk)
        ctx = self.get_context_data()
        ctx["session_form"] = form
        return render(request, self.template_name, ctx)


# ──────────────────────────────────────────────────────────────
# Session detail — invite management & phase toggle
# ──────────────────────────────────────────────────────────────

class TrainingSessionDetailView(HQAdminRequiredMixin, View):
    template_name = "dashboard/hq_admin/training/session_detail.html"

    def get(self, request, pk):
        session = get_object_or_404(TrainingSession, pk=pk)
        invite_form = InvitationBulkForm()
        invitations = session.invitations.all().order_by("name")
        return render(request, self.template_name, {
            "session": session,
            "invite_form": invite_form,
            "invitations": invitations,
            "pre_count": session.pre_responses_count,
            "post_count": session.post_responses_count,
        })

    def post(self, request, pk):
        session = get_object_or_404(TrainingSession, pk=pk)

        # ── Phase toggle ──────────────────────────────────────
        if "toggle_phase" in request.POST:
            new_phase = (
                TrainingSession.PHASE_POST
                if session.phase == TrainingSession.PHASE_PRE
                else TrainingSession.PHASE_PRE
            )
            session.phase = new_phase
            session.save(update_fields=["phase"])
            phase_label = dict(TrainingSession.PHASE_CHOICES)[new_phase]
            messages.success(request, _("Phase switched to: %(phase)s") % {"phase": phase_label})
            return redirect("dashboard:hq:training:detail", pk=pk)

        # ── Resend invitation ─────────────────────────────────
        if "resend_invite" in request.POST:
            inv_id = request.POST.get("invitation_id")
            inv = get_object_or_404(TrainingInvitation, pk=inv_id, session=session)
            ok = send_training_invitation(inv)
            if ok:
                messages.success(request, _("Invitation resent to %(email)s.") % {"email": inv.email})
            else:
                messages.error(request, _("Failed to send email to %(email)s.") % {"email": inv.email})
            return redirect("dashboard:hq:training:detail", pk=pk)

        # ── Add new invitee ───────────────────────────────────
        form = InvitationBulkForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            inv, created = TrainingInvitation.objects.get_or_create(
                session=session,
                email=cd["email"],
                defaults={
                    "name": cd["name"],
                    "organization": cd.get("organization", ""),
                    "country": cd["country"],
                    "job_title": cd.get("job_title", ""),
                },
            )
            if not created:
                messages.warning(
                    request,
                    _("%(email)s is already in this session.") % {"email": cd["email"]},
                )
                return redirect("dashboard:hq:training:detail", pk=pk)

            # Auto-trigger email (Decision 1)
            ok = send_training_invitation(inv)
            if ok:
                messages.success(
                    request,
                    _("Invitation created and email sent to %(email)s.") % {"email": cd["email"]},
                )
            else:
                messages.warning(
                    request,
                    _("Invitee added but email delivery failed for %(email)s. Use 'Resend' to retry.") % {"email": cd["email"]},
                )
            return redirect("dashboard:hq:training:detail", pk=pk)

        # Re-render with form errors
        invitations = session.invitations.all().order_by("name")
        return render(request, self.template_name, {
            "session": session,
            "invite_form": form,
            "invitations": invitations,
            "pre_count": session.pre_responses_count,
            "post_count": session.post_responses_count,
        })


# ──────────────────────────────────────────────────────────────
# Response viewer
# ──────────────────────────────────────────────────────────────

class TrainingResponsesView(HQAdminRequiredMixin, View):
    template_name = "dashboard/hq_admin/training/responses.html"

    def get(self, request, pk):
        session = get_object_or_404(TrainingSession, pk=pk)
        phase = request.GET.get("phase", "pre")

        if phase == "post":
            responses = PostTrainingFeedback.objects.filter(
                invitation__session=session
            ).select_related("invitation")
        else:
            responses = PreTrainingAssessment.objects.filter(
                invitation__session=session
            ).select_related("invitation")

        return render(request, self.template_name, {
            "session": session,
            "responses": responses,
            "phase": phase,
        })
