"""
Forms for Invitation System.

Handles invitation creation, resending, and user registration from invitations.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Invitation

User = get_user_model()


class InvitationForm(forms.ModelForm):
    """
    Form for creating new invitations.
    Used by IPAWAS admins and IPA admins to invite staff.
    """

    # Custom field for email validation
    email = forms.EmailField(
        label=_("Email Address"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "email@example.com",
                "autocomplete": "off",
            }
        ),
        help_text=_("Email address of the person you're inviting"),
    )

    user_type = forms.ChoiceField(
        label=_("Invitation Type"),
        choices=[
            ("ipa_staff", _("IPA Staff (assigned to a member state)")),
            ("ipawas_admin", _("IPAWAS HQ Admin (no member state)")),
        ],
        initial="ipa_staff",
        widget=forms.RadioSelect(
            attrs={
                "class": "form-check-input",
            }
        ),
        help_text=_("IPA Staff invitations require a member state and role. HQ Admin invitations do not."),
    )

    invitation_message = forms.CharField(
        label=_("Personal Message (Optional)"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Add a personal message to the invitation email..."),
            }
        ),
        help_text=_("Optional personalized message to include in the invitation email"),
    )

    expires_in_days = forms.IntegerField(
        label=_("Expires In (Days)"),
        initial=7,
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
            }
        ),
        help_text=_("Number of days until invitation expires (1-30)"),
    )

    class Meta:
        model = Invitation
        fields = ["email", "user_type", "role", "is_primary_contact", "invitation_message"]
        widgets = {
            "role": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "is_primary_contact": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "role": _("Role"),
            "is_primary_contact": _("Primary Contact"),
        }
        help_texts = {
            "role": _("Access level for this user (required for IPA Staff, not used for HQ Admin)"),
            "is_primary_contact": _("Check if this person is the main IPA contact"),
        }

    def __init__(self, *args, **kwargs):
        self.member_state = kwargs.pop("member_state", None)
        self.invited_by = kwargs.pop("invited_by", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Make role not required at form level — we enforce it in clean() when needed
        self.fields["role"].required = False

        if self.member_state:
            # IPA staff creating invitation for their own member state:
            # - user_type is always ipa_staff — hidden + not required + clean_user_type().
            self.fields["user_type"].widget = forms.HiddenInput()
            self.fields["user_type"].initial = "ipa_staff"
            self.fields["user_type"].required = False

            # Show member state as a locked, disabled dropdown.
            # Queryset is restricted to the user's own member state so even if
            # someone removes the disabled attribute and submits a different PK,
            # validation will reject it.
            from members.models import MemberStateIPA

            self.fields["member_state"] = forms.ModelChoiceField(
                queryset=MemberStateIPA.objects.filter(pk=self.member_state.pk),
                initial=self.member_state,
                widget=forms.Select(attrs={
                    "class": "form-select",
                    "disabled": "disabled",
                }),
                label=_("Member State"),
                required=False,  # disabled inputs are not submitted by browsers
                help_text=_("Invitations are always for your own member state."),
            )
        else:
            # HQ admin creating invitation:
            # - show user_type radio to choose ipa_staff vs ipawas_admin
            # - show member_state dropdown (conditionally required based on user_type)
            from members.models import MemberStateIPA

            self.fields["member_state"] = forms.ModelChoiceField(
                queryset=MemberStateIPA.objects.filter(is_active=True).order_by("country_name"),
                widget=forms.Select(attrs={"class": "form-select"}),
                label=_("Member State"),
                help_text=_("Select the member state for this invitation (not required for HQ Admin)"),
                required=False,
            )

    def clean_user_type(self):
        """
        For IPA staff (member_state set), always return 'ipa_staff' regardless
        of what was submitted.  This handles the case where the hidden input is
        absent from POST data (e.g. template not rendering {{ form.hidden_fields }}).
        """
        if self.member_state:
            return "ipa_staff"
        return self.cleaned_data.get("user_type")

    def clean_email(self):
        """Validate email address"""
        email = self.cleaned_data.get("email", "").lower().strip()

        if not email:
            raise ValidationError(_("Email address is required"))

        # Basic email validation
        if "@" not in email or "." not in email.split("@")[1]:
            raise ValidationError(_("Please enter a valid email address"))

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)

            # Check if already IPA staff for this member state
            if self.member_state and hasattr(user, "ipa_profile"):
                if user.ipa_profile.member_state == self.member_state:
                    raise ValidationError(
                        _(
                            f"A user with this email already has access to {self.member_state.ipa_acronym}"
                        )
                    )

        # Check for pending invitation in this member state (if known at this stage)
        if self.member_state:
            pending_invitation = Invitation.objects.filter(
                email=email, member_state=self.member_state, status="pending"
            ).first()

            if pending_invitation:
                raise ValidationError(
                    _(
                        f"An invitation has already been sent to this email for {self.member_state.ipa_acronym}"
                    )
                )

        return email

    def clean_invitation_message(self):
        """Validate invitation message"""
        message = self.cleaned_data.get("invitation_message", "").strip()

        if len(message) > 500:
            raise ValidationError(_("Message is too long (max 500 characters)"))

        return message

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()

        # When member_state is passed in kwargs (IPA staff), user_type field is removed
        # from the form, so it won't be in cleaned_data — always treat as ipa_staff.
        if self.member_state:
            cleaned_data["user_type"] = "ipa_staff"

        user_type = cleaned_data.get("user_type", "ipa_staff")
        is_hq_admin = user_type == "ipawas_admin"

        if is_hq_admin:
            # HQ admin invitations must NOT have a member state or role
            cleaned_data["member_state"] = None
            cleaned_data["role"] = ""
            self.instance.member_state = None  # keep model instance in sync

            # Check for existing pending HQ invitation for this email
            email = cleaned_data.get("email")
            if email and Invitation.objects.filter(
                email=email, member_state__isnull=True, status="pending"
            ).exists():
                self.add_error(
                    "email",
                    _("A pending HQ admin invitation already exists for this email address."),
                )
        else:
            # IPA staff invitations require member_state and role
            member_state = self.member_state or cleaned_data.get("member_state")
            if not member_state:
                raise ValidationError(_("Member state is required for IPA staff invitations"))
            if not cleaned_data.get("role"):
                self.add_error("role", _("Role is required for IPA staff invitations"))
            # Sync member_state onto the model instance now so that _post_clean()'s
            # call to instance.full_clean() sees the correct value.  Without this,
            # member_state is not in Meta.fields so _post_clean() never applies it,
            # and the model's clean() raises "must use user_type='ipawas_admin'".
            self.instance.member_state = member_state

        return cleaned_data


class ResendInvitationForm(forms.Form):
    """
    Simple form for resending invitations.
    """

    confirm = forms.BooleanField(
        label=_("Confirm resend"),
        required=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
        help_text=_("Check to confirm you want to resend this invitation"),
    )


class RevokeInvitationForm(forms.Form):
    """
    Form for revoking invitations.
    """

    reason = forms.CharField(
        label=_("Reason for revocation"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Optional: Explain why you're revoking this invitation..."),
            }
        ),
        help_text=_("Optional reason for revoking this invitation"),
    )

    confirm = forms.BooleanField(
        label=_("Confirm revocation"),
        required=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
        error_messages={
            "required": _("You must confirm to revoke this invitation"),
        },
    )


class InvitationRegistrationForm(UserCreationForm):
    """
    Registration form for users accepting invitations.
    Pre-filled with email from invitation.
    """

    first_name = forms.CharField(
        label=_("First Name"),
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("First name"),
                "autocomplete": "given-name",
            }
        ),
    )

    last_name = forms.CharField(
        label=_("Last Name"),
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Last name"),
                "autocomplete": "family-name",
            }
        ),
    )

    job_title = forms.CharField(
        label=_("Job Title"),
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Your job title"),
                "autocomplete": "organization-title",
            }
        ),
    )

    phone_number = forms.CharField(
        label=_("Phone Number"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("+XXX XXX XXX XXXX"),
                "autocomplete": "tel",
            }
        ),
    )

    language_preference = forms.ChoiceField(
        label=_("Preferred Language"),
        choices=[
            ("en", _("English")),
            ("fr", _("French")),
            ("pt", _("Portuguese")),
        ],
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    terms_accepted = forms.BooleanField(
        label=_("I accept the terms and conditions"),
        required=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
        error_messages={
            "required": _("You must accept the terms and conditions to register"),
        },
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "job_title",
            "phone_number",
            "language_preference",
            "password1",
            "password2",
        ]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "readonly": "readonly",
                    "autocomplete": "email",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.invitation = kwargs.pop("invitation", None)
        super().__init__(*args, **kwargs)

        # Pre-fill email from invitation
        if self.invitation:
            self.fields["email"].initial = self.invitation.email
            self.fields["email"].widget.attrs["readonly"] = True

        # Enhance password fields
        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": _("Password"),
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": _("Confirm password"),
                "autocomplete": "new-password",
            }
        )

        # Update help texts
        self.fields["password1"].help_text = _(
            "Password must be at least 12 characters and contain uppercase, "
            "lowercase, numbers, and special characters."
        )

    def clean_email(self):
        """Ensure email matches invitation"""
        email = self.cleaned_data.get("email", "").lower().strip()

        if self.invitation and email != self.invitation.email:
            raise ValidationError(_("Email must match the invitation"))

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("An account with this email already exists"))

        return email

    def clean_password1(self):
        """Enhanced password validation"""
        password = self.cleaned_data.get("password1")

        if len(password) < 12:
            raise ValidationError(_("Password must be at least 12 characters long"))

        # Check for complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValidationError(
                _("Password must contain uppercase, lowercase, numbers, and special characters")
            )

        return password

    def save(self, commit=True):
        """Save user with additional fields"""
        user = super().save(commit=False)

        # Set user type from invitation (ipa_staff or ipawas_admin)
        user.user_type = self.invitation.user_type if self.invitation else "ipa_staff"
        user.email_verified = True  # Email verified through invitation
        user.job_title = self.cleaned_data.get("job_title", "")
        user.phone_number = self.cleaned_data.get("phone_number", "")
        user.language_preference = self.cleaned_data.get("language_preference", "en")

        # Link to invitation
        if self.invitation:
            user.invitation_token = str(self.invitation.token)
            user.invited_by = self.invitation.invited_by

        if commit:
            user.save()

        return user


class BulkInvitationForm(forms.Form):
    """
    Form for bulk inviting multiple users at once.

    Features:
    - Supports up to 50 emails
    - Removes duplicates automatically
    - Validates email format
    - Member state field for HQ admins (optional for IPA staff)
    """

    emails = forms.CharField(
        label=_("Email Addresses"),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "email1@example.com\nemail2@example.com",
                "id": "id_emails",
            }
        ),
        help_text=_("Enter one email address per line (max 50)"),
    )

    role = forms.ChoiceField(
        label=_("Role"),
        choices=[
            ("ipa_director", _("IPA Director")),
            ("ipa_manager", _("IPA Manager")),
            ("ipa_officer", _("IPA Officer")),
            ("ipa_data_entry", _("IPA Data Entry")),
            ("ipa_analyst", _("IPA Analyst")),
        ],
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_role",
            }
        ),
        help_text=_("All invited users will have this role"),
    )

    invitation_message = forms.CharField(
        label=_("Message to all invitees"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Add a personalized message for all invitees..."),
            }
        ),
        help_text=_("This message will be included in all invitation emails"),
    )

    def __init__(self, *args, **kwargs):
        """
        Initialize form with user context.

        Args:
            user: Current user (required)
            member_state: Member state for IPA staff (optional)
        """
        self.user = kwargs.pop("user", None)
        self.member_state = kwargs.pop("member_state", None)
        super().__init__(*args, **kwargs)

        # Add member_state field for HQ admins only
        if self.user and self.user.user_type != "ipa_staff":
            from members.models import MemberStateIPA

            self.fields["member_state"] = forms.ModelChoiceField(
                queryset=MemberStateIPA.objects.filter(is_active=True).order_by("country_name"),
                widget=forms.Select(attrs={"class": "form-select"}),
                label=_("Member State"),
                help_text=_("Select the member state for these invitations"),
                required=True,
            )

    def clean_emails(self):
        """Validate and parse email addresses"""
        emails_text = self.cleaned_data.get("emails", "")

        # Split by newlines and clean
        email_list = [email.strip().lower() for email in emails_text.split("\n") if email.strip()]

        # Remove duplicates while preserving order
        seen = set()
        unique_emails = []
        for email in email_list:
            if email not in seen:
                seen.add(email)
                unique_emails.append(email)

        # Validate count
        if len(unique_emails) == 0:
            raise ValidationError(_("Please enter at least one email address"))

        if len(unique_emails) > 50:
            raise ValidationError(
                _("Maximum 50 email addresses allowed at once. You entered %(count)d.")
                % {"count": len(unique_emails)}
            )

        # Validate each email format
        invalid_emails = []
        for email in unique_emails:
            # Basic email validation
            if "@" not in email:
                invalid_emails.append(email)
                continue

            parts = email.split("@")
            if len(parts) != 2:
                invalid_emails.append(email)
                continue

            local, domain = parts
            if not local or not domain:
                invalid_emails.append(email)
                continue

            if "." not in domain:
                invalid_emails.append(email)
                continue

        if invalid_emails:
            # Show first 5 invalid emails
            display_emails = invalid_emails[:5]
            error_msg = _("Invalid email addresses: %(emails)s") % {
                "emails": ", ".join(display_emails)
            }

            if len(invalid_emails) > 5:
                error_msg += f" (and {len(invalid_emails) - 5} more)"

            raise ValidationError(error_msg)

        return unique_emails

    def clean_invitation_message(self):
        """Validate invitation message"""
        message = self.cleaned_data.get("invitation_message", "").strip()

        if len(message) > 1000:
            raise ValidationError(
                _("Message is too long. Maximum 1000 characters (currently %(count)d).")
                % {"count": len(message)}
            )

        return message

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()

        # Ensure member_state is set for HQ admins
        if self.user and self.user.user_type != "ipa_staff":
            if "member_state" not in cleaned_data or not cleaned_data["member_state"]:
                raise ValidationError(_("Please select a member state"))

        return cleaned_data


# For backward compatibility, keep the simpler version too
class SimpleBulkInvitationForm(forms.Form):
    """
    Simplified bulk invitation form (for IPA staff only).
    Use BulkInvitationForm for full functionality.
    """

    emails = forms.CharField(
        label=_("Email Addresses"),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "email1@example.com\nemail2@example.com",
            }
        ),
        help_text=_("Enter one email address per line (max 50)"),
    )

    role = forms.ChoiceField(
        label=_("Role"),
        choices=[
            ("ipa_director", _("IPA Director")),
            ("ipa_manager", _("IPA Manager")),
            ("ipa_officer", _("IPA Officer")),
            ("ipa_data_entry", _("IPA Data Entry")),
            ("ipa_analyst", _("IPA Analyst")),
        ],
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
        help_text=_("All invited users will have this role"),
    )

    invitation_message = forms.CharField(
        label=_("Message to all invitees"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
            }
        ),
        help_text=_("This message will be included in all invitation emails"),
    )

    def clean_emails(self):
        """Validate and parse email addresses"""
        emails_text = self.cleaned_data.get("emails", "")

        # Split by newlines and clean
        email_list = [email.strip().lower() for email in emails_text.split("\n") if email.strip()]

        # Remove duplicates
        email_list = list(set(email_list))

        # Validate count
        if len(email_list) == 0:
            raise ValidationError(_("Please enter at least one email address"))

        if len(email_list) > 50:
            raise ValidationError(_("Maximum 50 email addresses allowed at once"))

        # Validate each email
        invalid_emails = []
        for email in email_list:
            if "@" not in email or "." not in email.split("@")[1]:
                invalid_emails.append(email)

        if invalid_emails:
            raise ValidationError(
                _("Invalid email addresses: %(emails)s") % {"emails": ", ".join(invalid_emails)}
            )

        return email_list
