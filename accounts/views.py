"""
Authentication Views for IPAWAS Platform
apps/accounts/views.py

Views for authentication operations:
- Login/Logout
- Invitation acceptance
- Password reset
- Profile management
- User management

Following Django CBV patterns with service layer integration.
"""

import base64
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import FormView, TemplateView, UpdateView
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

from accounts.forms import (
    InvitationAcceptanceForm,
    IPAProfileUpdateForm,
    LoginForm,
    PasswordChangeForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    PermissionsUpdateForm,
    ProfileUpdateForm,
    UserInvitationForm,
)
from accounts.models import IPAUser, User
from accounts.services import (
    AuthenticationService,
    PermissionService,
    UserInvitationService,
    UserManagementService,
)
from core.email.services import get_system_email_service
from dashboard.mixins import CanManageUsersMixin, IPAStaffRequiredMixin
from django.http import JsonResponse
from media_app.services.cloudinary_service import CloudinaryService

# ==============================================================================
# AUTHENTICATION VIEWS
# ==============================================================================


class LoginView(FormView):
    """
    User login view.

    Handles user authentication and redirects to appropriate dashboard.
    """

    template_name = "accounts/login.html"
    form_class = LoginForm

    def get(self, request, *args, **kwargs):
        # Redirect if already logged in
        if request.user.is_authenticated:
            return self._redirect_to_dashboard(request.user)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        remember_me = form.cleaned_data.get("remember_me", False)

        # Get IP address
        ip_address = self._get_client_ip(self.request)

        # Authenticate
        success, user, message = AuthenticationService.authenticate_user(
            email=email,
            password=password,
            request=self.request,
            ip_address=ip_address,
        )

        if success:
            # --- 2FA gate for staff / admin accounts ---
            if user.two_factor_enabled and user.user_type in ("ipawas_admin", "ipa_staff"):
                # Don't call login() yet — stash the user pk and next destination
                self.request.session["_2fa_user_pk"] = user.pk
                self.request.session["_2fa_remember_me"] = remember_me
                # Preserve the backend so _do_login can call login() on a fresh DB fetch
                self.request.session["_2fa_backend"] = getattr(
                    user, "backend", "django.contrib.auth.backends.ModelBackend"
                )
                next_url = self.request.GET.get("next", "")
                if next_url:
                    self.request.session["_2fa_next"] = next_url
                return redirect(reverse("accounts:verify_totp"))

            # No 2FA required — log in normally
            login(self.request, user)

            # Set session expiry
            if not remember_me:
                self.request.session.set_expiry(0)  # Expire on browser close
            else:
                self.request.session.set_expiry(1209600)  # 2 weeks

            # Record dashboard access for IPA staff
            if hasattr(user, "ipa_profile"):
                user.ipa_profile.record_dashboard_access()

            messages.success(self.request, _("Welcome back, %(name)s!") % {'name': user.get_full_name()})

            # Redirect to appropriate dashboard
            return self._redirect_to_dashboard(user)

        else:
            messages.error(self.request, message)
            return self.form_invalid(form)

    def _redirect_to_dashboard(self, user):
        """Redirect user to their appropriate dashboard"""
        # Check for next parameter — validate to prevent open redirect phishing
        next_url = self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return redirect(next_url)

        # Redirect based on user type
        if user.user_type == "ipawas_admin":
            return redirect("dashboard:hq:overview")
        elif user.user_type == "ipa_staff":
            return redirect(
                "dashboard:country:overview", member_state_slug=user.ipa_profile.member_state.slug
            )
        else:
            return redirect("home")

    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


@require_POST
@login_required
def logout_view(request):
    """
    User logout view — POST only to prevent CSRF-based forced logout via GET.

    Third-party sites cannot log users out via <img> or <a href> tags.
    Templates must use: <form method='post' action='{% url "accounts:logout" %}'>
    """
    user_name = request.user.get_full_name()
    logout(request)
    messages.success(request, _("Goodbye, %(name)s! You've been logged out successfully.") % {'name': user_name})
    return redirect("accounts:login")


