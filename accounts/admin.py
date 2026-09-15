"""
Django Admin Configuration for Accounts Models.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import IPAUser

User = get_user_model()


# ============================================================================
# CUSTOM FILTERS
# ============================================================================


class RoleFilter(admin.SimpleListFilter):
    """Filter by IPA role"""

    title = _("role")
    parameter_name = "role"

    def lookups(self, request, model_admin):
        return [
            ("ipa_director", _("IPA Director")),
            ("ipa_manager", _("IPA Manager")),
            ("ipa_officer", _("IPA Officer")),
            ("ipa_data_entry", _("IPA Data Entry")),
            ("ipa_analyst", _("IPA Analyst")),
            ("primary_contacts", _("Primary Contacts Only")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "primary_contacts":
            return queryset.filter(is_primary_contact=True)
        elif self.value() in [
            "ipa_director",
            "ipa_manager",
            "ipa_officer",
            "ipa_data_entry",
            "ipa_analyst",
        ]:
            return queryset.filter(role=self.value())
        return queryset


class MemberStateFilter(admin.SimpleListFilter):
    """Filter by member state"""

    title = _("member state")
    parameter_name = "member_state"

    def lookups(self, request, model_admin):
        from members.models import MemberStateIPA

        states = (
            MemberStateIPA.objects.filter(ipa_users__isnull=False)
            .distinct()
            .order_by("ipa_acronym")
        )
        return [(state.id, f"{state.ipa_acronym} - {state.country_name}") for state in states]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(member_state_id=self.value())
        return queryset


class ActiveStatusFilter(admin.SimpleListFilter):
    """Filter by active status"""

    title = _("account status")
    parameter_name = "account_status"

    def lookups(self, request, model_admin):
        return [
            ("active", _("Active")),
            ("inactive", _("Inactive")),
            ("onboarding", _("Needs Onboarding")),
            ("recent_login", _("Logged in Recently")),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        week_ago = now - timezone.timedelta(days=7)

        if self.value() == "active":
            return queryset.filter(is_active=True)
        elif self.value() == "inactive":
            return queryset.filter(is_active=False)
        elif self.value() == "onboarding":
            return queryset.filter(onboarding_completed=False)
        elif self.value() == "recent_login":
            return queryset.filter(last_dashboard_login__gte=week_ago)
        return queryset


class PermissionFilter(admin.SimpleListFilter):
    """Filter by specific permissions"""

    title = _("special permissions")
    parameter_name = "special_permissions"

    def lookups(self, request, model_admin):
        return [
            ("can_publish", _("Can Publish Opportunities")),
            ("can_approve", _("Can Approve Data")),
            ("can_manage_users", _("Can Manage Users")),
            ("can_export", _("Can Export Data")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "can_publish":
            return queryset.filter(can_publish_opportunities=True)
        elif self.value() == "can_approve":
            return queryset.filter(can_approve_data=True)
        elif self.value() == "can_manage_users":
            return queryset.filter(can_manage_users=True)
        elif self.value() == "can_export":
            return queryset.filter(can_export_data=True)
        return queryset


# ============================================================================
# INLINE ADMIN
# ============================================================================


class IPAUserInline(admin.StackedInline):
    """Inline for IPAUser in User admin"""

    model = IPAUser
    can_delete = False
    verbose_name_plural = _("IPA Profile")
    fk_name = "user"

    fieldsets = [
        (
            _("IPA Information"),
            {
                "fields": [
                    "member_state",
                    "role",
                    "is_primary_contact",
                ]
            },
        ),
        (
            _("Permissions"),
            {
                "fields": [
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
                ],
                "classes": ["collapse"],
            },
        ),
        (
            _("Contact Information"),
            {
                "fields": [
                    "direct_phone",
                    "extension",
                    "office_location",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            _("Status"),
            {
                "fields": [
                    "is_active",
                    "dashboard_access_granted_at",
                    "last_dashboard_login",
                    "onboarding_completed",
                    "training_completed",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            _("Notification Preferences"),
            {
                "fields": [
                    "notify_on_inquiry",
                    "notify_on_opportunity_expiry",
                    "notify_on_team_changes",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    readonly_fields = [
        "dashboard_access_granted_at",
        "last_dashboard_login",
        "created_at",
        "updated_at",
    ]


# ============================================================================
# MAIN ADMIN
# ============================================================================


@admin.register(IPAUser)
class IPAUserAdmin(admin.ModelAdmin):
    """
    Admin interface for IPA Users.
    """

    list_display = [
        "user_display",
        "member_state_badge",
        "role_badge",
        "status_badge",
        "permissions_summary",
        "last_login_display",
        "actions_column",
    ]

    list_filter = [
        ActiveStatusFilter,
        RoleFilter,
        MemberStateFilter,
        PermissionFilter,
        "is_active",
        "is_primary_contact",
        "onboarding_completed",
        "training_completed",
        ("last_dashboard_login", admin.DateFieldListFilter),
        ("dashboard_access_granted_at", admin.DateFieldListFilter),
    ]

    search_fields = [
        # "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "member_state__country_name",
        "member_state__ipa_acronym",
        "direct_phone",
        "office_location",
    ]

    fieldsets = [
        (
            _("User Account"),
            {
                "fields": [
                    "user",
                    "member_state",
                    "role",
                    "is_primary_contact",
                ]
            },
        ),
        (
            _("Opportunity Permissions"),
            {
                "fields": [
                    "can_create_opportunities",
                    "can_publish_opportunities",
                ]
            },
        ),
        (
            _("Data Management Permissions"),
            {
                "fields": [
                    "can_approve_data",
                    "can_edit_profile",
                    "can_manage_sectors",
                    "can_edit_incentives",
                    "can_manage_success_stories",
                ]
            },
        ),
        (
            _("Inquiry & Analytics Permissions"),
            {
                "fields": [
                    "can_view_inquiries",
                    "can_respond_to_inquiries",
                    "can_view_analytics",
                    "can_export_data",
                ]
            },
        ),
        (
            _("User Management Permissions"),
            {
                "fields": [
                    "can_manage_users",
                ]
            },
        ),
        (
            _("Contact Information"),
            {
                "fields": [
                    "direct_phone",
                    "extension",
                    "office_location",
                ]
            },
        ),
        (
            _("Status & Access"),
            {
                "fields": [
                    "is_active",
                    "dashboard_access_granted_at",
                    "last_dashboard_login",
                    "dashboard_onboarding_completed",
                    "onboarding_completed",
                    "training_completed",
                ]
            },
        ),
        (
            _("Notification Preferences"),
            {
                "fields": [
                    "notify_on_inquiry",
                    "notify_on_opportunity_expiry",
                    "notify_on_team_changes",
                ]
            },
        ),
        (
            _("Metadata"),
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    readonly_fields = [
        "dashboard_access_granted_at",
        "last_dashboard_login",
        "created_at",
        "updated_at",
    ]

    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    raw_id_fields = ["user"]
    autocomplete_fields = ["user", "member_state"]

    actions = [
        "grant_dashboard_access",
        "revoke_dashboard_access",
        "mark_onboarding_complete",
        "reset_onboarding",
        "grant_full_permissions",
        "grant_editor_permissions",
        "grant_viewer_permissions",
        "export_as_csv",
    ]

    def user_display(self, obj):
        """Display user with profile link"""
        user_url = reverse("admin:accounts_user_change", args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a><br><small class="text-muted">{}</small>',
            user_url,
            obj.user.get_full_name(),
            obj.user.email,
        )

    user_display.short_description = _("User")
    user_display.admin_order_field = "user"

    def member_state_badge(self, obj):
        """Display member state as badge"""
        state_url = reverse("admin:members_memberstateipa_change", args=[obj.member_state.pk])
        return format_html(
            '<a href="{}" style="text-decoration: none;">'
            '<span class="badge" style="background-color: #007bff; color: white; padding: 5px 10px;">'
            "{} {}"
            "</span>"
            "</a>",
            state_url,
            obj.member_state.flag_emoji or "🏛️",
            obj.member_state.ipa_acronym,
        )

    member_state_badge.short_description = _("Member State")
    member_state_badge.admin_order_field = "member_state"

    def role_badge(self, obj):
        """Display role as colored badge"""
        color_map = {
            "hq_admin": "#6f42c1",
            "hq_analyst": "#e83e8c",
            "ipa_director": "#dc3545",
            "ipa_manager": "#fd7e14",
            "ipa_officer": "#0d6efd",
            "ipa_data_entry": "#17a2b8",
            "ipa_analyst": "#198754",
        }

        icon_map = {
            "hq_admin": "fa-crown",
            "hq_analyst": "fa-chart-line",
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
        """Display status badges"""
        badges = []

        if obj.is_active:
            badges.append(
                '<span class="badge" style="background-color: #28a745; color: white;">'
                '<i class="fas fa-check-circle"></i> Active'
                "</span>"
            )
        else:
            badges.append(
                '<span class="badge" style="background-color: #dc3545; color: white;">'
                '<i class="fas fa-times-circle"></i> Inactive'
                "</span>"
            )

        if not obj.onboarding_completed:
            badges.append(
                '<span class="badge" style="background-color: #ffc107; color: black;">'
                '<i class="fas fa-exclamation-triangle"></i> Needs Onboarding'
                "</span>"
            )

        return format_html("<br>".join(badges))

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "is_active"

    def permissions_summary(self, obj):
        """Display summary of key permissions"""
        perms = []

        if obj.can_publish_opportunities:
            perms.append(
                '<i class="fas fa-paper-plane" style="color: #28a745;" title="Can Publish"></i>'
            )
        if obj.can_approve_data:
            perms.append(
                '<i class="fas fa-check-circle" style="color: #17a2b8;" title="Can Approve"></i>'
            )
        if obj.can_manage_users:
            perms.append(
                '<i class="fas fa-users-cog" style="color: #dc3545;" title="Can Manage Users"></i>'
            )
        if obj.can_export_data:
            perms.append(
                '<i class="fas fa-download" style="color: #6c757d;" title="Can Export"></i>'
            )

        if perms:
            return format_html(" ".join(perms))
        return format_html('<span class="text-muted">-</span>')

    permissions_summary.short_description = _("Key Permissions")

    def last_login_display(self, obj):
        """Display last login with relative time"""
        if obj.last_dashboard_login:
            delta = timezone.now() - obj.last_dashboard_login
            if delta.days > 30:
                time_ago = f"{delta.days // 30} month(s) ago"
                color = "#dc3545"
            elif delta.days > 7:
                time_ago = f"{delta.days} day(s) ago"
                color = "#ffc107"
            elif delta.days > 0:
                time_ago = f"{delta.days} day(s) ago"
                color = "#28a745"
            else:
                time_ago = "Today"
                color = "#28a745"

            return format_html(
                '<span style="color: {};">{}</span><br>' '<small class="text-muted">{}</small>',
                color,
                time_ago,
                obj.last_dashboard_login.strftime("%Y-%m-%d %H:%M"),
            )
        return format_html('<span class="text-muted">Never</span>')

    last_login_display.short_description = _("Last Login")
    last_login_display.admin_order_field = "last_dashboard_login"

    def actions_column(self, obj):
        """Display quick action buttons"""
        buttons = []

        if not obj.is_active:
            buttons.append(
                format_html(
                    '<span class="button" style="background-color: #28a745; color: white; '
                    'padding: 3px 10px; border-radius: 3px;">'
                    '<i class="fas fa-check"></i> Activate'
                    "</span>"
                )
            )
        else:
            buttons.append(
                format_html(
                    '<span class="button" style="background-color: #dc3545; color: white; '
                    'padding: 3px 10px; border-radius: 3px;">'
                    '<i class="fas fa-ban"></i> Deactivate'
                    "</span>"
                )
            )

        if not obj.onboarding_completed:
            buttons.append(
                format_html(
                    '<span class="button" style="background-color: #17a2b8; color: white; '
                    'padding: 3px 10px; border-radius: 3px;">'
                    '<i class="fas fa-graduation-cap"></i> Complete Onboarding'
                    "</span>"
                )
            )

        return format_html(" ".join(buttons)) if buttons else "-"

    actions_column.short_description = _("Quick Actions")

    def grant_dashboard_access(self, request, queryset):
        """Grant dashboard access to selected users"""
        count = queryset.filter(dashboard_access_granted_at__isnull=True).update(
            dashboard_access_granted_at=timezone.now()
        )
        self.message_user(request, f"Dashboard access granted to {count} user(s).")

    grant_dashboard_access.short_description = _("Grant dashboard access")

    def revoke_dashboard_access(self, request, queryset):
        """Revoke dashboard access from selected users"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Dashboard access revoked from {count} user(s).")

    revoke_dashboard_access.short_description = _("Revoke dashboard access")

    def mark_onboarding_complete(self, request, queryset):
        """Mark onboarding as complete for selected users"""
        count = queryset.update(onboarding_completed=True, dashboard_onboarding_completed=True)
        self.message_user(request, f"Onboarding marked complete for {count} user(s).")

    mark_onboarding_complete.short_description = _("Mark onboarding complete")

    def reset_onboarding(self, request, queryset):
        """Reset onboarding for selected users"""
        count = queryset.update(onboarding_completed=False, dashboard_onboarding_completed=False)
        self.message_user(request, f"Onboarding reset for {count} user(s).")

    reset_onboarding.short_description = _("Reset onboarding")

    def grant_full_permissions(self, request, queryset):
        """Grant all permissions to selected users"""
        count = queryset.update(
            can_publish_opportunities=True,
            can_approve_data=True,
            can_manage_users=True,
            can_edit_profile=True,
            can_manage_sectors=True,
            can_create_opportunities=True,
            can_edit_incentives=True,
            can_manage_success_stories=True,
            can_view_inquiries=True,
            can_respond_to_inquiries=True,
            can_view_analytics=True,
            can_export_data=True,
        )
        self.message_user(request, f"Full permissions granted to {count} user(s).")

    grant_full_permissions.short_description = _("Grant full permissions")

    def grant_editor_permissions(self, request, queryset):
        """Grant editor permissions to selected users"""
        count = queryset.update(
            can_publish_opportunities=False,
            can_approve_data=False,
            can_manage_users=False,
            can_edit_profile=True,
            can_manage_sectors=False,
            can_create_opportunities=True,
            can_edit_incentives=True,
            can_manage_success_stories=True,
            can_view_inquiries=True,
            can_respond_to_inquiries=True,
            can_view_analytics=True,
            can_export_data=False,
        )
        self.message_user(request, f"Editor permissions granted to {count} user(s).")

    grant_editor_permissions.short_description = _("Grant editor permissions")

    def grant_viewer_permissions(self, request, queryset):
        """Grant viewer permissions to selected users"""
        count = queryset.update(
            can_publish_opportunities=False,
            can_approve_data=False,
            can_manage_users=False,
            can_edit_profile=False,
            can_manage_sectors=False,
            can_create_opportunities=False,
            can_edit_incentives=False,
            can_manage_success_stories=False,
            can_view_inquiries=True,
            can_respond_to_inquiries=False,
            can_view_analytics=True,
            can_export_data=False,
        )
        self.message_user(request, f"Viewer permissions granted to {count} user(s).")

    grant_viewer_permissions.short_description = _("Grant viewer permissions")

    def export_as_csv(self, request, queryset):
        """Export selected users as CSV"""
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="ipa_users.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                # "Username",
                "Email",
                "Full Name",
                "Member State",
                "Role",
                "Is Active",
                "Is Primary Contact",
                "Last Login",
                "Created At",
            ]
        )

        for ipa_user in queryset.select_related("user", "member_state"):
            writer.writerow(
                [
                    # ipa_user.user.username,
                    ipa_user.user.email,
                    ipa_user.user.get_full_name(),
                    ipa_user.member_state.ipa_acronym,
                    ipa_user.get_role_display(),
                    "Yes" if ipa_user.is_active else "No",
                    "Yes" if ipa_user.is_primary_contact else "No",
                    (
                        ipa_user.last_dashboard_login.strftime("%Y-%m-%d %H:%M")
                        if ipa_user.last_dashboard_login
                        else "Never"
                    ),
                    ipa_user.created_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        return response

    export_as_csv.short_description = _("Export selected as CSV")

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("user", "member_state")

    def changelist_view(self, request, extra_context=None):
        """Add statistics to changelist view"""
        extra_context = extra_context or {}

        total = IPAUser.objects.count()
        active = IPAUser.objects.filter(is_active=True).count()
        inactive = IPAUser.objects.filter(is_active=False).count()
        primary_contacts = IPAUser.objects.filter(is_primary_contact=True).count()
        needs_onboarding = IPAUser.objects.filter(onboarding_completed=False).count()

        extra_context["ipa_user_stats"] = {
            "total": total,
            "active": active,
            "inactive": inactive,
            "primary_contacts": primary_contacts,
            "needs_onboarding": needs_onboarding,
        }

        return super().changelist_view(request, extra_context=extra_context)


# ============================================================================
# EXTEND USER ADMIN
# ============================================================================


class CustomUserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "user_type", "is_active")
    search_fields = ("email", "first_name", "last_name")

    inlines = [IPAUserInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "job_title",
                    "organization",
                    "profile_picture",
                    "bio",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "user_type",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Security"),
            {
                "fields": (
                    "email_verified",
                    "two_factor_enabled",
                    "two_factor_secret",
                    "password_changed_at",
                    "failed_login_attempts",
                    "account_locked_until",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "user_type",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    def get_inline_instances(self, request, obj=None):
        if obj and hasattr(obj, "ipa_profile"):
            return super().get_inline_instances(request, obj)
        return []


# Unregister default User admin and register custom one
# admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
