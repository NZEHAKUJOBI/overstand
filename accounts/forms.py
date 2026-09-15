"""
Authentication Forms for IPAWAS Platform
apps/accounts/forms.py

Django forms for authentication operations:
- LoginForm: User login
- InvitationAcceptanceForm: Complete registration from invitation
- PasswordResetRequestForm: Request password reset
- PasswordResetForm: Set new password
- PasswordChangeForm: Change password (requires old password)
- UserInvitationForm: Send invitations to new users
- ProfileUpdateForm: Update user profile
- PermissionsUpdateForm: Update user permissions
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models import IPAUser, User


class UserEditForm(forms.ModelForm):
    """
    Form for editing basic user information by HQ admins.
    """

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "job_title",
            "organization",
            "is_active",
            "language_preference",
            "timezone",
            "email_notifications",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("First Name")}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Last Name")}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": _("Email Address")}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+234..."}
            ),
            "job_title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("e.g. Investment Officer")}
            ),
            "organization": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Organization Name")}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "language_preference": forms.Select(attrs={"class": "form-select"}),
            "timezone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("e.g. Africa/Lagos")}
            ),
            "email_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_email(self):
        """Ensure email is unique (excluding current user)."""
        email = self.cleaned_data.get("email")
        if email:
            qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(_("This email is already in use."))
        return email


class IPAUserPermissionsForm(forms.ModelForm):
    """
    Form for managing IPA user permissions.
    """

    class Meta:
        model = IPAUser
        fields = [
            "role",
            "can_publish_opportunities",
            "can_approve_data",
            "can_manage_users",
            "can_edit_profile",
            "can_manage_sectors",
            "can_create_opportunities",
            "can_edit_incentives",
            "can_manage_success_stories",
            "can_view_inquiries",
            "can_respond_to_inquiries",
            "can_view_analytics",
            "can_export_data",
            "is_primary_contact",
        ]
        widgets = {
            "role": forms.Select(attrs={"class": "form-select", "id": "id_role"}),
            "can_publish_opportunities": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_approve_data": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_manage_users": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_edit_profile": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_manage_sectors": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_create_opportunities": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_edit_incentives": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_manage_success_stories": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_view_inquiries": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_respond_to_inquiries": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_view_analytics": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_export_data": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_primary_contact": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            "role": _("Role automatically sets default permissions"),
            "can_publish_opportunities": _("Publish without approval"),
            "can_approve_data": _("Approve WAIIS submissions"),
            "can_manage_users": _("Create/edit IPA users"),
            "is_primary_contact": _("Primary focal point for this IPA"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for permission fields
        self.fields["role"].help_text = _("Changing role will reset permissions to defaults")


class LoginForm(forms.Form):
    """
    User login form.

    Simple and clean - just email and password.
    """

    email = forms.EmailField(
        label=_("Email Address"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter your email"),
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter your password"),
            }
        ),
    )

    remember_me = forms.BooleanField(
        label=_("Remember me"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    def clean_email(self):
        """Normalize email to lowercase"""
        return self.cleaned_data.get("email", "").lower().strip()


class InvitationAcceptanceForm(forms.Form):
    """
    Form for accepting invitation and completing registration.

    User fills in their details and sets a password.
    """

    first_name = forms.CharField(
        label=_("First Name"),
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter your first name"),
            }
        ),
    )

    last_name = forms.CharField(
        label=_("Last Name"),
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter your last name"),
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
                "placeholder": "+234 XXX XXX XXXX",
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
                "placeholder": _("e.g., Investment Officer"),
            }
        ),
    )

    password = forms.CharField(
        label=_("Create Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Create a strong password"),
            }
        ),
        help_text=_("Password must be at least 8 characters with letters and numbers"),
    )

    password_confirm = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Confirm your password"),
            }
        ),
    )

    accept_terms = forms.BooleanField(
        label=_("I accept the Terms of Service and Privacy Policy"),
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    def clean_password(self):
        """Validate password strength"""
        password = self.cleaned_data.get("password")

        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)

        return password

    def clean(self):
        """Validate that passwords match"""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(_("Passwords do not match"))

        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    """
    Form for requesting password reset.

    User enters their email to receive reset link.
    """

    email = forms.EmailField(
        label=_("Email Address"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter your registered email"),
            }
        ),
        help_text=_("Enter the email address associated with your account"),
    )

    def clean_email(self):
        """Normalize email"""
        return self.cleaned_data.get("email", "").lower().strip()


class PasswordResetForm(forms.Form):
    """
    Form for setting new password after reset request.

    Used when user clicks link from reset email.
    """

    new_password = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter new password"),
            }
        ),
        help_text=_("Password must be at least 8 characters"),
    )

    new_password_confirm = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Confirm new password"),
            }
        ),
    )

    def clean_new_password(self):
        """Validate password strength"""
        password = self.cleaned_data.get("new_password")

        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)

        return password

    def clean(self):
        """Validate that passwords match"""
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        password_confirm = cleaned_data.get("new_password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(_("Passwords do not match"))

        return cleaned_data


class PasswordChangeForm(forms.Form):
    """
    Form for changing password (requires old password).

    Used in account settings when user wants to change password.
    """

    current_password = forms.CharField(
        label=_("Current Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter current password"),
            }
        ),
    )

    new_password = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter new password"),
            }
        ),
        help_text=_("Password must be at least 8 characters"),
    )

    new_password_confirm = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Confirm new password"),
            }
        ),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        """Verify current password is correct"""
        password = self.cleaned_data.get("current_password")

        if not self.user.check_password(password):
            raise forms.ValidationError(_("Current password is incorrect"))

        return password

    def clean_new_password(self):
        """Validate password strength"""
        password = self.cleaned_data.get("new_password")

        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)

        return password

    def clean(self):
        """Validate that passwords match"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        new_password_confirm = cleaned_data.get("new_password_confirm")

        if new_password and new_password_confirm and new_password != new_password_confirm:
            raise forms.ValidationError(_("New passwords do not match"))

        return cleaned_data