class VerifyTOTPView(View):
    """
    Second step of login for accounts with 2FA enabled.

    After a successful password check, LoginView stashes the user pk in
    the session under ``_2fa_user_pk``.  This view validates the TOTP token,
    calls login(), then redirects to the appropriate dashboard.
    """

    template_name = "accounts/verify_totp.html"

    # Allow up to ±1 time-step (30 s) drift for clock skew
    _DRIFT_WINDOW = 1

    def dispatch(self, request, *args, **kwargs):
        # If already authenticated, go straight to dashboard
        if request.user.is_authenticated:
            return self._finish_redirect(request.user, request)

        # Must have a pending 2FA session
        if "_2fa_user_pk" not in request.session:
            return redirect("accounts:login")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        token = request.POST.get("token", "").strip().replace(" ", "")

        user_pk = request.session.get("_2fa_user_pk")
        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            messages.error(request, _("Session expired. Please log in again."))
            return redirect("accounts:login")

        if not user.two_factor_enabled or not user.two_factor_secret:
            # 2FA was disabled between steps — just log in
            self._do_login(request, user)
            return self._finish_redirect(user, request)

        if self._verify_token(user.two_factor_secret, token):
            self._do_login(request, user)
            return self._finish_redirect(user, request)

        messages.error(request, _("Invalid authentication code. Please try again."))
        return render(request, self.template_name)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _verify_token(secret: str, token: str) -> bool:
        """Verify a 6-digit TOTP token against the user's base32 secret."""
        try:
            from django_otp.oath import TOTP

            # base32-decode the secret (pad to multiple of 8)
            padded = secret + "=" * (-len(secret) % 8)
            key = base64.b32decode(padded, casefold=True)

            # TOTP.verify() compares self.token() (int) == token, so must pass int
            token_int = int(token)
            totp = TOTP(key=key, step=30, t0=0, digits=6, drift=0)
            # Check current step and ±1 window for clock-skew tolerance
            for drift in range(-VerifyTOTPView._DRIFT_WINDOW, VerifyTOTPView._DRIFT_WINDOW + 1):
                totp.drift = drift
                if totp.verify(token_int):
                    return True
            return False
        except Exception:
            logger.exception("TOTP verification error")
            return False

    @staticmethod
    def _do_login(request, user):
        remember_me = request.session.pop("_2fa_remember_me", False)
        # Restore the backend that was used for password auth so login() can work
        # with multiple AUTHENTICATION_BACKENDS configured (e.g. Axes + ModelBackend)
        backend = request.session.pop(
            "_2fa_backend", "django.contrib.auth.backends.ModelBackend"
        )
        if not hasattr(user, "backend"):
            user.backend = backend
        request.session.pop("_2fa_user_pk", None)

        login(request, user)

        if not remember_me:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(1209600)  # 2 weeks

        if hasattr(user, "ipa_profile"):
            user.ipa_profile.record_dashboard_access()

        messages.success(
            request,
            _("Welcome back, %(name)s!") % {"name": user.get_full_name()},
        )

    @staticmethod
    def _finish_redirect(user, request):
        next_url = request.session.pop("_2fa_next", "")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        if user.user_type == "ipawas_admin":
            return redirect("dashboard:hq:overview")
        elif user.user_type == "ipa_staff":
            return redirect(
                "dashboard:country:overview",
                member_state_slug=user.ipa_profile.member_state.slug,
            )
        return redirect("home")


# ==============================================================================
# 2FA SETUP VIEWS
# ==============================================================================


