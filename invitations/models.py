"""
Invitation System Models for IPAWAS Platform.

This module handles the invite-only registration system for IPA staff.
Invitations are token-based, time-limited, and single-use.
"""

import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class InvitationManager(models.Manager):
    """Custom manager for Invitation model with convenience methods"""

    def create_invitation(
        self,
        email,
        invited_by,
        member_state=None,
        role="",
        user_type="ipa_staff",
        is_primary_contact=False,
        invitation_message="",
        expires_in_days=None,
    ):
        """
        Create a new invitation with auto-generated token.

        Args:
            email: Email address to invite
            invited_by: User who is sending the invitation
            member_state: MemberStateIPA instance (None for HQ admin invitations)
            role: IPA role (ipa_director, ipa_manager, ipa_officer, ipa_data_entry, ipa_analyst)
                  Empty string for HQ admin invitations.
            user_type: 'ipa_staff' (default) or 'ipawas_admin' for HQ staff
            is_primary_contact: Whether this is the primary contact
            invitation_message: Optional personalized message
            expires_in_days: Days until expiration (default from settings)

        Returns:
            Invitation instance
        """
        if expires_in_days is None:
            expires_in_days = getattr(settings, "INVITATION_EXPIRY_DAYS", 7)

        # Convert string to integer
        expires_in_days = int(expires_in_days)

        normalized_email = email.lower().strip()

        # Check for an existing pending invitation before hitting the DB constraint,
        # so the user gets a friendly message instead of a raw constraint name.
        if member_state is not None:
            if self.filter(
                email=normalized_email, member_state=member_state, status="pending"
            ).exists():
                raise ValidationError(
                    _(
                        "A pending invitation has already been sent to %(email)s for %(state)s. "
                        "You can resend or revoke it from the invitations list."
                    )
                    % {"email": normalized_email, "state": member_state.ipa_acronym}
                )
        else:
            if self.filter(
                email=normalized_email, member_state__isnull=True, status="pending"
            ).exists():
                raise ValidationError(
                    _("A pending HQ admin invitation has already been sent to %(email)s.")
                    % {"email": normalized_email}
                )

        invitation = self.create(
            email=normalized_email,
            token=uuid.uuid4(),
            member_state=member_state,
            role=role,
            user_type=user_type,
            invited_by=invited_by,
            invited_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=expires_in_days),
            status="pending",
            is_primary_contact=is_primary_contact,
            invitation_message=invitation_message,
        )

        return invitation

    def get_pending_invitations(self, member_state=None):
        """Get all pending invitations, optionally filtered by member state"""
        queryset = self.filter(status="pending", expires_at__gt=timezone.now())
        if member_state:
            queryset = queryset.filter(member_state=member_state)
        return queryset

    def get_expired_invitations(self):
        """Get all expired invitations that haven't been cleaned up"""
        return self.filter(status="pending", expires_at__lte=timezone.now())

    def cleanup_expired(self):
        """Mark expired invitations as expired"""
        expired = self.get_expired_invitations()
        count = expired.update(status="expired")
        return count

    def get_by_token(self, token):
        """Get invitation by token, raising 404 if not found or invalid"""
        try:
            invitation = self.get(token=token, status="pending")
            if invitation.is_expired:
                invitation.status = "expired"
                invitation.save()
                raise ValidationError(_("This invitation has expired."))
            return invitation
        except self.model.DoesNotExist:
            raise ValidationError(_("Invalid or expired invitation token."))


