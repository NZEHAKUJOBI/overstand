"""
Authentication Services for IPAWAS Platform
apps/accounts/services.py

Business logic layer for authentication and user management:
- AuthenticationService: Login, logout, password management
- UserInvitationService: Invitation workflow
- PermissionService: Permission checking and validation
- UserManagementService: User CRUD operations

Following domain-driven design principles.
"""

import base64
import secrets
from datetime import timedelta
from typing import Dict, Optional, Tuple

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import EmailMultiAlternatives
from django.core.signing import TimestampSigner
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from accounts.models import IPAUser, User
from core.email.services import get_system_email_service


class AuthenticationService:
    """
    Service for handling authentication operations.

    Think of this as the security gate - it validates credentials,
    manages sessions, and ensures only authorized users get through.
    """

    @staticmethod
    def generate_password_reset_token(user: User) -> str:
        signer = TimestampSigner()
        return signer.sign(user.pk)

    @staticmethod
    def authenticate_user(
        email: str, password: str, request=None, ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[User], str]:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address
            password: User's password
            ip_address: Optional IP address for logging

        Returns:
            Tuple of (success, user, message)
        """
        # Normalize email
        email = email.lower().strip()

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return False, None, "Invalid email or password"

        # Check if account is locked
        if user.is_account_locked:
            return (
                False,
                None,
                "Account is temporarily locked due to failed login attempts. Please try again later.",
            )

        # Check if account is active
        if not user.is_active:
            return False, None, "Your account has been deactivated. Please contact support."

        # Authenticate
        authenticated_user = authenticate(request=request, username=email, password=password)

        if authenticated_user:
            # Record successful login
            user.record_login(ip_address)
            return True, authenticated_user, "Login successful"
        else:
            # Record failed login (both django-axes and our own model counter)
            user.record_failed_login()
            attempts_left = 5 - user.failed_login_attempts

            if attempts_left > 0:
                return (
                    False,
                    None,
                    f"Invalid email or password. {attempts_left} attempt(s) remaining.",
                )
            else:
                return (
                    False,
                    None,
                    "Account locked due to too many failed attempts. Please try again in 30 minutes.",
                )

    @staticmethod
    def verify_email(token: str) -> Tuple[bool, str]:
        """
        Verify user's email address with token.

        Args:
            token: Email verification token

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.objects.get(email_verification_token=token)

            if user.email_verified:
                return False, "Email already verified"

            user.email_verified = True
            user.email_verification_token = ""
            user.save(update_fields=["email_verified", "email_verification_token"])

            return True, "Email verified successfully"

        except User.DoesNotExist:
            return False, "Invalid verification token"

    @staticmethod
    def send_password_reset_email(email: str) -> Tuple[bool, str]:
        """
        Send password reset email to user.

        Args:
            email: User's email address

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.objects.get(email=email.lower().strip())

            if not user.is_active:
                return False, "Account is deactivated"

            # Initialize email service
            email_service = get_system_email_service()

            # Generate reset token
            token = AuthenticationService.generate_password_reset_token(user)

            # Use reverse() so the URL includes the i18n language prefix (/en/, /fr/, /pt/)
            # that i18n_patterns adds. A hardcoded path like /accounts/password-reset/...
            # would 404 because Django only matches /en/accounts/password-reset/...
            reset_path = reverse(
                "accounts:password_reset_confirm", kwargs={"token": token}
            )
            reset_url = f"{settings.SITE_URL}{reset_path}"

            email_service.send_password_reset_email(
                user=user,
                reset_url=reset_url,
            )

            return True, "Password reset email sent"

        except User.DoesNotExist:
            return True, "If an account exists with that email, a reset link has been sent"

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user's password (requires old password).

        Args:
            user: User instance
            old_password: Current password
            new_password: New password

        Returns:
            Tuple of (success, message)
        """
        if not user.check_password(old_password):
            return False, "Current password is incorrect"

        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.save()

        return True, "Password changed successfully"

    @staticmethod
    def enable_two_factor(user: User) -> str:
        """
        Enable 2FA for user and return secret.

        Args:
            user: User instance

        Returns:
            TOTP secret key
        """
        if user.two_factor_enabled:
            return user.two_factor_secret

        # Generate TOTP secret — RFC 6238 requires base32-encoded bytes
        secret = base64.b32encode(secrets.token_bytes(20)).decode("utf-8").rstrip("=")
        user.two_factor_secret = secret
        user.two_factor_enabled = True
        user.save(update_fields=["two_factor_secret", "two_factor_enabled"])

        return secret

    @staticmethod
    def disable_two_factor(user: User) -> bool:
        """
        Disable 2FA for user.

        Args:
            user: User instance

        Returns:
            Success status
        """
        user.two_factor_enabled = False
        user.two_factor_secret = ""
        user.save(update_fields=["two_factor_enabled", "two_factor_secret"])
        return True