class Setup2FAView(LoginRequiredMixin, View):
    """
    Two-factor authentication setup flow.

    GET  — generates a fresh TOTP secret, stores it in the session (not in the
           DB yet), renders the QR code for the user to scan.
    POST — verifies the code the user enters against the session secret; only
           saves to the DB after a valid code is submitted.
    """

    template_name = "accounts/setup_2fa.html"

    def get(self, request, *args, **kwargs):
        import io
        import base64 as b64
        import secrets as sec
        import urllib.parse
        import qrcode

        # Generate a fresh base32 secret (RFC 6238)
        raw = sec.token_bytes(20)
        secret = b64.b32encode(raw).decode("utf-8").rstrip("=")

        # Stash in session — not persisted to DB until confirmed
        request.session["_2fa_setup_secret"] = secret

        # Build the otpauth:// URI so authenticator apps can parse the QR
        label = urllib.parse.quote(f"IPAWAS:{request.user.email}")
        issuer = urllib.parse.quote("IPAWAS Platform")
        padded = secret + "=" * (-len(secret) % 8)
        otp_uri = (
            f"otpauth://totp/{label}"
            f"?secret={padded}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
        )

        # Generate QR code as inline base64 PNG
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(otp_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = b64.b64encode(buf.getvalue()).decode("utf-8")

        return render(request, self.template_name, {
            "qr_b64": qr_b64,
            "secret": padded,   # shown as fallback manual-entry key
        })

    def post(self, request, *args, **kwargs):
        import base64 as b64
        from django_otp.oath import TOTP

        token = request.POST.get("token", "").strip().replace(" ", "")
        secret = request.session.get("_2fa_setup_secret")

        if not secret:
            messages.error(request, _("Setup session expired. Please start again."))
            return redirect("accounts:setup_2fa")

        # Verify the token against the session secret (±1 window)
        try:
            padded = secret + "=" * (-len(secret) % 8)
            key = b64.b32decode(padded, casefold=True)
            token_int = int(token)  # TOTP.verify() requires int
            totp = TOTP(key=key, step=30, t0=0, digits=6, drift=0)
            verified = False
            for drift in range(-1, 2):
                totp.drift = drift
                if totp.verify(token_int):
                    verified = True
                    break
        except Exception:
            logger.exception("2FA setup verification error")
            verified = False

        if not verified:
            messages.error(request, _("Invalid code. Please try again — make sure your device clock is accurate."))
            return redirect("accounts:setup_2fa")

        # Code confirmed — persist to DB
        from accounts.services import AuthenticationService
        request.user.two_factor_secret = secret
        request.user.two_factor_enabled = True
        request.user.save(update_fields=["two_factor_secret", "two_factor_enabled"])
        request.session.pop("_2fa_setup_secret", None)

        messages.success(request, _("Two-factor authentication is now active on your account."))
        return redirect("accounts:profile")


class Disable2FAView(LoginRequiredMixin, View):
    """Disable 2FA after the user confirms with their current TOTP code."""

    def post(self, request, *args, **kwargs):
        import base64 as b64
        from django_otp.oath import TOTP

        if not request.user.two_factor_enabled:
            messages.info(request, _("Two-factor authentication is not currently enabled."))
            return redirect("accounts:profile")

        token = request.POST.get("token", "").strip().replace(" ", "")
        secret = request.user.two_factor_secret

        try:
            padded = secret + "=" * (-len(secret) % 8)
            key = b64.b32decode(padded, casefold=True)
            token_int = int(token)  # TOTP.verify() requires int
            totp = TOTP(key=key, step=30, t0=0, digits=6, drift=0)
            verified = False
            for drift in range(-1, 2):
                totp.drift = drift
                if totp.verify(token_int):
                    verified = True
                    break
        except Exception:
            logger.exception("2FA disable verification error")
            verified = False

        if not verified:
            messages.error(request, _("Invalid code. Two-factor authentication was not disabled."))
            return redirect("accounts:profile")

        request.user.two_factor_enabled = False
        request.user.two_factor_secret = ""
        request.user.save(update_fields=["two_factor_enabled", "two_factor_secret"])

        messages.success(request, _("Two-factor authentication has been disabled."))
        return redirect("accounts:profile")


# ==============================================================================
# INVITATION VIEWS
# ==============================================================================


class AcceptInvitationView(FormView):
    """
    Accept invitation and complete registration.

    User clicks link from invitation email and fills in their details.
    """

    template_name = "accounts/accept_invitation.html"
    form_class = InvitationAcceptanceForm

    def dispatch(self, request, *args, **kwargs):
        # Get and validate token
        self.token = kwargs.get("token")

        try:
            self.invited_user = User.objects.get(
                invitation_token=self.token,
                is_active=False,
            )
        except User.DoesNotExist:
            messages.error(request, _("Invalid or expired invitation link"))
            return redirect("accounts:login")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invited_user"] = self.invited_user
        context["invited_by"] = self.invited_user.invited_by

        # Get member state if IPA staff
        if hasattr(self.invited_user, "ipa_profile"):
            context["member_state"] = self.invited_user.ipa_profile.member_state

        return context

    def form_valid(self, form):
        success, user, message = UserInvitationService.accept_invitation(
            token=self.token,
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            password=form.cleaned_data["password"],
            phone_number=form.cleaned_data.get("phone_number", ""),
            job_title=form.cleaned_data.get("job_title", ""),
        )

        if success:
            # Log user in
            login(self.request, user)
            messages.success(
                self.request,
                _("Welcome to IPAWAS! Your account has been activated successfully."),
            )
            return redirect("accounts:onboarding")
        else:
            messages.error(self.request, message)
            return self.form_invalid(form)


class OnboardingView(LoginRequiredMixin, TemplateView):
    """
    Onboarding view for new users.

    Shows welcome message and quick tour of dashboard.
    """

    template_name = "accounts/onboarding.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Mark onboarding as shown
        if hasattr(self.request.user, "ipa_profile"):
            ipa_profile = self.request.user.ipa_profile
            if not ipa_profile.onboarding_completed:
                ipa_profile.onboarding_completed = True
                ipa_profile.save(update_fields=["onboarding_completed"])

        return context


class SendInvitationView(CanManageUsersMixin, FormView):
    """
    Send invitation to new user.

    Used by admins and authorized users to invite team members.
    """

    template_name = "accounts/send_invitation.html"
    form_class = UserInvitationForm

    def get_success_url(self):
        user = self.request.user
        if user.user_type == "ipa_staff":
            return reverse(
                "dashboard:country:overview",
                kwargs={"member_state_slug": user.ipa_profile.member_state.slug},
            )
        return reverse("dashboard:hq:overview")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # Get member state for IPA staff
        if self.request.user.user_type == "ipa_staff":
            kwargs["member_state"] = self.request.user.ipa_profile.member_state

        return kwargs

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user_type = form.cleaned_data["user_type"]
        role = form.cleaned_data.get("role")
        personal_message = form.cleaned_data.get("personal_message", "")

        # Get member state
        member_state = None
        if user_type == "ipa_staff":
            if self.request.user.user_type == "ipa_staff":
                member_state = self.request.user.ipa_profile.member_state
            # If HQ admin inviting IPA staff, they would need to select member state
            # This would require additional form field

        # Send invitation
        success, token, message = UserInvitationService.create_invitation(
            invited_by=self.request.user,
            email=email,
            user_type=user_type,
            member_state=member_state,
            role=role,
            personal_message=personal_message,
        )

        if success:
            messages.success(
                self.request,
                _("Invitation sent to %(email)s. They will receive an email with instructions.") % {'email': email},
            )
            return super().form_valid(form)
        else:
            messages.error(self.request, message)
            return self.form_invalid(form)


class PendingInvitationsView(CanManageUsersMixin, TemplateView):
    """
    View pending invitations.

    Shows list of sent invitations that haven't been accepted yet.
    """

    template_name = "accounts/pending_invitations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get pending invitations
        member_state = None
        if self.request.user.user_type == "ipa_staff":
            member_state = self.request.user.ipa_profile.member_state

        context["pending_invitations"] = UserManagementService.get_pending_invitations(
            member_state=member_state
        )

        return context


@login_required
def resend_invitation(request, token):
    """Resend an invitation"""
    success, message = UserInvitationService.resend_invitation(
        invitation_token=token,
        invited_by=request.user,
    )

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect("dashboard:invitations:list")


@login_required
def revoke_invitation(request, token):
    """Revoke an invitation"""
    success, message = UserInvitationService.revoke_invitation(invitation_token=token)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect("dashboard:invitations:list")


# ==============================================================================
# PASSWORD RESET VIEWS
# ==============================================================================


class PasswordResetRequestView(FormView):
    """
    Request password reset.

    User enters email and receives reset link.
    """

    template_name = "accounts/password_reset_request.html"
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy("accounts:password_reset_done")

    def form_valid(self, form):
        email = form.cleaned_data["email"]

        success, message = AuthenticationService.send_password_reset_email(email)

        # Always show success message (don't reveal if email exists)
        messages.success(
            self.request,
            _("If an account exists with that email, we've sent password reset instructions."),
        )

        return super().form_valid(form)


class PasswordResetDoneView(TemplateView):
    """Confirmation that password reset email was sent"""

    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(FormView):
    """
    Confirm password reset using a signed, time-limited token.
    """

    template_name = "accounts/password_reset_confirm.html"
    form_class = PasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_complete")

    TOKEN_MAX_AGE = 60 * 60  # 1 hour

    def dispatch(self, request, *args, **kwargs):
        self.token = kwargs.get("token")

        # 🔑 Always resolve user (needed for POST)
        self.user = self._validate_token(self.token)

        # 🚫 Only block invalid tokens on GET
        if request.method == "GET" and not self.user:
            # messages.error(request, "This password reset link is invalid or has expired.")
            return redirect("accounts:login")

        return super().dispatch(request, *args, **kwargs)

    def _validate_token(self, token):
        signer = TimestampSigner()

        try:
            user_id = signer.unsign(
                token,
                max_age=self.TOKEN_MAX_AGE,
            )

            return User.objects.get(pk=user_id, is_active=True)

        except (BadSignature, SignatureExpired, User.DoesNotExist):
            return None

    def form_valid(self, form):
        new_password = form.cleaned_data["new_password"]

        self.user.set_password(new_password)
        self.user.password_changed_at = timezone.now()

        # Security hardening
        self.user.failed_login_attempts = 0
        self.user.account_locked_until = None

        self.user.save(
            update_fields=[
                "password",
                "password_changed_at",
                "failed_login_attempts",
                "account_locked_until",
            ]
        )

        messages.success(
            self.request, _("Your password has been reset successfully. You can now log in.")
        )

        # return redirect(self.get_success_url())
        return super().form_valid(form)


class PasswordResetCompleteView(TemplateView):
    """Confirmation that password was reset"""

    template_name = "accounts/password_reset_complete.html"


class PasswordChangeView(LoginRequiredMixin, FormView):
    """
    Change password (requires old password).

    Used in account settings.
    """

    template_name = "accounts/password_change.html"
    form_class = PasswordChangeForm
    success_url = reverse_lazy("accounts:profile")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        success, message = AuthenticationService.change_password(
            user=self.request.user,
            old_password=form.cleaned_data["current_password"],
            new_password=form.cleaned_data["new_password"],
        )

        if success:
            messages.success(self.request, _("Your password has been changed successfully."))
            return super().form_valid(form)
        else:
            messages.error(self.request, message)
            return self.form_invalid(form)


# ==============================================================================
# PROFILE VIEWS
# ==============================================================================


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    View user profile.

    Shows user's information and settings.
    """

    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user

        if hasattr(self.request.user, "ipa_profile"):
            context["ipa_profile"] = self.request.user.ipa_profile
            context["permissions"] = self.request.user.ipa_profile.get_permissions_summary()

        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update user profile.
    """

    model = User
    form_class = ProfileUpdateForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, _("Your profile has been updated."))
        return super().form_valid(form)


