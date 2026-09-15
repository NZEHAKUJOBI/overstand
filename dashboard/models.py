"""
Activity Logging and Notification Models for IPAWAS Platform.

This module provides comprehensive audit logging and in-app notifications
for dashboard activities.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class IPADashboardActivityManager(models.Manager):
    """Custom manager for activity logs with convenience methods"""

    def log_activity(
        self,
        user,
        action_type,
        description,
        member_state=None,
        content_object=None,
        changes=None,
        ip_address=None,
        user_agent=None,
    ):
        """
        Log a dashboard activity.

        Args:
            user: User performing the action
            action_type: Type of action (create, update, delete, etc.)
            description: Human-readable description
            member_state: Related member state (optional)
            content_object: Related object (optional)
            changes: Dict of before/after changes (optional)
            ip_address: IP address of user (optional)
            user_agent: User agent string (optional)

        Returns:
            IPADashboardActivity instance
        """
        activity = self.create(
            user=user,
            member_state=member_state,
            action_type=action_type,
            description=description,
            changes_json=changes or {},
            ip_address=ip_address,
            user_agent=user_agent or "",
        )

        if content_object:
            activity.content_type = ContentType.objects.get_for_model(content_object)
            activity.object_id = content_object.pk
            activity.save()

        return activity

    def get_recent_activities(self, member_state=None, user=None, days=7):
        """Get recent activities, optionally filtered"""
        since = timezone.now() - timezone.timedelta(days=days)
        queryset = self.filter(timestamp__gte=since)

        if member_state:
            queryset = queryset.filter(member_state=member_state)
        if user:
            queryset = queryset.filter(user=user)

        return queryset.select_related("user", "member_state")

    def get_user_activities(self, user, limit=50):
        """Get activities for a specific user"""
        return self.filter(user=user).select_related("member_state")[:limit]

    def get_member_state_activities(self, member_state, limit=100):
        """Get activities for a specific member state"""
        return self.filter(member_state=member_state).select_related("user")[:limit]


class IPADashboardActivity(models.Model):
    """
    Comprehensive audit log for all dashboard activities.

    Essential for:
    - Compliance and auditing
    - Tracking changes
    - Debugging issues
    - Understanding user behavior
    - Security monitoring
    """

    ACTION_TYPES = [
        # User actions
        ("login", _("User Login")),
        ("logout", _("User Logout")),
        ("password_change", _("Password Changed")),
        # Profile actions
        ("profile_update", _("Profile Updated")),
        ("profile_view", _("Profile Viewed")),
        # Content actions
        ("create", _("Created")),
        ("update", _("Updated")),
        ("delete", _("Deleted")),
        ("publish", _("Published")),
        ("unpublish", _("Unpublished")),
        ("approve", _("Approved")),
        ("reject", _("Rejected")),
        # Opportunity actions
        ("opportunity_create", _("Opportunity Created")),
        ("opportunity_update", _("Opportunity Updated")),
        ("opportunity_publish", _("Opportunity Published")),
        ("opportunity_delete", _("Opportunity Deleted")),
        # Inquiry actions
        ("inquiry_view", _("Inquiry Viewed")),
        ("inquiry_respond", _("Inquiry Responded")),
        ("inquiry_assign", _("Inquiry Assigned")),
        ("inquiry_close", _("Inquiry Closed")),
        # Team actions
        ("user_invite", _("User Invited")),
        ("user_create", _("User Created")),
        ("user_update", _("User Updated")),
        ("user_deactivate", _("User Deactivated")),
        ("permission_change", _("Permissions Changed")),
        # Export actions
        ("export_data", _("Data Exported")),
        ("export_report", _("Report Exported")),
        # System actions
        ("settings_change", _("Settings Changed")),
        ("bulk_import", _("Bulk Import")),
        ("bulk_update", _("Bulk Update")),
        ("bulk_invitation", _("Bulk Invitation Sent")),
        # Dashboard view events
        ("viewed_dashboard", _("Dashboard Viewed")),
        ("viewed_member_state_detail", _("Member State Detail Viewed")),
        ("viewed_user_detail", _("User Detail Viewed")),
        # Extended opportunity actions
        ("published_opportunity", _("Opportunity Published (direct)")),
        ("unpublished_opportunity", _("Opportunity Unpublished")),
        ("created_opportunity", _("Opportunity Created as Draft")),
        ("featured_opportunity", _("Opportunity Featured")),
        ("unfeatured_opportunity", _("Opportunity Unfeatured")),
        # Extended user actions
        ("updated_user", _("User Updated")),
        ("updated_permissions", _("Permissions Updated")),
        ("activate_user", _("User Activated")),
        ("deactivate_user", _("User Deactivated")),
        ("reset_password_user", _("User Password Reset")),
        # Knowledge hub actions
        ("created_news", _("News Article Created")),
        ("updated_news", _("News Article Updated")),
        ("deleted_news", _("News Article Deleted")),
    ]

    # Core fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="dashboard_activities",
        help_text=_("User who performed the action"),
    )

    member_state = models.ForeignKey(
        "members.MemberStateIPA",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dashboard_activities",
        help_text=_("Related member state"),
    )

    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        help_text=_("Type of action performed"),
        db_index=True,
    )

    # Generic relation to any object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # Activity details
    description = models.TextField(help_text=_("Human-readable description of the action"))

    changes_json = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("JSON representation of before/after changes"),
    )

    # Request metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_("IP address of the user"),
    )

    user_agent = models.TextField(
        blank=True,
        help_text=_("User agent string from request"),
    )

    # Metadata
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When this activity occurred"),
        db_index=True,
    )

    # Custom manager
    objects = IPADashboardActivityManager()

    class Meta:
        verbose_name = _("Dashboard Activity")
        verbose_name_plural = _("Dashboard Activities")
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["member_state", "-timestamp"]),
            models.Index(fields=["action_type", "-timestamp"]),
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else "Unknown User"
        return f"{user_name} - {self.get_action_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def get_content_object_display(self):
        """Get display name for the related object"""
        if self.content_object:
            return str(self.content_object)
        return _("N/A")

    def get_changes_summary(self):
        """Get human-readable summary of changes"""
        if not self.changes_json:
            return _("No changes recorded")

        summary = []
        for field, change in self.changes_json.items():
            if isinstance(change, dict) and "old" in change and "new" in change:
                summary.append(f"{field}: {change['old']} → {change['new']}")
            else:
                summary.append(f"{field}: {change}")

        return "; ".join(summary)

    def get_icon_class(self):
        """Get Font Awesome icon class for action type"""
        icon_map = {
            "login": "fa-sign-in-alt",
            "logout": "fa-sign-out-alt",
            "create": "fa-plus-circle",
            "update": "fa-edit",
            "delete": "fa-trash-alt",
            "publish": "fa-paper-plane",
            "approve": "fa-check-circle",
            "reject": "fa-times-circle",
            "export_data": "fa-download",
            "user_invite": "fa-user-plus",
        }
        return icon_map.get(self.action_type, "fa-info-circle")


class IPANotificationManager(models.Manager):
    """Custom manager for notifications"""

    def create_notification(
        self,
        recipient,
        notification_type,
        title,
        message,
        link_url=None,
    ):
        """
        Create a new notification.

        Args:
            recipient: IPAUser who will receive notification
            notification_type: Type of notification
            title: Short title
            message: Full message
            link_url: Optional link to related page

        Returns:
            IPANotification instance
        """
        return self.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            link_url=link_url or "",
        )

    def get_unread(self, recipient):
        """Get unread notifications for a user"""
        return self.filter(recipient=recipient, is_read=False).order_by("-created_at")

    def get_recent(self, recipient, days=30):
        """Get recent notifications for a user"""
        since = timezone.now() - timezone.timedelta(days=days)
        return self.filter(recipient=recipient, created_at__gte=since)

    def mark_all_read(self, recipient):
        """Mark all notifications as read for a user"""
        return self.filter(recipient=recipient, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )


class IPANotification(models.Model):
    """
    In-dashboard notifications for IPA staff.

    Like an internal memo system for:
    - New investor inquiries
    - Approval requests
    - System alerts
    - Team updates
    - Opportunity expirations
    """

    NOTIFICATION_TYPES = [
        ("inquiry", _("New Investor Inquiry")),
        ("inquiry_response", _("Inquiry Response")),
        ("approval_needed", _("Approval Needed")),
        ("approved", _("Content Approved")),
        ("rejected", _("Content Rejected")),
        ("opportunity_expiring", _("Opportunity Expiring")),
        ("team_member_added", _("Team Member Added")),
        ("team_member_removed", _("Team Member Removed")),
        ("permission_changed", _("Your Permissions Changed")),
        ("system_alert", _("System Alert")),
        ("announcement", _("Announcement")),
        ("reminder", _("Reminder")),
    ]

    # Core fields
    recipient = models.ForeignKey(
        "accounts.IPAUser",
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text=_("IPA user receiving this notification"),
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        help_text=_("Type of notification"),
        db_index=True,
    )

    title = models.CharField(
        max_length=200,
        help_text=_("Short notification title"),
    )

    message = models.TextField(
        help_text=_("Full notification message"),
    )

    # Optional link
    link_url = models.URLField(
        max_length=500,
        blank=True,
        help_text=_("Optional link to relevant page"),
    )

    # Read status
    is_read = models.BooleanField(
        default=False,
        help_text=_("Has notification been read?"),
        db_index=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When notification was read"),
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When notification was created"),
        db_index=True,
    )

    # Custom manager
    objects = IPANotificationManager()

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["notification_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.recipient.user.get_full_name()} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=["is_read", "read_at"])

    def get_icon_class(self):
        """Get Font Awesome icon class for notification type"""
        icon_map = {
            "inquiry": "fa-envelope",
            "inquiry_response": "fa-reply",
            "approval_needed": "fa-clock",
            "approved": "fa-check-circle",
            "rejected": "fa-times-circle",
            "opportunity_expiring": "fa-exclamation-triangle",
            "team_member_added": "fa-user-plus",
            "team_member_removed": "fa-user-minus",
            "permission_changed": "fa-key",
            "system_alert": "fa-bell",
            "announcement": "fa-bullhorn",
            "reminder": "fa-calendar-check",
        }
        return icon_map.get(self.notification_type, "fa-info-circle")

    def get_badge_class(self):
        """Get Bootstrap badge class for notification type"""
        badge_map = {
            "inquiry": "primary",
            "approval_needed": "warning",
            "approved": "success",
            "rejected": "danger",
            "opportunity_expiring": "warning",
            "team_member_added": "info",
            "system_alert": "danger",
            "announcement": "info",
        }
        return badge_map.get(self.notification_type, "secondary")

    @property
    def age(self):
        """Get human-readable age of notification"""
        delta = timezone.now() - self.created_at

        if delta.days > 30:
            return f"{delta.days // 30} month{'s' if delta.days // 30 != 1 else ''} ago"
        elif delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
