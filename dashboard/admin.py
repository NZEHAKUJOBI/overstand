"""
Django Admin Configuration for Dashboard Models.

This module provides comprehensive admin interfaces for:
- IPADashboardActivity: Activity logging and audit trails
- IPANotification: In-app notification system
"""

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import IPADashboardActivity, IPANotification

# ============================================================================
# DASHBOARD ACTIVITY ADMIN
# ============================================================================


class RecentActivityFilter(admin.SimpleListFilter):
    """Filter activities by time period"""

    title = _("time period")
    parameter_name = "period"

    def lookups(self, request, model_admin):
        return [
            ("today", _("Today")),
            ("week", _("This Week")),
            ("month", _("This Month")),
            ("quarter", _("This Quarter")),
        ]

    def queryset(self, request, queryset):
        from datetime import timedelta

        from django.utils import timezone

        now = timezone.now()

        if self.value() == "today":
            return queryset.filter(timestamp__date=now.date())
        elif self.value() == "week":
            return queryset.filter(timestamp__gte=now - timedelta(days=7))
        elif self.value() == "month":
            return queryset.filter(timestamp__gte=now - timedelta(days=30))
        elif self.value() == "quarter":
            return queryset.filter(timestamp__gte=now - timedelta(days=90))
        return queryset


class ActionTypeFilter(admin.SimpleListFilter):
    """Filter by action category"""

    title = _("action category")
    parameter_name = "action_category"

    def lookups(self, request, model_admin):
        return [
            ("user", _("User Actions")),
            ("content", _("Content Actions")),
            ("opportunity", _("Opportunity Actions")),
            ("inquiry", _("Inquiry Actions")),
            ("team", _("Team Actions")),
            ("system", _("System Actions")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "user":
            return queryset.filter(action_type__in=["login", "logout", "password_change"])
        elif self.value() == "content":
            return queryset.filter(
                action_type__in=["create", "update", "delete", "publish", "unpublish"]
            )
        elif self.value() == "opportunity":
            return queryset.filter(action_type__startswith="opportunity_")
        elif self.value() == "inquiry":
            return queryset.filter(action_type__startswith="inquiry_")
        elif self.value() == "team":
            return queryset.filter(action_type__startswith="user_")
        elif self.value() == "system":
            return queryset.filter(
                action_type__in=["settings_change", "bulk_import", "bulk_update", "export_data"]
            )
        return queryset


@admin.register(IPADashboardActivity)
class IPADashboardActivityAdmin(admin.ModelAdmin):
    """
    Admin interface for Dashboard Activity Logs.

    Features:
    - Comprehensive filtering and search
    - Read-only interface (audit logs shouldn't be modified)
    - Timeline view of activities
    - Export functionality
    """

    # Display configuration
    list_display = [
        "timestamp_display",
        "user_link",
        "action_badge",
        "description_short",
        "member_state_link",
        "content_object_link",
        "ip_address",
    ]

    list_filter = [
        RecentActivityFilter,
        ActionTypeFilter,
        "action_type",
        "member_state",
        ("timestamp", admin.DateFieldListFilter),
    ]

    search_fields = [
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "description",
        "ip_address",
    ]

    # Read-only fields (audit logs should never be edited)
    readonly_fields = [
        "user",
        "member_state",
        "action_type",
        "content_type",
        "object_id",
        "content_object",
        "description",
        "changes_display",
        "ip_address",
        "user_agent_display",
        "timestamp",
    ]

    # Fieldsets for detail view
    fieldsets = [
        (
            _("Activity Information"),
            {
                "fields": [
                    "timestamp",
                    "user",
                    "member_state",
                    "action_type",
                ]
            },
        ),
        (
            _("Details"),
            {
                "fields": [
                    "description",
                    "content_type",
                    "object_id",
                    "content_object",
                    "changes_display",
                ]
            },
        ),
        (
            _("Request Metadata"),
            {
                "fields": [
                    "ip_address",
                    "user_agent_display",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    # Disable add/delete permissions
    def has_add_permission(self, request):
        """Activities should only be created programmatically"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs should not be deleted"""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Audit logs should be read-only"""
        return False

    # Date hierarchy
    date_hierarchy = "timestamp"

    # Ordering
    ordering = ["-timestamp"]

    # Custom display methods
    def timestamp_display(self, obj):
        """Display timestamp with icon"""
        return format_html(
            '<i class="far fa-clock"></i> {}',
            obj.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        )

    timestamp_display.short_description = _("Time")
    timestamp_display.admin_order_field = "timestamp"

    def user_link(self, obj):
        """Display user as clickable link"""
        if obj.user:
            url = reverse("admin:auth_user_change", args=[obj.user.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.user.get_full_name() or obj.user.username,
            )
        return _("Unknown User")

    user_link.short_description = _("User")
    user_link.admin_order_field = "user"

    def action_badge(self, obj):
        """Display action type as colored badge"""
        color_map = {
            "login": "success",
            "logout": "secondary",
            "create": "primary",
            "update": "info",
            "delete": "danger",
            "publish": "success",
            "approve": "success",
            "reject": "danger",
        }
        color = color_map.get(obj.action_type, "secondary")

        return format_html(
            '<span class="badge badge-{}" style="background-color: {};">'
            '<i class="{}"></i> {}'
            "</span>",
            color,
            self._get_badge_color(color),
            obj.get_icon_class(),
            obj.get_action_type_display(),
        )

    action_badge.short_description = _("Action")
    action_badge.admin_order_field = "action_type"

    def _get_badge_color(self, badge_type):
        """Get hex color for badge type"""
        colors = {
            "primary": "#007bff",
            "success": "#28a745",
            "info": "#17a2b8",
            "warning": "#ffc107",
            "danger": "#dc3545",
            "secondary": "#6c757d",
        }
        return colors.get(badge_type, "#6c757d")

    def description_short(self, obj):
        """Display shortened description"""
        if len(obj.description) > 100:
            return format_html(
                '<span title="{}">{}</span>',
                obj.description,
                obj.description[:100] + "...",
            )
        return obj.description

    description_short.short_description = _("Description")

    def member_state_link(self, obj):
        """Display member state as link"""
        if obj.member_state:
            url = reverse("admin:members_memberstateipa_change", args=[obj.member_state.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.member_state.ipa_acronym,
            )
        return "-"

    member_state_link.short_description = _("Member State")
    member_state_link.admin_order_field = "member_state"

    def content_object_link(self, obj):
        """Display content object as link if possible"""
        if obj.content_object:
            try:
                content_type = obj.content_type
                model_name = content_type.model
                app_label = content_type.app_label
                url = reverse(
                    f"admin:{app_label}_{model_name}_change",
                    args=[obj.object_id],
                )
                return format_html(
                    '<a href="{}">{}</a>',
                    url,
                    str(obj.content_object)[:50],
                )
            except Exception:
                return str(obj.content_object)[:50]
        return "-"

    content_object_link.short_description = _("Related Object")

    def changes_display(self, obj):
        """Display changes in formatted JSON"""
        if not obj.changes_json:
            return _("No changes recorded")

        html = '<table class="table table-sm">'
        html += "<thead><tr><th>Field</th><th>Old Value</th><th>New Value</th></tr></thead>"
        html += "<tbody>"

        for field, change in obj.changes_json.items():
            if isinstance(change, dict) and "old" in change and "new" in change:
                html += f"<tr><td><strong>{field}</strong></td>"
                html += f"<td>{change['old']}</td>"
                html += f"<td>{change['new']}</td></tr>"
            else:
                html += f"<tr><td colspan='3'><strong>{field}:</strong> {change}</td></tr>"

        html += "</tbody></table>"
        return mark_safe(html)

    changes_display.short_description = _("Changes")

    def user_agent_display(self, obj):
        """Display user agent in readable format"""
        if not obj.user_agent:
            return "-"
        return format_html("<pre>{}</pre>", obj.user_agent)

    user_agent_display.short_description = _("User Agent")

    # Actions
    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        """Export selected activities as CSV"""
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="activities.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Timestamp",
                "User",
                "Action",
                "Description",
                "Member State",
                "IP Address",
            ]
        )

        for activity in queryset:
            writer.writerow(
                [
                    activity.timestamp,
                    activity.user.get_full_name() if activity.user else "Unknown",
                    activity.get_action_type_display(),
                    activity.description,
                    activity.member_state.ipa_acronym if activity.member_state else "",
                    activity.ip_address or "",
                ]
            )

        return response

    export_as_csv.short_description = _("Export selected as CSV")


# ============================================================================
# NOTIFICATION ADMIN
# ============================================================================


class ReadStatusFilter(admin.SimpleListFilter):
    """Filter notifications by read status"""

    title = _("read status")
    parameter_name = "read_status"

    def lookups(self, request, model_admin):
        return [
            ("unread", _("Unread")),
            ("read", _("Read")),
            ("read_today", _("Read Today")),
        ]

    def queryset(self, request, queryset):
        from django.utils import timezone

        if self.value() == "unread":
            return queryset.filter(is_read=False)
        elif self.value() == "read":
            return queryset.filter(is_read=True)
        elif self.value() == "read_today":
            return queryset.filter(is_read=True, read_at__date=timezone.now().date())
        return queryset


@admin.register(IPANotification)
class IPANotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for IPA Notifications.

    Features:
    - Create notifications for users
    - Filter by read status and type
    - Bulk mark as read/unread
    - Send notification actions
    """

    # Display configuration
    list_display = [
        "created_display",
        "recipient_link",
        "notification_badge",
        "title",
        "read_status_badge",
        "read_at_display",
    ]

    list_filter = [
        ReadStatusFilter,
        "notification_type",
        "is_read",
        ("created_at", admin.DateFieldListFilter),
        ("read_at", admin.DateFieldListFilter),
    ]

    search_fields = [
        "recipient__user__username",
        "recipient__user__email",
        "recipient__user__first_name",
        "recipient__user__last_name",
        "title",
        "message",
    ]

    # Fieldsets
    fieldsets = [
        (
            _("Notification Information"),
            {
                "fields": [
                    "recipient",
                    "notification_type",
                    "title",
                    "message",
                    "link_url",
                ]
            },
        ),
        (
            _("Read Status"),
            {
                "fields": [
                    "is_read",
                    "read_at",
                ]
            },
        ),
        (
            _("Metadata"),
            {
                "fields": [
                    "created_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    readonly_fields = ["created_at", "read_at"]

    # Date hierarchy
    date_hierarchy = "created_at"

    # Ordering
    ordering = ["-created_at"]

    # Raw ID fields for performance
    raw_id_fields = ["recipient"]
    autocomplete_fields = ["recipient"]

    # Custom display methods
    def created_display(self, obj):
        """Display creation time with age"""
        return format_html(
            '<i class="far fa-clock"></i> {}<br><small class="text-muted">{}</small>',
            obj.created_at.strftime("%Y-%m-%d %H:%M"),
            obj.age,
        )

    created_display.short_description = _("Created")
    created_display.admin_order_field = "created_at"

    def recipient_link(self, obj):
        """Display recipient as link"""
        url = reverse("admin:accounts_ipauser_change", args=[obj.recipient.pk])
        return format_html(
            '<a href="{}">{}</a><br><small class="text-muted">{}</small>',
            url,
            obj.recipient.user.get_full_name(),
            obj.recipient.member_state.ipa_acronym,
        )

    recipient_link.short_description = _("Recipient")
    recipient_link.admin_order_field = "recipient"

    def notification_badge(self, obj):
        """Display notification type as colored badge"""
        return format_html(
            '<span class="badge badge-{}" style="background-color: {};">'
            '<i class="{}"></i> {}'
            "</span>",
            obj.get_badge_class(),
            self._get_badge_color(obj.get_badge_class()),
            obj.get_icon_class(),
            obj.get_notification_type_display(),
        )

    notification_badge.short_description = _("Type")
    notification_badge.admin_order_field = "notification_type"

    def _get_badge_color(self, badge_type):
        """Get hex color for badge type"""
        colors = {
            "primary": "#007bff",
            "success": "#28a745",
            "info": "#17a2b8",
            "warning": "#ffc107",
            "danger": "#dc3545",
            "secondary": "#6c757d",
        }
        return colors.get(badge_type, "#6c757d")

    def read_status_badge(self, obj):
        """Display read status as badge"""
        if obj.is_read:
            return format_html(
                '<span class="badge badge-success" style="background-color: #28a745;">'
                '<i class="fas fa-check"></i> Read'
                "</span>"
            )
        else:
            return format_html(
                '<span class="badge badge-warning" style="background-color: #ffc107;">'
                '<i class="fas fa-envelope"></i> Unread'
                "</span>"
            )

    read_status_badge.short_description = _("Status")
    read_status_badge.admin_order_field = "is_read"

    def read_at_display(self, obj):
        """Display when notification was read"""
        if obj.read_at:
            return obj.read_at.strftime("%Y-%m-%d %H:%M")
        return "-"

    read_at_display.short_description = _("Read At")
    read_at_display.admin_order_field = "read_at"

    # Actions
    actions = [
        "mark_as_read",
        "mark_as_unread",
        "delete_read_notifications",
        "export_as_csv",
    ]

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        from django.utils import timezone

        count = queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        self.message_user(request, f"{count} notification(s) marked as read.")

    mark_as_read.short_description = _("Mark selected as read")

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        count = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f"{count} notification(s) marked as unread.")

    mark_as_unread.short_description = _("Mark selected as unread")

    def delete_read_notifications(self, request, queryset):
        """Delete notifications that have been read"""
        count, _ = queryset.filter(is_read=True).delete()
        self.message_user(request, f"{count} read notification(s) deleted.")

    delete_read_notifications.short_description = _("Delete read notifications")

    def export_as_csv(self, request, queryset):
        """Export selected notifications as CSV"""
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="notifications.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Created At",
                "Recipient",
                "Type",
                "Title",
                "Message",
                "Is Read",
                "Read At",
            ]
        )

        for notification in queryset:
            writer.writerow(
                [
                    notification.created_at,
                    notification.recipient.user.get_full_name(),
                    notification.get_notification_type_display(),
                    notification.title,
                    notification.message,
                    "Yes" if notification.is_read else "No",
                    notification.read_at if notification.read_at else "",
                ]
            )

        return response

    export_as_csv.short_description = _("Export selected as CSV")

    # Custom queryset to optimize queries
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return (
            super()
            .get_queryset(request)
            .select_related("recipient__user", "recipient__member_state")
        )