class UserInvitationForm(forms.Form):
    """
    Form for inviting new users.

    Used by admins and authorized users to invite team members.
    """

    email = forms.EmailField(
        label=_("Email Address"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "user@example.com",
            }
        ),
        help_text=_("Invitation will be sent to this email"),
    )

    user_type = forms.ChoiceField(
        label=_("User Type"),
        choices=[
            ("ipa_staff", _("IPA Staff Member")),
            ("ipawas_admin", _("IPAWAS HQ Administrator")),
        ],
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    role = forms.ChoiceField(
        label=_("Role"),
        choices=IPAUser.IPA_ROLES,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        help_text=_("Role determines default permissions (for IPA staff only)"),
    )

    personal_message = forms.CharField(
        label=_("Personal Message"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Optional: Add a personal message to the invitation"),
            }
        ),
    )

    def __init__(self, member_state=None, *args, **kwargs):
        """
        Initialize form with member state context.

        Args:
            member_state: MemberStateIPA instance (for IPA staff invitations)
        """
        self.member_state = member_state
        super().__init__(*args, **kwargs)

        # If member state is provided, default to ipa_staff and hide user_type
        if member_state:
            self.fields["user_type"].initial = "ipa_staff"
            self.fields["user_type"].widget = forms.HiddenInput()

    def clean_email(self):
        """Validate email doesn't already exist"""
        email = self.cleaned_data.get("email", "").lower().strip()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user with this email already exists"))

        return email

    def clean(self):
        """Validate role is provided for IPA staff"""
        cleaned_data = super().clean()
        user_type = cleaned_data.get("user_type")
        role = cleaned_data.get("role")

        if user_type == "ipa_staff" and not role:
            raise forms.ValidationError(_("Role is required for IPA staff invitations"))

        if user_type == "ipa_staff" and not self.member_state:
            raise forms.ValidationError(_("Member state is required for IPA staff invitations"))

        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information.
    """

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "job_title",
            "bio",
            "language_preference",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "job_title": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "language_preference": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email read-only
        self.fields["email"].disabled = True


class IPAProfileUpdateForm(forms.ModelForm):
    """
    Form for updating IPA-specific profile information.
    """

    class Meta:
        model = IPAUser
        fields = [
            "direct_phone",
            "extension",
            "office_location",
            "is_primary_contact",
            "notify_on_inquiry",
            "notify_on_opportunity_expiry",
            "notify_on_team_changes",
        ]
        widgets = {
            "direct_phone": forms.TextInput(attrs={"class": "form-control"}),
            "extension": forms.TextInput(attrs={"class": "form-control"}),
            "office_location": forms.TextInput(attrs={"class": "form-control"}),
            "is_primary_contact": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notify_on_inquiry": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notify_on_opportunity_expiry": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "notify_on_team_changes": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class PermissionsUpdateForm(forms.ModelForm):
    """
    Form for updating user permissions.

    Used by admins to manage what users can do.
    """

    class Meta:
        model = IPAUser
        fields = [
            "role",
            "can_publish_opportunities",
            "can_approve_data",
            "can_manage_users",
            "can_edit_profile",
            "can_manage_sectors",
            "can_create_opportunities",
            "can_edit_incentives",
            "can_manage_success_stories",
            "can_view_inquiries",
            "can_respond_to_inquiries",
            "can_view_analytics",
            "can_export_data",
        ]
        widgets = {
            "role": forms.Select(attrs={"class": "form-control"}),
            "can_publish_opportunities": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_approve_data": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_manage_users": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_edit_profile": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_manage_sectors": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_create_opportunities": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_edit_incentives": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_manage_success_stories": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_view_inquiries": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_respond_to_inquiries": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_view_analytics": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_export_data": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add help text for each permission
        help_texts = {
            "can_publish_opportunities": _("Can publish opportunities without approval"),
            "can_approve_data": _("Can approve WAIIS data submissions"),
            "can_manage_users": _("Can create and edit other IPA users"),
            "can_edit_profile": _("Can edit member state profile"),
            "can_manage_sectors": _("Can add and edit priority sectors"),
            "can_create_opportunities": _("Can create investment opportunities"),
            "can_edit_incentives": _("Can manage investment incentives"),
            "can_manage_success_stories": _("Can create and edit success stories"),
            "can_view_inquiries": _("Can view investor inquiries"),
            "can_respond_to_inquiries": _("Can respond to investor inquiries"),
            "can_view_analytics": _("Can access analytics dashboard"),
            "can_export_data": _("Can export data and reports"),
        }

        for field_name, help_text in help_texts.items():
            if field_name in self.fields:
                self.fields[field_name].help_text = help_text


# NOTE: BulkPermissionsForm removed — was never referenced by any view or URL.