class IPAProfileUpdateView(IPAStaffRequiredMixin, UpdateView):
    """
    Update IPA-specific profile information.
    """

    model = IPAUser
    form_class = IPAProfileUpdateForm
    template_name = "accounts/ipa_profile_edit.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self):
        return self.request.user.ipa_profile

    def form_valid(self, form):
        messages.success(self.request, _("Your IPA profile has been updated."))
        return super().form_valid(form)


class AvatarUploadView(LoginRequiredMixin, View):
    """Upload or replace the user's profile picture via Cloudinary."""

    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

    def post(self, request, *args, **kwargs):
        f = request.FILES.get("avatar")
        if not f:
            return JsonResponse({"success": False, "error": "No file received."}, status=400)

        if f.content_type not in self.ALLOWED_TYPES:
            return JsonResponse(
                {"success": False, "error": "Only JPEG, PNG, WebP, or GIF images are allowed."},
                status=400,
            )

        if f.size > self.MAX_SIZE_BYTES:
            return JsonResponse(
                {"success": False, "error": "File must be smaller than 5 MB."},
                status=400,
            )

        folder = f"ipawas/avatars/user-{request.user.pk}"
        result = CloudinaryService.upload_file(f, folder_path=folder, resource_type="image")

        if not result["success"]:
            return JsonResponse(
                {"success": False, "error": "Upload failed. Please try again."},
                status=500,
            )

        url = result["data"].get("secure_url", "")
        if not url:
            return JsonResponse(
                {"success": False, "error": "Upload succeeded but no URL was returned."},
                status=500,
            )

        request.user.profile_picture = url
        request.user.save(update_fields=["profile_picture"])

        return JsonResponse({"success": True, "url": url})


