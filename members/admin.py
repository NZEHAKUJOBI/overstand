"""
Django Admin Configuration for IPAWAS Members App

Provides comprehensive admin interface for managing member states,
sectors, incentives, inquiries, and related data.

App Name: members (not member_states)
"""

from django.contrib import admin
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.models import Sector
from members.models import (
    FDIDataPoint,
    InvestmentIncentive,
    InvestorInquiry,
    IPAStaff,
    MemberStateIPA,
    MemberStateSector,
    SuccessStory,
)

from .models import ECOWASLeadershipPosition, IPALeadership


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name"]


@admin.register(MemberStateIPA)
class MemberStateIPAAdmin(admin.ModelAdmin):
    """Admin interface for Member State IPAs."""

    list_display = [
        "country_flag_display",
        "country_name",
        "ipa_acronym",
        "population_display",
        "gdp_display",
        "official_language",
        "active_status_display",
        "featured",
        "display_order",
    ]

    list_filter = [
        "is_active",
        "featured",
        "official_language",
        "geographic_region",
    ]

    search_fields = [
        "country_name",
        "ipa_full_name",
        "ipa_acronym",
        "country_code",
        "capital_city",
    ]

    prepopulated_fields = {"slug": ("country_name",)}

    readonly_fields = [
        "created_at",
        "updated_at",
        "population_display",
        # "gdp_display",
        "view_on_site_link",
    ]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "country_name",
                    "slug",
                    "country_code",
                    "flag_emoji",
                    "is_active",
                    "featured",
                    "display_order",
                )
            },
        ),
        (
            "IPA Information",
            {
                "fields": (
                    "ipa_full_name",
                    "ipa_acronym",
                    "ipa_website",
                    "ipa_logo",
                    "overview",
                    "tagline",
                )
            },
        ),
        (
            "Economic Indicators",
            {
                "fields": (
                    ("population", "population_display"),
                    ("gdp", "gdp_display"),
                    "gdp_growth_rate",
                    "gdp_per_capita",
                )
            },
        ),
        (
            "Geographic Information",
            {
                "fields": (
                    "capital_city",
                    "major_cities",
                    "geographic_region",
                    "time_zone",
                )
            },
        ),
        (
            "Language & Currency",
            {
                "fields": (
                    "official_language",
                    ("currency_name", "currency_code", "currency_symbol"),
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "contact_email",
                    "contact_phone",
                    "physical_address",
                    "office_hours",
                )
            },
        ),
        (
            "Social Media",
            {
                "fields": (
                    "linkedin_url",
                    "twitter_url",
                    "facebook_url",
                    "instagram_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Images (AWS S3 URLs)",
            {
                "fields": (
                    "hero_image",
                    "card_image",
                )
            },
        ),
        (
            "Investment Climate",
            {
                "fields": (
                    "ease_of_doing_business_rank",
                    "competitiveness_score",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Resources (AWS S3 URLs)",
            {
                "fields": (
                    "investment_guide_pdf",
                    "doing_business_pdf",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "view_on_site_link",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def country_flag_display(self, obj):
        """Display country flag emoji"""
        return format_html('<span style="font-size: 24px;">{}</span>', obj.flag_emoji or "🏳️")

    country_flag_display.short_description = "Flag"

    def active_status_display(self, obj):
        """Display active status with color"""
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactive</span>')

    active_status_display.short_description = "Status"

    def view_on_site_link(self, obj):
        """Link to view member state on site"""
        if obj.pk:
            url = reverse("members:detail", kwargs={"country_slug": obj.slug})
            return format_html('<a href="{}" target="_blank">View on Site →</a>', url)
        return "-"

    view_on_site_link.short_description = "Public Page"

    actions = ["activate_members", "deactivate_members", "mark_as_featured", "unmark_as_featured"]

    def activate_members(self, request, queryset):
        """Activate selected member states"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} member state(s) activated.")

    activate_members.short_description = "Activate selected member states"

    def deactivate_members(self, request, queryset):
        """Deactivate selected member states"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} member state(s) deactivated.")

    deactivate_members.short_description = "Deactivate selected member states"

    def mark_as_featured(self, request, queryset):
        """Mark as featured"""
        count = queryset.update(featured=True)
        self.message_user(request, f"{count} member state(s) marked as featured.")

    mark_as_featured.short_description = "Mark as featured"

    def unmark_as_featured(self, request, queryset):
        """Unmark as featured"""
        count = queryset.update(featured=False)
        self.message_user(request, f"{count} member state(s) unmarked as featured.")

    unmark_as_featured.short_description = "Unmark as featured"


class MemberStateSectorInline(admin.TabularInline):
    """Inline for member state sectors"""

    model = MemberStateSector
    extra = 1
    fields = ["sector", "is_priority", "description", "display_order"]
    autocomplete_fields = ["sector"]


class InvestmentIncentiveInline(admin.TabularInline):
    """Inline for investment incentives"""

    model = InvestmentIncentive
    extra = 0
    fields = ["title", "incentive_type", "duration", "is_active"]
    show_change_link = True


@admin.register(MemberStateSector)
class MemberStateSectorAdmin(admin.ModelAdmin):
    """Admin for member state-sector relationships"""

    list_display = [
        "member_state",
        "sector",
        "is_priority_display",
        "display_order",
    ]

    list_filter = [
        "is_priority",
        "member_state__is_active",
        "sector",
    ]

    search_fields = [
        "member_state__country_name",
        "sector__name",
    ]

    autocomplete_fields = ["member_state", "sector"]

    list_editable = ["display_order"]

    def is_priority_display(self, obj):
        """Display priority status"""
        if obj.is_priority:
            return format_html('<span style="color: gold;">⭐ Priority</span>')
        return "-"

    is_priority_display.short_description = "Priority"


@admin.register(InvestmentIncentive)
class InvestmentIncentiveAdmin(admin.ModelAdmin):
    """Admin for investment incentives"""

    list_display = [
        "title",
        "member_state",
        "incentive_type",
        "duration",
        "is_active",
        "display_order",
    ]

    list_filter = [
        "is_active",
        "incentive_type",
        "member_state",
    ]

    search_fields = [
        "title",
        "description",
        "member_state__country_name",
    ]

    autocomplete_fields = ["member_state"]
    filter_horizontal = ["applicable_sectors"]

    list_editable = ["display_order", "is_active"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "member_state",
                    "title",
                    "incentive_type",
                    "is_active",
                    "display_order",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "description",
                    "duration",
                    "benefit_amount",
                    "eligibility_criteria",
                    "applicable_sectors",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at"]


@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    """Admin for success stories"""

    list_display = [
        "title",
        "company_name",
        "member_state",
        "sector",
        "year",
        "investment_display",
        "jobs_created",
        "published",
        "featured",
    ]

    list_filter = [
        "published",
        "featured",
        "year",
        "member_state",
        "sector",
    ]

    search_fields = [
        "title",
        "company_name",
        "company_origin",
        "summary",
    ]

    autocomplete_fields = ["member_state", "sector"]

    list_editable = ["published", "featured"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "member_state",
                    "title",
                    "company_name",
                    "company_origin",
                    "sector",
                    "year",
                )
            },
        ),
        (
            "Investment Details",
            {
                "fields": (
                    ("investment_amount", "investment_amount_display"),
                    "jobs_created",
                )
            },
        ),
        (
            "Story Content",
            {
                "fields": (
                    "summary",
                    "full_story",
                    "impact",
                    "image",
                )
            },
        ),
        (
            "Publishing",
            {
                "fields": (
                    "published",
                    "featured",
                    "display_order",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at"]

    def investment_display(self, obj):
        """Display formatted investment amount"""
        return obj.investment_amount_display or "-"

    investment_display.short_description = "Investment"


@admin.register(InvestorInquiry)
class InvestorInquiryAdmin(admin.ModelAdmin):
    """Admin for investor inquiries"""

    list_display = [
        "reference_number",
        "member_state",
        "full_name",
        "company_name",
        "inquiry_type",
        "status_display",
        "assigned_to",
        "created_at",
    ]

    list_filter = [
        "status",
        "inquiry_type",
        "member_state",
        "created_at",
        "assigned_to",
    ]

    search_fields = [
        "reference_number",
        "full_name",
        "email",
        "company_name",
        "subject",
    ]

    readonly_fields = [
        "reference_number",
        "created_at",
        "updated_at",
        "ip_address",
        "user_agent",
    ]

    fieldsets = (
        (
            "Inquiry Details",
            {
                "fields": (
                    "reference_number",
                    "member_state",
                    "inquiry_type",
                    "status",
                    "assigned_to",
                )
            },
        ),
        (
            "Investor Information",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone",
                    "company_name",
                    "company_country",
                )
            },
        ),
        (
            "Investment Details",
            {
                "fields": (
                    "sector_of_interest",
                    "estimated_investment",
                )
            },
        ),
        (
            "Message",
            {
                "fields": (
                    "subject",
                    "message",
                )
            },
        ),
        ("Internal Processing", {"fields": ("internal_notes",)}),
        (
            "Metadata",
            {
                "fields": (
                    "ip_address",
                    "user_agent",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def status_display(self, obj):
        """Display status with color"""
        colors = {
            "new": "blue",
            "in_progress": "orange",
            "responded": "green",
            "closed": "gray",
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, "black"),
            obj.get_status_display(),
        )

    status_display.short_description = "Status"

    actions = ["mark_as_in_progress", "mark_as_responded", "mark_as_closed"]

    def mark_as_in_progress(self, request, queryset):
        """Mark inquiries as in progress"""
        count = queryset.update(status="in_progress")
        self.message_user(request, f"{count} inquir(y/ies) marked as in progress.")

    mark_as_in_progress.short_description = "Mark as In Progress"

    def mark_as_responded(self, request, queryset):
        """Mark inquiries as responded"""
        count = queryset.update(status="responded")
        self.message_user(request, f"{count} inquir(y/ies) marked as responded.")

    mark_as_responded.short_description = "Mark as Responded"

    def mark_as_closed(self, request, queryset):
        """Mark inquiries as closed"""
        count = queryset.update(status="closed")
        self.message_user(request, f"{count} inquir(y/ies) marked as closed.")

    mark_as_closed.short_description = "Mark as Closed"


@admin.register(FDIDataPoint)
class FDIDataPointAdmin(admin.ModelAdmin):
    """Admin for FDI data points"""

    list_display = [
        "member_state",
        "data_type",
        "year",
        "value_formatted",
        "data_source",
        "validation_status",
    ]

    list_filter = [
        "validation_status",
        "data_type",
        "member_state",
        "year",
    ]

    search_fields = [
        "member_state__country_name",
        "data_source",
        "notes",
    ]

    list_editable = ["validation_status"]

    fieldsets = (
        (
            "Data Point",
            {
                "fields": (
                    "member_state",
                    "data_type",
                    "year",
                    ("value", "value_display"),
                )
            },
        ),
        (
            "Source & Validation",
            {
                "fields": (
                    "data_source",
                    "validation_status",
                    "notes",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at"]

    def value_formatted(self, obj):
        """Display formatted value"""
        return obj.value_display or f"${obj.value:,.2f}M"

    value_formatted.short_description = "Value"

    actions = ["publish_data", "unpublish_data"]

    def publish_data(self, request, queryset):
        """Publish selected data points"""
        count = queryset.update(validation_status="published")
        self.message_user(request, f"{count} data point(s) published.")

    publish_data.short_description = "Publish selected data"

    def unpublish_data(self, request, queryset):
        """Unpublish selected data points"""
        count = queryset.update(validation_status="draft")
        self.message_user(request, f"{count} data point(s) unpublished.")

    unpublish_data.short_description = "Unpublish selected data"


@admin.register(IPAStaff)
class IPAStaffAdmin(admin.ModelAdmin):
    """Admin for IPA staff members"""

    list_display = [
        "full_name",
        "position_title",
        "member_state",
        "position_type",
        "is_active",
        "show_on_website",
        "display_order",
    ]

    list_filter = [
        "is_active",
        "show_on_website",
        "position_type",
        "member_state",
    ]

    search_fields = [
        "full_name",
        "position_title",
        "member_state__country_name",
        "bio",
    ]

    list_editable = ["display_order", "is_active", "show_on_website"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "member_state",
                    "full_name",
                    "position_title",
                    "position_type",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "email",
                    "phone",
                    "linkedin_url",
                )
            },
        ),
        (
            "Profile",
            {
                "fields": (
                    "bio",
                    "photo",
                )
            },
        ),
        (
            "Display Settings",
            {
                "fields": (
                    "display_order",
                    "is_active",
                    "show_on_website",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at"]


@admin.register(IPALeadership)
class IPALeadershipAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "official_title",
        "member_state",
        "appointment_date",
        "is_verified",
        "last_verified",
    )
    list_filter = ("official_title", "member_state", "last_verified")
    search_fields = (
        "full_name",
        "member_state__country_name",
        "member_state__ipa_acronym",
    )
    readonly_fields = ("created_at", "updated_at", "is_verified")
    ordering = ("member_state__country_name",)

    fieldsets = (
        (
            "Member State",
            {
                "fields": ("member_state",),
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "full_name",
                    "official_title",
                    "official_photograph",
                    "direct_email",
                ),
            },
        ),
        (
            "Biography",
            {
                "fields": ("biography",),
            },
        ),
        (
            "Appointment & Verification",
            {
                "fields": ("appointment_date", "last_verified", "is_verified"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


@admin.register(ECOWASLeadershipPosition)
class ECOWASLeadershipPositionAdmin(admin.ModelAdmin):
    list_display = (
        "position_type",
        "current_holder_name",
        "country_of_origin",
        "start_date",
        "end_date",
        "is_active",
    )
    list_filter = ("position_type", "is_active", "country_of_origin")
    search_fields = (
        "current_holder_name",
        "position_title",
        "country_of_origin",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("position_type",)

    fieldsets = (
        (
            "Position Details",
            {
                "fields": (
                    "position_type",
                    "position_title",
                    "position_description",
                ),
            },
        ),
        (
            "Current Holder",
            {
                "fields": (
                    "current_holder_title_prefix",
                    "current_holder_name",
                    "country_of_origin",
                    "official_portrait",
                ),
            },
        ),
        (
            "Biography & Background",
            {
                "fields": (
                    "biography",
                    "education",
                    "career_highlights",
                    "vision_statement",
                ),
            },
        ),
        (
            "Tenure & Status",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "is_active",
                ),
            },
        ),
        (
            "Contact Information",
            {
                "fields": ("office_email", "office_phone"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


# Customize admin site headers
admin.site.site_header = "IPAWAS Members Administration"
admin.site.site_title = "IPAWAS Members Admin"
admin.site.index_title = "Member States Management"
