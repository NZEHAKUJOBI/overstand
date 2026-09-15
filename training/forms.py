"""
Training forms — both admin-side (invite creation) and public-side (assessment).
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from members.models import MemberStateIPA

from .models import (
    ROLE_CHOICES,
    YEARS_CHOICES,
    PostTrainingFeedback,
    PreTrainingAssessment,
    TrainingInvitation,
    TrainingSession,
)


def get_member_state_choices():
    """Return choices tuple from the live DB; fall back to empty if not yet migrated."""
    try:
        states = (
            MemberStateIPA.objects.filter(is_active=True)
            .values_list("country_name", "country_name")
            .order_by("country_name")
        )
        choices = [("", _("Select your country…"))] + list(states)
        return choices
    except Exception:
        return [("", _("Select your country…"))]


# ──────────────────────────────────────────────────────────────
# Admin forms (dashboard)
# ──────────────────────────────────────────────────────────────

class TrainingSessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ["title", "description", "training_date", "location", "phase", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. IPAWAS Platform Handover Training"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "training_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Abuja, Nigeria / Zoom"}),
            "phase": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class InvitationBulkForm(forms.Form):
    """Add one or more invitees at once (comma-separated or line-separated emails)."""

    name = forms.CharField(
        label=_("Full Name"),
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Jane Doe"}),
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    organization = forms.CharField(
        label=_("Organization"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    country = forms.ChoiceField(
        label=_("Country"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    job_title = forms.CharField(
        label=_("Job Title"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["country"].choices = get_member_state_choices()


# ──────────────────────────────────────────────────────────────
# Public forms (assessment page)
# ──────────────────────────────────────────────────────────────

class RegistrationConfirmForm(forms.Form):
    """
    Shown at top of assessment page — participant confirms/updates their details.
    """
    name = forms.CharField(
        label=_("Full Name"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    organization = forms.CharField(
        label=_("Organization / IPA"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    job_title = forms.CharField(
        label=_("Job Title / Position"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    country = forms.ChoiceField(
        label=_("Country"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["country"].choices = get_member_state_choices()


class PreAssessmentForm(forms.ModelForm):
    CHALLENGING_AREA_CHOICES = [
        ("digital_tools", _("Digital tools & platforms")),
        ("investor_targeting", _("Investor targeting & outreach")),
        ("data_analysis", _("Data collection & analysis")),
        ("policy_advocacy", _("Policy advocacy")),
        ("deal_facilitation", _("Deal facilitation & aftercare")),
        ("communication", _("Communication & stakeholder engagement")),
        ("monitoring", _("Monitoring & evaluation")),
        ("regional_cooperation", _("Regional / ECOWAS cooperation")),
    ]

    challenging_areas = forms.MultipleChoiceField(
        choices=CHALLENGING_AREA_CHOICES,
        required=False,
        label=_("Challenging Areas (select all that apply)"),
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = PreTrainingAssessment
        exclude = ["invitation", "submitted_at"]
        widgets = {
            "current_role": forms.Select(attrs={"class": "form-select"}),
            "years_in_role": forms.Select(attrs={"class": "form-select"}),
            "knowledge_ipawas": forms.RadioSelect(),
            "knowledge_investment_promotion": forms.RadioSelect(),
            "knowledge_data_tools": forms.RadioSelect(),
            "knowledge_regional_collab": forms.RadioSelect(),
            "training_expectations": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Describe your expectations…"}),
            "prior_ipawas_experience": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Leave blank if none…"}),
        }

    def clean_challenging_areas(self):
        return self.cleaned_data.get("challenging_areas", [])


class PostFeedbackForm(forms.ModelForm):
    would_recommend = forms.TypedChoiceField(
        choices=[("true", _("Yes")), ("false", _("No"))],
        coerce=lambda v: v == "true",
        widget=forms.RadioSelect(),
        label=_("Would you recommend this training to a colleague?"),
    )

    class Meta:
        model = PostTrainingFeedback
        exclude = ["invitation", "submitted_at"]
        widgets = {
            "overall_rating": forms.RadioSelect(),
            "content_relevance": forms.RadioSelect(),
            "trainer_effectiveness": forms.RadioSelect(),
            "platform_usability": forms.RadioSelect(),
            "pace_and_structure": forms.RadioSelect(),
            "most_valuable": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "needs_improvement": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "key_takeaway": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "apply_learning_timeline": forms.Select(attrs={"class": "form-select"}),
            "additional_comments": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