# ==============================================================================
# USER MANAGEMENT VIEWS
# ==============================================================================


class TeamMembersView(CanManageUsersMixin, TemplateView):
    """
    View team members.

    Shows list of users in the member state.
    """

    template_name = "accounts/team_members.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get member state
        member_state = None
        if self.request.user.user_type == "ipa_staff":
            member_state = self.request.user.ipa_profile.member_state

        if member_state:
            context["team_members"] = UserManagementService.get_team_members(member_state)
            context["member_state"] = member_state

        return context


class ManageUserPermissionsView(CanManageUsersMixin, UpdateView):
    """
    Manage user permissions.

    Update what a user can do in their dashboard.
    """

    model = IPAUser
    form_class = PermissionsUpdateForm
    template_name = "accounts/manage_permissions.html"

    def get_object(self):
        from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)

        # IDOR guard: IPA staff may only manage users in their own member state
        if self.request.user.user_type == "ipa_staff":
            try:
                requester_state = self.request.user.ipa_profile.member_state
                target_state = user.ipa_profile.member_state
                if requester_state != target_state:
                    raise DjangoPermissionDenied(
                        "You cannot manage users from another member state."
                    )
            except AttributeError:
                raise DjangoPermissionDenied("Target user is not an IPA staff member.")

        return user.ipa_profile

    def get_success_url(self):
        user = self.request.user
        if user.user_type == "ipa_staff":
            return reverse(
                "dashboard:country:overview",
                kwargs={"member_state_slug": user.ipa_profile.member_state.slug},
            )
        return reverse("dashboard:hq:overview")

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Permissions updated for %(name)s") % {'name': form.instance.user.get_full_name()},
        )
        return super().form_valid(form)