class UserInvitationService:
    """
    Service for managing user invitations.

    Like sending out wedding invitations - you prepare them,
    send them out, track RSVPs, and handle acceptances.
    """

    @staticmethod
    @transaction.atomic
    def create_invitation(
        invited_by: User,
        email: str,
        user_type: str,
        member_state=None,
        role: str = "ipa_officer",
        preset_permissions: Optional[Dict] = None,
        personal_message: str = "",
    ) -> Tuple[bool, Optional[User], str]:
        """
        Create and send an invitation.

        Args:
            invited_by: User sending the invitation
            email: Email address to invite
            user_type: 'ipa_staff' or 'ipawas_admin'
            member_state: MemberStateIPA instance (required for ipa_staff)
            role: Role to assign (for ipa_staff)
            preset_permissions: Dict of permissions to set
            personal_message: Optional message to include

        Returns:
            Tuple of (success, invitation_token_or_none, message)
        """
        email = email.lower().strip()

        # Validate inputs
        if user_type not in ["ipa_staff", "ipawas_admin"]:
            return False, None, "Invalid user type"

        if user_type == "ipa_staff" and not member_state:
            return False, None, "Member state is required for IPA staff invitations"

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return False, None, "A user with this email already exists"

        # Check if there's already a pending invitation
        existing_pending = User.objects.filter(
            email=email,
            invitation_token__isnull=False,
            accepted_invitation_at__isnull=True,
        ).exists()

        if existing_pending:
            return False, None, "An invitation has already been sent to this email"

        # Generate invitation token
        invitation_token = secrets.token_urlsafe(32)

        # Create user account (inactive until invitation accepted)
        user = User.objects.create(
            email=email,
            username=email,  # Set username same as email
            user_type=user_type,
            is_active=False,  # Inactive until they complete registration
            invitation_token=invitation_token,
            invited_by=invited_by,
        )

        # Create IPA profile if ipa_staff
        if user_type == "ipa_staff":
            ipa_profile = IPAUser.objects.create(
                user=user,
                member_state=member_state,
                role=role,
            )

            # Apply custom permissions if provided
            if preset_permissions:
                for perm_name, perm_value in preset_permissions.items():
                    if hasattr(ipa_profile, perm_name):
                        setattr(ipa_profile, perm_name, perm_value)
                ipa_profile.save()

        # Send invitation email
        UserInvitationService._send_invitation_email(
            user=user,
            invited_by=invited_by,
            invitation_token=invitation_token,
            member_state=member_state,
            personal_message=personal_message,
        )

        return True, invitation_token, "Invitation sent successfully"

    @staticmethod
    def _send_invitation_email(
        user: User,
        invited_by: User,
        invitation_token: str,
        member_state=None,
        personal_message: str = "",
    ):
        """Send invitation email."""
        context = {
            "invited_user": user,
            "invited_by": invited_by,
            "invitation_token": invitation_token,
            "accept_url": f"{settings.SITE_URL}/accounts/accept-invitation/{invitation_token}/",
            "member_state": member_state,
            "personal_message": personal_message,
            "expiry_days": 7,
        }

        html_content = render_to_string("accounts/emails/invitation.html", context)
        text_content = strip_tags(html_content)

        email_message = EmailMultiAlternatives(
            subject=f"You're invited to join IPAWAS Dashboard",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

    @staticmethod
    @transaction.atomic
    def accept_invitation(
        token: str,
        first_name: str,
        last_name: str,
        password: str,
        phone_number: str = "",
        job_title: str = "",
    ) -> Tuple[bool, Optional[User], str]:
        """
        Accept an invitation and complete registration.

        Args:
            token: Invitation token
            first_name: User's first name
            last_name: User's last name
            password: User's chosen password
            phone_number: Optional phone number
            job_title: Optional job title

        Returns:
            Tuple of (success, user, message)
        """
        try:
            user = User.objects.get(invitation_token=token, is_active=False)
        except User.DoesNotExist:
            return False, None, "Invalid or expired invitation"

        # Update user details
        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone_number
        user.job_title = job_title
        user.set_password(password)
        user.is_active = True
        user.email_verified = True
        user.accepted_invitation_at = timezone.now()
        user.password_changed_at = timezone.now()
        user.save()

        # Clear invitation token after use
        user.invitation_token = ""
        user.save(update_fields=["invitation_token"])

        # Send welcome email
        UserInvitationService._send_welcome_email(user)

        return True, user, "Registration completed successfully"

    @staticmethod
    def _send_welcome_email(user: User):
        """Send welcome email after successful registration."""
        context = {
            "user": user,
            "dashboard_url": f"{settings.SITE_URL}/dashboard/",
        }

        html_content = render_to_string("accounts/emails/welcome.html", context)
        text_content = strip_tags(html_content)

        email_message = EmailMultiAlternatives(
            subject="Welcome to IPAWAS Dashboard",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

    @staticmethod
    def resend_invitation(invitation_token: str, invited_by: User) -> Tuple[bool, str]:
        """
        Resend an invitation email.

        Args:
            invitation_token: Token of invitation to resend
            invited_by: User resending the invitation

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.objects.get(invitation_token=invitation_token, is_active=False)

            member_state = None
            if hasattr(user, "ipa_profile"):
                member_state = user.ipa_profile.member_state

            UserInvitationService._send_invitation_email(
                user=user,
                invited_by=invited_by,
                invitation_token=invitation_token,
                member_state=member_state,
            )

            return True, "Invitation resent successfully"

        except User.DoesNotExist:
            return False, "Invitation not found"

    @staticmethod
    def revoke_invitation(invitation_token: str) -> Tuple[bool, str]:
        """
        Revoke an invitation (delete the inactive user).

        Args:
            invitation_token: Token of invitation to revoke

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.objects.get(invitation_token=invitation_token, is_active=False)
            email = user.email
            user.delete()
            return True, f"Invitation to {email} has been revoked"

        except User.DoesNotExist:
            return False, "Invitation not found"


class PermissionService:
    """
    Service for checking user permissions.

    Like a bouncer at a club - checks if you have the right
    credentials to access specific areas.
    """

    @staticmethod
    def can_user_access_dashboard(user: User, dashboard_type: str) -> bool:
        """
        Check if user can access a specific dashboard.

        Args:
            user: User instance
            dashboard_type: 'hq' or 'country'

        Returns:
            Boolean indicating access permission
        """
        if not user.is_authenticated or not user.is_active:
            return False

        if dashboard_type == "hq":
            return user.user_type == "ipawas_admin"
        elif dashboard_type == "country":
            return user.user_type == "ipa_staff" and hasattr(user, "ipa_profile")

        return False

    @staticmethod
    def can_edit_member_state_content(user: User, member_state) -> bool:
        """
        Check if user can edit content for a specific member state.

        Args:
            user: User instance
            member_state: MemberStateIPA instance

        Returns:
            Boolean indicating permission
        """
        if not user.is_authenticated or not user.is_active:
            return False

        # HQ admins can edit any member state
        if user.user_type == "ipawas_admin":
            return True

        # IPA staff can only edit their own member state
        if user.user_type == "ipa_staff" and hasattr(user, "ipa_profile"):
            return user.ipa_profile.member_state == member_state

        return False

    @staticmethod
    def can_manage_users(user: User, target_member_state=None) -> bool:
        """
        Check if user can manage other users.

        Args:
            user: User instance
            target_member_state: Optional specific member state

        Returns:
            Boolean indicating permission
        """
        if not user.is_authenticated or not user.is_active:
            return False

        # HQ admins can manage all users
        if user.user_type == "ipawas_admin":
            return True

        # IPA staff can manage users in their member state if they have permission
        if user.user_type == "ipa_staff" and hasattr(user, "ipa_profile"):
            ipa_profile = user.ipa_profile

            if not ipa_profile.can_manage_users:
                return False

            # If target member state specified, check it matches
            if target_member_state:
                return ipa_profile.member_state == target_member_state

            return True

        return False

    @staticmethod
    def can_publish_content(user: User) -> bool:
        """
        Check if user can publish content.

        Args:
            user: User instance

        Returns:
            Boolean indicating permission
        """
        if not user.is_authenticated or not user.is_active:
            return False

        # HQ admins can always publish
        if user.user_type == "ipawas_admin":
            return True

        # IPA staff need specific permission
        if user.user_type == "ipa_staff" and hasattr(user, "ipa_profile"):
            # Check if they have publish permission
            # Using can_publish_opportunities as the publish permission
            return user.ipa_profile.can_publish_opportunities

        return False

    @staticmethod
    def get_accessible_member_states(user: User):
        """
        Get list of member states user can access.

        Args:
            user: User instance

        Returns:
            QuerySet of MemberStateIPA objects
        """
        from members.models import MemberStateIPA

        if not user.is_authenticated or not user.is_active:
            return MemberStateIPA.objects.none()

        # HQ admins can access all member states
        if user.user_type == "ipawas_admin":
            return MemberStateIPA.objects.filter(is_active=True)

        # IPA staff can only access their member state
        if user.user_type == "ipa_staff" and hasattr(user, "ipa_profile"):
            return MemberStateIPA.objects.filter(
                id=user.ipa_profile.member_state.id,
                is_active=True,
            )

        return MemberStateIPA.objects.none()


class UserManagementService:
    """
    Service for user CRUD operations and profile management.
    """

    @staticmethod
    @transaction.atomic
    def create_ipa_user(
        email: str,
        first_name: str,
        last_name: str,
        member_state,
        role: str = "ipa_officer",
        created_by: Optional[User] = None,
        send_invitation: bool = True,
        **additional_fields,
    ) -> Tuple[bool, Optional[User], str]:
        """
        Create a new IPA user.

        Args:
            email: User's email
            first_name: First name
            last_name: Last name
            member_state: MemberStateIPA instance
            role: IPA role
            created_by: User creating this account
            send_invitation: Whether to send invitation email
            **additional_fields: Additional user or profile fields

        Returns:
            Tuple of (success, user, message)
        """
        email = email.lower().strip()

        # Check if user exists
        if User.objects.filter(email=email).exists():
            return False, None, "User with this email already exists"

        # Create user
        user = User.objects.create(
            email=email,
            username=email,
            first_name=first_name,
            last_name=last_name,
            user_type="ipa_staff",
            is_active=False if send_invitation else True,
        )

        # Set additional user fields
        for field, value in additional_fields.items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.save()

        # Create IPA profile
        ipa_profile = IPAUser.objects.create(
            user=user,
            member_state=member_state,
            role=role,
        )

        if send_invitation and created_by:
            # Generate and send invitation
            invitation_token = secrets.token_urlsafe(32)
            user.invitation_token = invitation_token
            user.invited_by = created_by
            user.save(update_fields=["invitation_token", "invited_by"])

            UserInvitationService._send_invitation_email(
                user=user,
                invited_by=created_by,
                invitation_token=invitation_token,
                member_state=member_state,
            )

        return True, user, "User created successfully"

    @staticmethod
    def update_user_permissions(
        user: User,
        permissions: Dict[str, bool],
    ) -> Tuple[bool, str]:
        """
        Update user's permissions.

        Args:
            user: User to update
            permissions: Dict of permission names and values

        Returns:
            Tuple of (success, message)
        """
        if not hasattr(user, "ipa_profile"):
            return False, "User is not an IPA staff member"

        ipa_profile = user.ipa_profile

        # Update permissions
        updated = []
        for perm_name, perm_value in permissions.items():
            if hasattr(ipa_profile, perm_name):
                setattr(ipa_profile, perm_name, perm_value)
                updated.append(perm_name)

        ipa_profile.save()

        return True, f"Updated {len(updated)} permission(s)"

    @staticmethod
    def deactivate_user(user: User, reason: str = "") -> Tuple[bool, str]:
        """
        Deactivate a user account.

        Args:
            user: User to deactivate
            reason: Optional reason for deactivation

        Returns:
            Tuple of (success, message)
        """
        user.is_active = False
        user.save(update_fields=["is_active"])

        # Also deactivate IPA profile if exists
        if hasattr(user, "ipa_profile"):
            user.ipa_profile.is_active = False
            user.ipa_profile.save(update_fields=["is_active"])

        return True, f"User {user.email} has been deactivated"

    @staticmethod
    def reactivate_user(user: User) -> Tuple[bool, str]:
        """
        Reactivate a user account.

        Args:
            user: User to reactivate

        Returns:
            Tuple of (success, message)
        """
        user.is_active = True
        user.save(update_fields=["is_active"])

        # Also reactivate IPA profile if exists
        if hasattr(user, "ipa_profile"):
            user.ipa_profile.is_active = True
            user.ipa_profile.save(update_fields=["is_active"])

        return True, f"User {user.email} has been reactivated"

    @staticmethod
    def get_team_members(member_state) -> list:
        """
        Get all team members for a member state.

        Args:
            member_state: MemberStateIPA instance

        Returns:
            List of IPAUser instances
        """
        return (
            IPAUser.objects.filter(
                member_state=member_state,
                is_active=True,
            )
            .select_related("user")
            .order_by("-is_primary_contact", "user__first_name")
        )

    @staticmethod
    def get_pending_invitations(member_state=None):
        """
        Get pending invitations.

        Args:
            member_state: Optional MemberStateIPA to filter by

        Returns:
            QuerySet of User objects with pending invitations
        """
        queryset = User.objects.filter(
            is_active=False,
            invitation_token__isnull=False,
            accepted_invitation_at__isnull=True,
        )

        if member_state:
            queryset = queryset.filter(ipa_profile__member_state=member_state)

        return queryset.select_related("invited_by")
