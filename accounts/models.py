"""
Enhanced User models for IPAWAS Platform with Dashboard support.

This module extends the existing User and IPAUser models with fields and methods
necessary for the dashboard invitation and access control system.
"""

import secrets

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Custom manager for email-based authentication"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Extended User model for IPAWAS platform.

    Extends Django's AbstractUser to add IPAWAS-specific fields.
    Supports three user types:
    1. IPA Staff (linked to IPAUser profile)
    2. IPAWAS Admin Staff
    3. Public users (future: for investor accounts, newsletters, etc.)
    """

    USER_TYPES = [
        ("ipa_staff", _("IPA Staff")),
        ("ipawas_admin", _("IPAWAS Admin")),
        ("public", _("Public User")),
    ]

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default="public",
        help_text=_("User type determines access level"),
    )

    username = None
    email = models.EmailField(unique=True)

    phone_number = models.CharField(max_length=50, blank=True, help_text=_("Contact phone number"))

    job_title = models.CharField(max_length=200, blank=True, help_text=_("Professional title"))

    organization = models.CharField(
        max_length=200, blank=True, help_text=_("Organization/Company name")
    )

    # Email verification
    email_verified = models.BooleanField(default=False, help_text=_("Has user verified their email?"))

    email_verification_token = models.CharField(
        max_length=100, blank=True, help_text=_("Token for email verification")
    )

    # Two-factor authentication
    two_factor_enabled = models.BooleanField(
        default=False, help_text=_("Is 2FA enabled for this user?")
    )

    two_factor_secret = models.CharField(
        max_length=100, blank=True, help_text=_("TOTP secret for 2FA")
    )

    # Last activity tracking
    last_login_ip = models.GenericIPAddressField(
        null=True, blank=True, help_text=_("IP address of last login")
    )

    last_activity = models.DateTimeField(null=True, blank=True, help_text=_("Last activity timestamp"))

    # Preferences
    language_preference = models.CharField(
        max_length=10,
        choices=[
            ("en", _("English")),
            ("fr", _("French")),
            ("pt", _("Portuguese")),
        ],
        default="en",
        help_text=_("Preferred interface language"),
    )

    timezone = models.CharField(max_length=50, default="UTC", help_text=_("User's timezone"))

    # Notifications
    email_notifications = models.BooleanField(
        default=True, help_text=_("Receive email notifications?")
    )

    # Profile
    profile_picture = models.URLField(
        max_length=500, blank=True, help_text=_("Profile photo URL (AWS S3)")
    )

    bio = models.TextField(blank=True, help_text=_("Short bio (optional)"))

    # DASHBOARD ENHANCEMENTS - Invitation tracking
    invitation_token = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text=_("Token used for registration (if invited)"),
    )

    invited_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_users",
        help_text=_("User who sent the invitation"),
    )

    accepted_invitation_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When user accepted their invitation"),
    )

    # Security
    password_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Last password change timestamp"),
    )

    failed_login_attempts = models.PositiveIntegerField(
        default=0, help_text=_("Counter for failed login attempts")
    )

    account_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Account locked until this time (after failed attempts)"),
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["user_type", "is_active"]),
            models.Index(fields=["-date_joined"]),
            models.Index(fields=["email_verified"]),
            models.Index(fields=["invitation_token"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Return user's full name or email if name not set"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    @property
    def is_ipa_staff(self):
        """Check if user is IPA staff"""
        return self.user_type == "ipa_staff"

    @property
    def is_ipawas_admin(self):
        """Check if user is IPAWAS admin"""
        return self.user_type == "ipawas_admin"

    @property
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False

    def get_ipa_profile(self):
        """Get associated IPA profile if exists"""
        if hasattr(self, "ipa_profile"):
            return self.ipa_profile
        return None

    def record_login(self, ip_address=None):
        """Record successful login"""
        self.last_login = timezone.now()
        self.last_activity = timezone.now()
        if ip_address:
            self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save(
            update_fields=[
                "last_login",
                "last_activity",
                "last_login_ip",
                "failed_login_attempts",
                "account_locked_until",
            ]
        )

    def record_failed_login(self):
        """Record failed login attempt and lock account if necessary"""
        self.failed_login_attempts += 1

        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)

        self.save(update_fields=["failed_login_attempts", "account_locked_until"])

    def generate_password_reset_token(self):
        """Generate secure password reset token"""
        return secrets.token_urlsafe(32)


class IPAUser(models.Model):
    """
    Extended profile for IPA staff users.
    Links User to MemberStateIPA and defines permissions.

    Each IPA has multiple staff with different roles:
    - ipa_director: Full country-level authority
    - ipa_manager: Content & operations — can publish but cannot manage users
    - ipa_officer: Data entry & updates — can draft but not publish
    - ipa_data_entry: Narrowest write access — data submission only
    - ipa_analyst: Read-only — can view and export, cannot create or edit
    """

    IPA_ROLES = [
        ("ipa_director", _("IPA Director")),
        ("ipa_manager", _("IPA Manager")),
        ("ipa_officer", _("IPA Officer")),
        ("ipa_data_entry", _("IPA Data Entry")),
        ("ipa_analyst", _("IPA Analyst")),
    ]

    # Link to User model
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="ipa_profile",
        help_text=_("Associated user account"),
    )

    # Link to Member State (will be imported from members app)
    # This creates a circular dependency, so we use string reference
    member_state = models.ForeignKey(
        "members.MemberStateIPA",
        on_delete=models.CASCADE,
        related_name="ipa_users",
        help_text=_("IPA this user belongs to"),
    )

    role = models.CharField(
        max_length=20,
        choices=IPA_ROLES,
        default="ipa_officer",
        help_text=_("User's role within their IPA"),
    )

    # ENHANCED PERMISSIONS - More granular control
    can_publish_opportunities = models.BooleanField(
        default=False, help_text=_("Can publish opportunities without approval?")
    )

    can_approve_data = models.BooleanField(
        default=False, help_text=_("Can approve WAIIS data submissions?")
    )

    can_manage_users = models.BooleanField(
        default=False, help_text=_("Can create/edit other IPA users?")
    )

    can_edit_profile = models.BooleanField(default=True, help_text=_("Can edit member state profile?"))

    can_manage_sectors = models.BooleanField(
        default=True, help_text=_("Can add/edit priority sectors?")
    )

    can_create_opportunities = models.BooleanField(
        default=True, help_text=_("Can create investment opportunities?")
    )

    can_edit_incentives = models.BooleanField(
        default=True, help_text=_("Can manage investment incentives?")
    )

    can_manage_success_stories = models.BooleanField(
        default=True, help_text=_("Can create/edit success stories?")
    )

    can_view_inquiries = models.BooleanField(default=True, help_text=_("Can view investor inquiries?"))

    can_respond_to_inquiries = models.BooleanField(
        default=True, help_text=_("Can respond to investor inquiries?")
    )

    can_view_analytics = models.BooleanField(
        default=True, help_text=_("Can access analytics dashboard?")
    )

    can_export_data = models.BooleanField(default=False, help_text=_("Can export data and reports?"))

    # Contact
    direct_phone = models.CharField(max_length=50, blank=True, help_text=_("Direct line phone number"))

    extension = models.CharField(max_length=20, blank=True, help_text=_("Phone extension"))

    office_location = models.CharField(
        max_length=200, blank=True, help_text=_("Office location/building")
    )

    # Status
    is_active = models.BooleanField(default=True, help_text=_("Is this IPA user account active?"))

    is_primary_contact = models.BooleanField(
        default=False, help_text=_("Is this the primary focal point?")
    )

    # DASHBOARD ENHANCEMENTS - Onboarding and activity
    dashboard_access_granted_at = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, help_text=_("When dashboard access was granted")
    )

    last_dashboard_login = models.DateTimeField(
        null=True, blank=True, help_text=_("Last time user accessed dashboard")
    )

    dashboard_onboarding_completed = models.BooleanField(
        default=False, help_text=_("Has user completed dashboard tour?")
    )

    onboarding_completed = models.BooleanField(
        default=False, help_text=_("Has user completed onboarding?")
    )

    training_completed = models.BooleanField(
        default=False, help_text=_("Has user completed training?")
    )

    # Notification preferences
    notify_on_inquiry = models.BooleanField(
        default=True, help_text=_("Notify when new inquiry received?")
    )

    notify_on_opportunity_expiry = models.BooleanField(
        default=True, help_text=_("Notify when opportunities are expiring?")
    )

    notify_on_team_changes = models.BooleanField(
        default=True, help_text=_("Notify when team members are added/removed?")
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("IPA User Profile")
        verbose_name_plural = _("IPA User Profiles")
        ordering = ["member_state", "-is_primary_contact", "user__first_name"]
        unique_together = ["user", "member_state"]
        indexes = [
            models.Index(fields=["member_state", "is_active"]),
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["is_primary_contact"]),
            models.Index(fields=["-last_dashboard_login"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.member_state.ipa_acronym} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        """Ensure user type is set to ipa_staff and set permissions based on role"""
        # Ensure user type is set to ipa_staff
        if self.user.user_type != "ipa_staff":
            self.user.user_type = "ipa_staff"
            self.user.save()

        # Auto-set permissions based on role
        if self.role == "ipa_director":
            # Full country-level authority
            self.can_publish_opportunities = True
            self.can_approve_data = True
            self.can_manage_users = True
            self.can_edit_profile = True
            self.can_manage_sectors = True
            self.can_create_opportunities = True
            self.can_edit_incentives = True
            self.can_manage_success_stories = True
            self.can_view_inquiries = True
            self.can_respond_to_inquiries = True
            self.can_view_analytics = True
            self.can_export_data = True
        elif self.role == "ipa_manager":
            # Content & operations — can publish but cannot manage users
            self.can_publish_opportunities = True
            self.can_approve_data = False
            self.can_manage_users = False
            self.can_edit_profile = True
            self.can_manage_sectors = True
            self.can_create_opportunities = True
            self.can_edit_incentives = True
            self.can_manage_success_stories = True
            self.can_view_inquiries = True
            self.can_respond_to_inquiries = True
            self.can_view_analytics = True
            self.can_export_data = True
        elif self.role == "ipa_officer":
            # Data entry & updates — can draft but not publish
            self.can_publish_opportunities = False
            self.can_approve_data = False
            self.can_manage_users = False
            self.can_edit_profile = True
            self.can_manage_sectors = True
            self.can_create_opportunities = True
            self.can_edit_incentives = True
            self.can_manage_success_stories = True
            self.can_view_inquiries = True
            self.can_respond_to_inquiries = True
            self.can_view_analytics = True
            self.can_export_data = False
        elif self.role == "ipa_data_entry":
            # Narrowest write access — data submission only
            self.can_publish_opportunities = False
            self.can_approve_data = False
            self.can_manage_users = False
            self.can_edit_profile = True
            self.can_manage_sectors = False
            self.can_create_opportunities = True
            self.can_edit_incentives = True
            self.can_manage_success_stories = False
            self.can_view_inquiries = False
            self.can_respond_to_inquiries = False
            self.can_view_analytics = False
            self.can_export_data = False
        elif self.role == "ipa_analyst":
            # Read-only — can view and export, cannot create or edit
            self.can_publish_opportunities = False
            self.can_approve_data = False
            self.can_manage_users = False
            self.can_edit_profile = False
            self.can_manage_sectors = False
            self.can_create_opportunities = False
            self.can_edit_incentives = False
            self.can_manage_success_stories = False
            self.can_view_inquiries = True
            self.can_respond_to_inquiries = False
            self.can_view_analytics = True
            self.can_export_data = True

        super().save(*args, **kwargs)

    def record_dashboard_access(self):
        """Record dashboard access timestamp"""
        self.last_dashboard_login = timezone.now()
        self.save(update_fields=["last_dashboard_login"])

    def get_dashboard_url(self):
        """Get URL to user's dashboard"""
        return reverse(
            "dashboard:country:overview",
            kwargs={"member_state_slug": self.member_state.slug},
        )
        # return reverse("dashboard:country:overview")

    def get_permissions_summary(self):
        """Return dict of all permissions for easy checking"""
        return {
            "publish_opportunities": self.can_publish_opportunities,
            "approve_data": self.can_approve_data,
            "manage_users": self.can_manage_users,
            "edit_profile": self.can_edit_profile,
            "manage_sectors": self.can_manage_sectors,
            "create_opportunities": self.can_create_opportunities,
            "edit_incentives": self.can_edit_incentives,
            "manage_success_stories": self.can_manage_success_stories,
            "view_inquiries": self.can_view_inquiries,
            "respond_to_inquiries": self.can_respond_to_inquiries,
            "view_analytics": self.can_view_analytics,
            "export_data": self.can_export_data,
        }

    @property
    def is_director(self):
        return self.role == "ipa_director"

    @property
    def is_manager(self):
        return self.role == "ipa_manager"

    @property
    def is_officer(self):
        return self.role == "ipa_officer"

    @property
    def is_data_entry(self):
        return self.role == "ipa_data_entry"

    @property
    def is_analyst(self):
        return self.role == "ipa_analyst"