def _dashboard_redirect(request):
    """Return the correct dashboard URL for the current user."""
    if request.user.user_type == "ipa_staff":
        return reverse(
            "dashboard:country:overview",
            kwargs={"member_state_slug": request.user.ipa_profile.member_state.slug},
        )
    return reverse("dashboard:hq:overview")


@login_required
def deactivate_user(request, user_id):
    """Deactivate a user"""
    if not PermissionService.can_manage_users(request.user):
        messages.error(request, _("You don't have permission to manage users"))
        return redirect(_dashboard_redirect(request))

    user = get_object_or_404(User, id=user_id)

    success, message = UserManagementService.deactivate_user(user)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect(_dashboard_redirect(request))


@login_required
def reactivate_user(request, user_id):
    """Reactivate a user"""
    if not PermissionService.can_manage_users(request.user):
        messages.error(request, _("You don't have permission to manage users"))
        return redirect(_dashboard_redirect(request))

    user = get_object_or_404(User, id=user_id)

    success, message = UserManagementService.reactivate_user(user)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect(_dashboard_redirect(request))


# ==============================================================================
# EMAIL VERIFICATION VIEWS
# ==============================================================================


class VerifyEmailView(View):
    """
    Verify email address with token.
    """

    def get(self, request, token):
        success, message = AuthenticationService.verify_email(token)

        if success:
            messages.success(request, _("Your email has been verified successfully!"))
        else:
            messages.error(request, message)

        if request.user.is_authenticated:
            return redirect("accounts:profile")
        else:
            return redirect("accounts:login")
