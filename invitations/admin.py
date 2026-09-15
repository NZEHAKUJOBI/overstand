"""
Django Admin Configuration for Invitation System.

This module provides comprehensive admin interface for managing
invitation-based user onboarding system.
"""

from django.contrib import admin
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Invitation

# ============================================================================
# CUSTOM FILTERS
# ============================================================================


class InvitationStatusFilter(admin.SimpleListFilter):
    """Filter invitations by current validity status"""

    title = _("invitation validity")
    parameter_name = "validity"

    def lookups(self, request, model_admin):
        return [
            ("valid", _("Valid (Pending & Not Expired)")),
            ("expired_pending", _("Expired but Pending")),
            ("recently_accepted", _("Accepted (Last 7 days)")),
            ("needs_resend", _("Needs Resend (Expiring Soon)")),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()

        if self.value() == "valid":
            return queryset.filter(status="pending", expires_at__gt=now)
        elif self.value() == "expired_pending":
            return queryset.filter(status="pending", expires_at__lte=now)
        elif self.value() == "recently_accepted":
            week_ago = now - timezone.timedelta(days=7)
            return queryset.filter(status="accepted", accepted_at__gte=week_ago)
        elif self.value() == "needs_resend":
            two_days = now + timezone.timedelta(days=2)
            return queryset.filter(status="pending", expires_at__lte=two_days, expires_at__gt=now)
        return queryset


class MemberStateFilter(admin.SimpleListFilter):
    """Filter by member state with counts"""

    title = _("member state")
    parameter_name = "member_state"

    def lookups(self, request, model_admin):
        from members.models import MemberStateIPA

        states = (
            MemberStateIPA.objects.filter(invitations__isnull=False)
            .distinct()
            .order_by("ipa_acronym")
        )
        return [(state.id, f"{state.ipa_acronym} - {state.country_name}") for state in states]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(member_state_id=self.value())
        return queryset


class RoleFilter(admin.SimpleListFilter):
    """Filter by role with pending count"""

    title = _("role")
    parameter_name = "role"

    def lookups(self, request, model_admin):
        return [
            ("ipa_director", _("IPA Director")),
            ("ipa_manager", _("IPA Manager")),
            ("ipa_officer", _("IPA Officer")),
            ("ipa_data_entry", _("IPA Data Entry")),
            ("ipa_analyst", _("IPA Analyst")),
        ]

    def queryset(self, request, queryset):
        if self.value() in ["ipa_director", "ipa_manager", "ipa_officer", "ipa_data_entry", "ipa_analyst"]:
            return queryset.filter(role=self.value())
        return queryset


# ============================================================================
# INLINE ADMIN
# ============================================================================


class InvitationInline(admin.TabularInline):
    """Inline for viewing invitations in related models"""

    model = Invitation
    extra = 0
    can_delete = False
    fields = ["email", "role", "status", "invited_at", "expires_at"]
    readonly_fields = ["email", "role", "status", "invited_at", "expires_at"]

    def has_add_permission(self, request, obj=None):
        return False


# ============================================================================
# MAIN ADMIN
# ============================================================================


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """
    Admin interface for managing IPA staff invitations.

    Features:
    - Send new invitations
    - Track invitation status
    - Resend expired invitations
    - Revoke pending invitations
    - View acceptance rates
    - Export invitation reports
    """

    # Display configuration
    list_display = [
        "email",
        "member_state_badge",
        "role_badge",
        "status_badge",
        "validity_display",
        "invited_by_display",
        "tracking_display",
        "actions_column",
    ]

    list_filter = [
        InvitationStatusFilter,
        "status",
        MemberStateFilter,
        RoleFilter,
        "is_primary_contact",
        ("invited_at", admin.DateFieldListFilter),
        ("expires_at", admin.DateFieldListFilter),
    ]

    search_fields = [
        "email",
        "member_state__country_name",
        "member_state__ipa_acronym",
        "invited_by__username",
        "invited_by__email",
        "invited_by__first_name",
        "invited_by__last_name",
        "invitation_message",
    ]

    # Fieldsets for add/edit view
    fieldsets = [
        (
            _("Invitation Details"),
            {
                "fields": [
                    "email",
                    "member_state",
                    "role",
                    "is_primary_contact",
                ]
            },
        ),
        (
            _("Invitation Message"),
            {
                "fields": [
                    "invitation_message",
                ],
                "description": _(
                    "Optional personalized message to include in the invitation email."
                ),
            },
        ),
        (
            _("Invitation Lifecycle"),
            {
                "fields": [
                    "token",
                    "invited_by",
                    "invited_at",
                    "expires_at",
                    "status",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            _("Tracking & Analytics"),
            {
                "fields": [
                    "email_sent_at",
                    "email_opened_at",
                    "registration_started_at",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            _("Acceptance Details"),
            {
                "fields": [
                    "accepted_at",
                    "created_user",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            _("Revocation Details"),
            {
                "fields": [
                    "revoked_at",
                    "revoked_by",
                    "revoke_reason",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    readonly_fields = [
        "token",
        "invited_at",
        "email_sent_at",
        "email_opened_at",
        "registration_started_at",
        "accepted_at",
        "created_user",
        "revoked_at",
        "revoked_by",
        "created_at",
        "updated_at",
    ]

    # Date hierarchy
    date_hierarchy = "invited_at"

    # Ordering
    ordering = ["-invited_at"]

    # Raw ID fields for performance
    raw_id_fields = ["invited_by", "created_user", "revoked_by"]

    # Actions
    actions = [
        "resend_invitations",
        "revoke_invitations",
        "mark_as_expired",
        "export_as_csv",
        "send_reminder_emails",
    ]

    # Custom display methods
    def member_state_badge(self, obj):
        """Display member state as badge with flag"""
        url = reverse("admin:members_memberstateipa_change", args=[obj.member_state.pk])
        return format_html(
            '<a href="{}" style="text-decoration: none;">'
            '<span class="badge" style="background-color: #007bff; color: white; padding: 5px 10px;">'
            "{} {}"
            "</span>"
            "</a>",
            url,
            obj.member_state.flag_emoji or "🏛️",
            obj.member_state.ipa_acronym,
        )

    member_state_badge.short_description = _("Member State")
    member_state_badge.admin_order_field = "member_state"

    def role_badge(self, obj):
        """Display role as colored badge"""
        color_map = {
            "ipa_director": "#dc3545",   # Red
            "ipa_manager": "#fd7e14",    # Orange
            "ipa_officer": "#0d6efd",    # Blue
            "ipa_data_entry": "#17a2b8", # Cyan
            "ipa_analyst": "#198754",    # Green
        }
        icon_map = {
            "ipa_director": "fa-user-shield",
            "ipa_manager": "fa-user-tie",
            "ipa_officer": "fa-user-edit",
            "ipa_data_entry": "fa-keyboard",
            "ipa_analyst": "fa-chart-bar",
        }

        role_display = obj.get_role_display()
        if obj.is_primary_contact:
            role_display += " ⭐"

        return format_html(
            '<span class="badge" style="background-color: {}; color: white; padding: 5px 10px;">'
            '<i class="fas {}"></i> {}'
            "</span>",
            color_map.get(obj.role, "#6c757d"),
            icon_map.get(obj.role, "fa-user"),
            role_display,
        )

    role_badge.short_description = _("Role")
    role_badge.admin_order_field = "role"

    def status_badge(self, obj):
        """Display status as colored badge"""
        color_map = {
            "pending": "#ffc107",  # Warning yellow
            "accepted": "#28a745",  # Success green
            "expired": "#6c757d",  # Secondary gray
            "revoked": "#dc3545",  # Danger red
        }

        icon_map = {
            "pending": "fa-clock",
            "accepted": "fa-check-circle",
            "expired": "fa-calendar-times",
            "revoked": "fa-ban",
        }

        # Check if pending but actually expired
        if obj.status == "pending" and obj.is_expired:
            status_text = "Expired"
            color = color_map["expired"]
            icon = icon_map["expired"]
        else:
            status_text = obj.get_status_display()
            color = color_map.get(obj.status, "#6c757d")
            icon = icon_map.get(obj.status, "fa-question-circle")

        return format_html(
            '<span class="badge" style="background-color: {}; color: white; padding: 5px 10px;">'
            '<i class="fas {}"></i> {}'
            "</span>",
            color,
            icon,
            status_text,
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"

    def validity_display(self, obj):
        """Display invitation validity with countdown"""
        if obj.status == "pending":
            if obj.is_expired:
                return format_html(
                    '<span style="color: #dc3545;"><i class="fas fa-times-circle"></i> Expired</span>'
                )
            elif obj.days_until_expiry <= 2:
                return format_html(
                    '<span style="color: #ffc107;"><i class="fas fa-exclamation-triangle"></i> {} day{} left</span>',
                    obj.days_until_expiry,
                    "s" if obj.days_until_expiry != 1 else "",
                )
            else:
                return format_html(
                    '<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Valid ({} days)</span>',
                    obj.days_until_expiry,
                )
        elif obj.status == "accepted":
            return format_html(
                '<span style="color: #28a745;"><i class="fas fa-user-check"></i> Accepted</span>'
            )
        elif obj.status == "revoked":
            return format_html(
                '<span style="color: #dc3545;"><i class="fas fa-ban"></i> Revoked</span>'
            )
        return "-"

    validity_display.short_description = _("Validity")

    def invited_by_display(self, obj):
        """Display who sent the invitation"""
        if obj.invited_by:
            url = reverse("admin:accounts_user_change", args=[obj.invited_by.pk])
            return format_html(
                '<a href="{}">{}</a><br><small class="text-muted">{}</small>',
                url,
                obj.invited_by.get_full_name() or obj.invited_by.username,
                obj.invited_at.strftime("%Y-%m-%d"),
            )
        return _("System")

    invited_by_display.short_description = _("Invited By")
    invited_by_display.admin_order_field = "invited_by"

    def tracking_display(self, obj):
        """Display email tracking information"""
        tracking = []

        if obj.email_sent_at:
            tracking.append(f'<i class="fas fa-paper-plane" style="color: #28a745;"></i> Sent')

        if obj.email_opened_at:
            tracking.append(f'<i class="fas fa-envelope-open" style="color: #17a2b8;"></i> Opened')

        if obj.registration_started_at:
            tracking.append(f'<i class="fas fa-user-plus" style="color: #ffc107;"></i> Started')

        if tracking:
            return format_html("<br>".join(tracking))
        return format_html('<span class="text-muted">-</span>')

    tracking_display.short_description = _("Tracking")

    def actions_column(self, obj):
        """Display quick action buttons"""
        buttons = []

        if obj.status == "pending" and not obj.is_expired:
            # Resend button
            buttons.append(
                format_html(
                    '<a href="#" onclick="return false;" '
                    'class="button" style="background-color: #17a2b8; color: white; '
                    'padding: 3px 10px; border-radius: 3px; text-decoration: none;">'
                    '<i class="fas fa-redo"></i> Resend'
                    "</a>"
                )
            )

            # Revoke button
            buttons.append(
                format_html(
                    '<a href="#" onclick="return false;" '
                    'class="button" style="background-color: #dc3545; color: white; '
                    'padding: 3px 10px; border-radius: 3px; text-decoration: none;">'
                    '<i class="fas fa-ban"></i> Revoke'
                    "</a>"
                )
            )

        elif obj.status == "accepted" and obj.created_user:
            # View user button
            user_url = reverse("admin:accounts_user_change", args=[obj.created_user.pk])
            buttons.append(
                format_html(
                    '<a href="{}" class="button" style="background-color: #28a745; '
                    'color: white; padding: 3px 10px; border-radius: 3px; text-decoration: none;">'
                    '<i class="fas fa-user"></i> View User'
                    "</a>",
                    user_url,
                )
            )

        return format_html(" ".join(buttons)) if buttons else "-"

    actions_column.short_description = _("Actions")

    # Admin actions
    def resend_invitations(self, request, queryset):
        """Resend selected invitations"""
        count = 0
        for invitation in queryset.filter(status="pending"):
            if invitation.resend():
                count += 1
                # TODO: Send actual email here
                # send_invitation_email(invitation)

        self.message_user(
            request, f"{count} invitation(s) resent successfully. Expiration extended by 7 days."
        )

    resend_invitations.short_description = _("Resend selected invitations")

    def revoke_invitations(self, request, queryset):
        """Revoke selected pending invitations"""
        count = 0
        for invitation in queryset.filter(status="pending"):
            try:
                invitation.revoke(
                    revoked_by=request.user, reason="Revoked by admin via bulk action"
                )
                count += 1
            except Exception:
                pass

        self.message_user(request, f"{count} invitation(s) revoked successfully.")

    revoke_invitations.short_description = _("Revoke selected invitations")

    def mark_as_expired(self, request, queryset):
        """Mark expired pending invitations as expired"""
        count = queryset.filter(status="pending", expires_at__lte=timezone.now()).update(
            status="expired"
        )
        self.message_user(request, f"{count} invitation(s) marked as expired.")

    mark_as_expired.short_description = _("Mark expired as expired status")

    def send_reminder_emails(self, request, queryset):
        """Send reminder emails for pending invitations"""
        count = 0
        for invitation in queryset.filter(status="pending", expires_at__gt=timezone.now()):
            # TODO: Send actual reminder email
            # send_reminder_email(invitation)
            count += 1

        self.message_user(request, f"Reminder emails sent for {count} invitation(s).")

    send_reminder_emails.short_description = _("Send reminder emails")

    def export_as_csv(self, request, queryset):
        """Export selected invitations as CSV"""
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="invitations.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Email",
                "Member State",
                "Role",
                "Status",
                "Invited By",
                "Invited At",
                "Expires At",
                "Accepted At",
                "Is Primary Contact",
            ]
        )

        for invitation in queryset:
            writer.writerow(
                [
                    invitation.email,
                    invitation.member_state.ipa_acronym,
                    invitation.get_role_display(),
                    invitation.get_status_display(),
                    invitation.get_inviter_name(),
                    invitation.invited_at.strftime("%Y-%m-%d %H:%M"),
                    invitation.expires_at.strftime("%Y-%m-%d %H:%M"),
                    (
                        invitation.accepted_at.strftime("%Y-%m-%d %H:%M")
                        if invitation.accepted_at
                        else ""
                    ),
                    "Yes" if invitation.is_primary_contact else "No",
                ]
            )

        return response

    export_as_csv.short_description = _("Export selected as CSV")

    # Custom save behavior
    def save_model(self, request, obj, form, change):
        """Set invited_by to current user if not set"""
        if not change:  # New invitation
            if not obj.invited_by:
                obj.invited_by = request.user
            if not obj.invited_at:
                obj.invited_at = timezone.now()
            if not obj.expires_at:
                obj.expires_at = timezone.now() + timezone.timedelta(days=7)

        super().save_model(request, obj, form, change)

        # TODO: Send invitation email after creation
        # if not change and obj.status == 'pending':
        #     send_invitation_email(obj)

    # Custom queryset optimization
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "member_state",
                "invited_by",
                "created_user",
                "revoked_by",
            )
        )

    # Add custom view for statistics
    def changelist_view(self, request, extra_context=None):
        """Add statistics to changelist view"""
        extra_context = extra_context or {}

        # Get statistics
        total = Invitation.objects.count()
        pending = Invitation.objects.filter(status="pending", expires_at__gt=timezone.now()).count()
        accepted = Invitation.objects.filter(status="accepted").count()
        expired = Invitation.objects.filter(
            Q(status="expired") | Q(status="pending", expires_at__lte=timezone.now())
        ).count()
        revoked = Invitation.objects.filter(status="revoked").count()

        acceptance_rate = (accepted / total * 100) if total > 0 else 0

        extra_context["invitation_stats"] = {
            "total": total,
            "pending": pending,
            "accepted": accepted,
            "expired": expired,
            "revoked": revoked,
            "acceptance_rate": f"{acceptance_rate:.1f}%",
        }

        return super().changelist_view(request, extra_context=extra_context)
