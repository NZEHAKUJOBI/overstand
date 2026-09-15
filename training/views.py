"""
Public-facing training views.

URL pattern: /training/<token>/
One URL — the phase (pre/post) is set by the admin on the TrainingSession.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django_ratelimit.decorators import ratelimit

from .forms import PostFeedbackForm, PreAssessmentForm, RegistrationConfirmForm
from .models import TrainingInvitation


@method_decorator(
    ratelimit(key="ip", rate="5/h", method="POST", block=True),
    name="post",
)
class AssessmentView(View):
    """
    Single URL that serves:
    - Pre-training assessment  (when session.phase == 'pre')
    - Post-training feedback   (when session.phase == 'post')

    Phase is toggled by the admin on the dashboard.
    """

    template_name = "training/assessment.html"

    def _get_invitation(self, token):
        return get_object_or_404(
            TrainingInvitation.select_related("session"),
            token=token,
        )

    def get(self, request, token):
        invitation = get_object_or_404(
            TrainingInvitation.objects.select_related("session"),
            token=token,
        )
        session = invitation.session

        # Guard: session must be active
        if not session.is_active:
            return render(request, "training/closed.html", {"session": session})

        # Guard: already submitted for this phase
        if session.is_pre_phase and invitation.has_pre_assessment:
            return render(request, "training/already_submitted.html", {
                "invitation": invitation,
                "phase": "pre",
            })
        if not session.is_pre_phase and invitation.has_post_feedback:
            return render(request, "training/already_submitted.html", {
                "invitation": invitation,
                "phase": "post",
            })

        confirm_form = RegistrationConfirmForm(initial={
            "name": invitation.name,
            "organization": invitation.organization,
            "job_title": invitation.job_title,
            "country": invitation.country,
        })
        assess_form = PreAssessmentForm() if session.is_pre_phase else PostFeedbackForm()

        return render(request, self.template_name, {
            "invitation": invitation,
            "session": session,
            "confirm_form": confirm_form,
            "assess_form": assess_form,
            "is_pre_phase": session.is_pre_phase,
        })

    def post(self, request, token):
        invitation = get_object_or_404(
            TrainingInvitation.objects.select_related("session"),
            token=token,
        )
        session = invitation.session

        if not session.is_active:
            return render(request, "training/closed.html", {"session": session})

        # Update participant details from confirmation section
        confirm_form = RegistrationConfirmForm(request.POST)
        if confirm_form.is_valid():
            cd = confirm_form.cleaned_data
            invitation.name = cd["name"]
            invitation.organization = cd.get("organization", invitation.organization)
            invitation.job_title = cd.get("job_title", invitation.job_title)
            invitation.country = cd["country"]
            invitation.save(update_fields=["name", "organization", "job_title", "country"])
            if not invitation.registered_at:
                invitation.mark_registered()

        if session.is_pre_phase:
            assess_form = PreAssessmentForm(request.POST)
            if assess_form.is_valid():
                obj = assess_form.save(commit=False)
                obj.invitation = invitation
                obj.save()
                invitation.mark_completed()
                return redirect("training:success", token=token)
        else:
            assess_form = PostFeedbackForm(request.POST)
            if assess_form.is_valid():
                obj = assess_form.save(commit=False)
                obj.invitation = invitation
                obj.save()
                invitation.mark_completed()
                return redirect("training:success", token=token)

        # Re-render with errors
        return render(request, self.template_name, {
            "invitation": invitation,
            "session": session,
            "confirm_form": confirm_form,
            "assess_form": assess_form,
            "is_pre_phase": session.is_pre_phase,
        })


class AssessmentSuccessView(View):
    def get(self, request, token):
        invitation = get_object_or_404(
            TrainingInvitation.objects.select_related("session"),
            token=token,
        )
        return render(request, "training/success.html", {
            "invitation": invitation,
            "session": invitation.session,
        })
