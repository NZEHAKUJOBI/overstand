"""
Onboarding Forms — IPAWAS Platform

OnboardingRequestForm  : public self-service form (with honeypot)
OnboardingRejectForm   : admin rejection form (reason field)
OnboardingSessionForm  : admin form for creating QR sessions
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from members.models import MemberStateIPA
from onboarding.models import ROLE_CHOICES


class OnboardingRequestForm(forms.Form):
    """
    Self-service form filled in by the prospective IPA staff member after scanning QR.

    Security:
      - `website` is a honeypot field (hidden via CSS, bots fill it, humans don't).
      - Server-side dedup and rate limiting are enforced in the view.
    """

    full_name = forms.CharField(
        max_length=200,
        label=_("Full Name"),
        widget=forms.TextInput(attrs={"autocomplete": "name", "class": "form-control"}),
        error_messages={"required": _("Please enter your full name.")},
    )
    email = forms.EmailField(
        label=_("Work Email Address"),
        widget=forms.EmailInput(attrs={"autocomplete": "email", "class": "form-control"}),
        error_messages={
            "required": _("Please enter your email address."),
            "invalid": _("Please enter a valid email address."),
        },
    )
    member_state = forms.ModelChoiceField(
        queryset=MemberStateIPA.objects.filter(is_active=True).order_by("country_name"),
        label=_("Member State / Country"),
        empty_label=_("— Select your country —"),
        widget=forms.Select(attrs={"class": "form-control"}),
        error_messages={"required": _("Please select your member state.")},
    )
    job_title = forms.CharField(
        max_length=200,
        label=_("Job Title / Position"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
        error_messages={"required": _("Please enter your job title.")},
    )
    requested_role = forms.ChoiceField(
        choices=[("", _("— Select your role —"))] + list(ROLE_CHOICES),
        label=_("Requested Platform Role"),
        widget=forms.Select(attrs={"class": "form-control"}),
        error_messages={"required": _("Please select your intended role.")},
    )
    organization = forms.CharField(
        max_length=200,
        required=False,
        label=_("Organization / IPA Name"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text=_("Optional — leave blank if same as your member state IPA."),
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        label=_("Phone Number"),
        widget=forms.TextInput(
            attrs={"autocomplete": "tel", "class": "form-control", "placeholder": "+225 XX XX XXXX"}
        ),
    )
    personal_email = forms.EmailField(
        required=False,
        label=_("Personal Email Address"),
        widget=forms.EmailInput(attrs={"autocomplete": "email", "class": "form-control"}),
        help_text=_("Optional — used as a backup contact in case your work email changes."),
        error_messages={"invalid": _("Please enter a valid email address.")},
    )

    # ── Honeypot ───────────────────────────────────────────────────────────
    # Rendered hidden via CSS. Legitimate users never fill it.
    # Bots that fill every field get silently rejected.
    website = forms.CharField(
        required=False,
        label="Website",  # Deliberately generic label to attract bots
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

    def clean_email(self):
        return self.cleaned_data["email"].lower().strip()

    def clean_requested_role(self):
        value = self.cleaned_data["requested_role"]
        valid = [r[0] for r in ROLE_CHOICES]
        if value not in valid:
            raise forms.ValidationError(_("Invalid role selected."))
        return value

    def clean(self):
        cleaned = super().clean()
        # Honeypot check — bots fill every field
        if cleaned.get("website"):
            raise forms.ValidationError(
                _("Your submission could not be processed. Please try again.")
            )
        return cleaned


class OnboardingRejectForm(forms.Form):
    """Used by HQ admin to reject a pending onboarding request."""

    rejection_reason = forms.CharField(
        required=False,
        label=_("Reason for Rejection"),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _(
                    "Optional — explain why the request was rejected. "
                    "This will be included in the notification email to the applicant."
                ),
            }
        ),
    )
    admin_notes = forms.CharField(
        required=False,
        label=_("Internal Notes"),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Internal notes (not sent to the applicant)."),
            }
        ),
    )
    notify_applicant = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Send rejection email to the applicant"),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class OnboardingSessionForm(forms.Form):
    """HQ admin form for creating a new onboarding QR session."""

    label = forms.CharField(
        max_length=200,
        label=_("Session Label"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("e.g. May 2026 Training — Accra"),
            }
        ),
        help_text=_("Internal label shown in the dashboard. Not visible publicly."),
    )
    expires_at = forms.DateTimeField(
        required=False,
        label=_("Expiry Date & Time"),
        widget=forms.DateTimeInput(
            attrs={"class": "form-control", "type": "datetime-local"}
        ),
        help_text=_("Optional. Leave blank for no automatic expiry."),
    )
    max_submissions = forms.IntegerField(
        required=False,
        min_value=1,
        label=_("Maximum Submissions"),
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        help_text=_(
            "Optional. Automatically closes the session after this many pending/approved "
            "submissions. Leave blank for unlimited."
        ),
    )
    notes = forms.CharField(
        required=False,
        label=_("Internal Notes"),
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        help_text=_("Not shown publicly."),
    )