class Invitation(models.Model):
    """
    Invitation model for token-based IPA staff onboarding.

    Think of this as an official appointment letter that:
    - Specifies the role and member state (embassy)
    - Has an expiration date
    - Can only be used once
    - Tracks who sent it and when

    Lifecycle:
    1. Created by IPAWAS admin or IPA admin
    2. Email sent to recipient with registration link
    3. Recipient clicks link and registers
    4. Status changes to 'accepted'
    5. User account and IPAUser profile created
    """

    INVITATION_STATUS = [
        ("pending", _("Pending")),
        ("accepted", _("Accepted")),
        ("expired", _("Expired")),
        ("revoked", _("Revoked")),
    ]

    # Core fields
    email = models.EmailField(
        max_length=255,
        help_text=_("Email address of person being invited"),
        db_index=True,
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text=_("Unique token for invitation link"),
    )

    member_state = models.ForeignKey(
        "members.MemberStateIPA",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="invitations",
        help_text=_("Member State IPA this invitation is for (null for HQ admin invitations)"),
    )

    role = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("ipa_director", _("IPA Director")),
            ("ipa_manager", _("IPA Manager")),
            ("ipa_officer", _("IPA Officer")),
            ("ipa_data_entry", _("IPA Data Entry")),
            ("ipa_analyst", _("IPA Analyst")),
        ],
        help_text=_("Role the invitee will have (blank for HQ admin invitations)"),
    )

    user_type = models.CharField(
        max_length=20,
        choices=[
            ("ipa_staff", _("IPA Staff")),
            ("ipawas_admin", _("IPAWAS HQ Admin")),
        ],
        default="ipa_staff",
        help_text=_("Type of user account to create on registration"),
    )

    # Invitation lifecycle
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
        help_text=_("User who sent this invitation"),
    )

    invited_at = models.DateTimeField(auto_now_add=True, help_text=_("When invitation was created"))

    expires_at = models.DateTimeField(
        help_text=_("When invitation expires"),
        db_index=True,
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=INVITATION_STATUS,
        default="pending",
        help_text=_("Current status of invitation"),
        db_index=True,
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When invitation was accepted"),
    )

    created_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitation_used",
        help_text=_("User account created from this invitation"),
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When invitation was revoked"),
    )

    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_invitations",
        help_text=_("User who revoked this invitation"),
    )

    revoke_reason = models.TextField(
        blank=True,
        help_text=_("Reason for revoking invitation"),
    )

    # Additional information
    is_primary_contact = models.BooleanField(
        default=False,
        help_text=_("Is this person the primary IPA contact?"),
    )

    invitation_message = models.TextField(
        blank=True,
        help_text=_("Optional personalized message to include in email"),
    )

    # Tracking
    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When invitation email was sent"),
    )

    email_opened_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When invitation email was opened (if tracking enabled)"),
    )

    registration_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When recipient started registration"),
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom manager
    objects = InvitationManager()

    class Meta:
        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")
        ordering = ["-invited_at"]
        indexes = [
            models.Index(fields=["email", "status"]),
            models.Index(fields=["token"]),
            models.Index(fields=["member_state", "status"]),
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["-invited_at"]),
        ]
        constraints = [
            # Only one pending invitation per email per member state (IPA staff)
            models.UniqueConstraint(
                fields=["email", "member_state"],
                condition=models.Q(status="pending", member_state__isnull=False),
                name="unique_pending_invitation_per_email_state",
            ),
            # Only one pending HQ admin invitation per email (member_state is NULL)
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(status="pending", member_state__isnull=True),
                name="unique_pending_hq_invitation_per_email",
            ),
        ]

    def __str__(self):
        destination = self.member_state.ipa_acronym if self.member_state else "HQ Admin"
        return f"{self.email} → {destination} ({self.get_status_display()})"

    def clean(self):
        """Validate invitation data"""
        super().clean()

        from accounts.models import IPAUser, User

        # HQ admin invitations must use user_type='ipawas_admin' and have no role
        if self.member_state is None:
            if self.user_type != "ipawas_admin":
                raise ValidationError(
                    _("Invitations without a member state must use user_type='ipawas_admin'")
                )
        else:
            # IPA staff invitations must have a role
            if not self.role:
                raise ValidationError(
                    _("A role is required for IPA staff invitations")
                )
            # HQ admin user_type must not have a member state
            if self.user_type == "ipawas_admin":
                raise ValidationError(
                    _("HQ admin invitations must not have a member state assigned")
                )

        if self.status == "pending":
            # Check if user already exists with this email
            existing_user = User.objects.filter(email=self.email).first()
            if existing_user and self.member_state:
                # Check if they're already staff for this member state
                if IPAUser.objects.filter(
                    user=existing_user, member_state=self.member_state
                ).exists():
                    raise ValidationError(
                        _(
                            f"A user with email {self.email} already has access to {self.member_state.ipa_acronym}"
                        )
                    )

        # Ensure expires_at is in the future
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError(_("Expiration date must be in the future"))

    def save(self, *args, **kwargs):
        """Save with validation.

        full_clean() is only run on full saves (not update_fields partial saves).
        Partial saves via accept(), revoke(), resend(), mark_*() bypass validation
        intentionally — they only touch specific, already-validated fields.
        """
        if "update_fields" not in kwargs:
            self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if invitation has expired"""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """Check if invitation is valid and can be used"""
        return self.status == "pending" and not self.is_expired

    @property
    def days_until_expiry(self):
        """Get days remaining until expiration"""
        if self.is_expired:
            return 0
        delta = self.expires_at - timezone.now()
        return delta.days

    @property
    def hours_until_expiry(self):
        """Get hours remaining until expiration"""
        if self.is_expired:
            return 0
        delta = self.expires_at - timezone.now()
        return delta.total_seconds() / 3600

    def get_registration_url(self):
        """Get the full registration URL with token"""
        return reverse("dashboard:invitations:register", kwargs={"token": self.token})

    def get_absolute_url(self):
        """Get URL to view invitation details"""
        return reverse("dashboard:invitations:detail", kwargs={"pk": self.pk})

    def accept(self, user):
        """
        Mark invitation as accepted.

        Args:
            user: The User instance created from this invitation
        """
        if self.status != "pending":
            raise ValidationError(_("Only pending invitations can be accepted"))

        if self.is_expired:
            raise ValidationError(_("This invitation has expired"))

        self.status = "accepted"
        self.accepted_at = timezone.now()
        self.created_user = user
        self.save(update_fields=["status", "accepted_at", "created_user", "updated_at"])

    def revoke(self, revoked_by, reason=""):
        """
        Revoke invitation.

        Args:
            revoked_by: User who is revoking the invitation
            reason: Optional reason for revocation
        """
        if self.status != "pending":
            raise ValidationError(_("Only pending invitations can be revoked"))

        self.status = "revoked"
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.revoke_reason = reason
        self.save(
            update_fields=["status", "revoked_at", "revoked_by", "revoke_reason", "updated_at"]
        )

    def resend(self):
        """
        Resend invitation email by extending expiration.

        Returns:
            bool: True if successfully resent
        """
        if self.status != "pending":
            return False

        # Extend expiration by configured days
        days = getattr(settings, "INVITATION_EXPIRY_DAYS", 7)
        self.expires_at = timezone.now() + timedelta(days=days)
        self.email_sent_at = None  # Will be set when email is actually sent
        self.save(update_fields=["expires_at", "email_sent_at", "updated_at"])

        return True

    def mark_email_sent(self):
        """Mark that invitation email has been sent"""
        self.email_sent_at = timezone.now()
        self.save(update_fields=["email_sent_at", "updated_at"])

    def mark_email_opened(self):
        """Mark that invitation email was opened"""
        if not self.email_opened_at:
            self.email_opened_at = timezone.now()
            self.save(update_fields=["email_opened_at", "updated_at"])

    def mark_registration_started(self):
        """Mark that recipient has started registration process"""
        if not self.registration_started_at:
            self.registration_started_at = timezone.now()
            self.save(update_fields=["registration_started_at", "updated_at"])

    def get_status_badge_class(self):
        """Get Bootstrap badge class for status display"""
        status_classes = {
            "pending": "warning",
            "accepted": "success",
            "expired": "secondary",
            "revoked": "danger",
        }
        return status_classes.get(self.status, "secondary")

    def can_be_resent(self):
        """Check if invitation can be resent"""
        return self.status == "pending" and self.days_until_expiry <= 2

    def get_inviter_name(self):
        """Get name of person who sent invitation"""
        if self.invited_by:
            return self.invited_by.get_full_name()
        return _("System Administrator")
