"""
IPAWAS Opportunities App Admin Configuration
============================================

Admin interface for managing investment opportunities, documents, inquiries, and updates.
"""

from django.contrib import admin
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    InvestmentOpportunity,
    OpportunityDocument,
    OpportunityInquiry,
    OpportunityUpdate,
)

# ============================================================================
# INLINE ADMINS
# ============================================================================


class OpportunityDocumentInline(admin.TabularInline):
    """Inline for managing opportunity documents"""

    model = OpportunityDocument
    extra = 1
    fields = [
        "title",
        "document_type",
        "file",
        "file_size",
        "is_public",
        "requires_nda",
        "download_count",
        "display_order",
    ]
    readonly_fields = ["download_count"]
    ordering = ["display_order", "title"]


class OpportunityUpdateInline(admin.StackedInline):
    """Inline for managing opportunity updates"""

    model = OpportunityUpdate
    extra = 0
    fields = ["update_type", "title", "description", "is_public", "created_by"]
    readonly_fields = ["created_by"]
    ordering = ["-created_at"]

    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================================
# INVESTMENT OPPORTUNITY ADMIN
# ============================================================================


@admin.register(InvestmentOpportunity)
class InvestmentOpportunityAdmin(admin.ModelAdmin):
    """Admin for Investment Opportunities"""

    list_display = [
        "reference_number_display",
        "title_display",
        "primary_country",
        "primary_sector",
        "status_badge",
        "investment_range",
        "expected_roi",
        "priority_level",
        # "published_badge",
        "featured_badge",
        "stats_display",
        "created_at",
    ]

    list_filter = [
        "status",
        "published",
        "featured",
        "priority_level",
        "opportunity_type",
        "project_stage",
        "primary_country",
        "primary_sector",
        "is_regional",
        "created_at",
    ]

    search_fields = [
        "title",
        "reference_number",
        "summary",
        "description",
        "implementing_agency",
        "specific_location",
    ]

    readonly_fields = [
        "reference_number",
        "slug",
        "views_count",
        "inquiries_count",
        "downloads_count",
        "created_at",
        "updated_at",
        "created_by",
        "approved_by",
        "approved_date",
        "published_date",
    ]

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "title",
                    "slug",
                    "reference_number",
                    "summary",
                    "description",
                    "status",
                    "priority_level",
                    "published",
                    "featured",
                ]
            },
        ),
        (
            "Classification",
            {
                "fields": [
                    "opportunity_type",
                    "primary_sector",
                    "secondary_sectors",
                    "sub_sector",
                    "project_stage",
                ]
            },
        ),
        (
            "Location",
            {
                "fields": [
                    "primary_country",
                    "is_regional",
                    "participating_countries",
                    "specific_location",
                    "geographic_coordinates",
                ]
            },
        ),
        (
            "Investment Details",
            {
                "fields": [
                    "investment_required_min",
                    "investment_required_max",
                    "investment_breakdown",
                    "expected_roi",
                    "payback_period",
                    "implementation_timeline",
                    "start_date_target",
                ]
            },
        ),
        (
            "Implementing Entity",
            {
                "fields": [
                    "implementing_agency",
                    "implementing_agency_contact",
                ]
            },
        ),
        (
            "Investor Requirements",
            {
                "fields": [
                    "investor_profile",
                    "technical_requirements",
                    "minimum_equity",
                    "local_content_requirements",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Market & Financial",
            {
                "fields": [
                    "market_analysis",
                    "target_market",
                    "revenue_projections",
                    "financial_incentives_available",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Regulatory & Legal",
            {
                "fields": [
                    "regulatory_framework",
                    "approval_process",
                    "licenses_required",
                    "land_availability",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Risk Assessment",
            {
                "fields": [
                    "risk_factors",
                    "mitigation_measures",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Media",
            {
                "fields": [
                    "thumbnail_image",
                    "hero_image",
                    "gallery_images",
                    "video_url",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Analytics & Metadata",
            {
                "fields": [
                    "views_count",
                    "inquiries_count",
                    "downloads_count",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "published_date",
                    "approved_by",
                    "approved_date",
                ]
            },
        ),
    ]

    filter_horizontal = ["secondary_sectors", "participating_countries"]
    inlines = [OpportunityDocumentInline, OpportunityUpdateInline]
    date_hierarchy = "created_at"
    save_on_top = True

    actions = [
        "publish_opportunities",
        "unpublish_opportunities",
        "mark_as_featured",
        "unmark_as_featured",
        "change_to_active",
        "change_to_draft",
    ]

    def get_queryset(self, request):
        """Optimize queries with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            "primary_country", "primary_sector", "created_by", "approved_by"
        ).prefetch_related("secondary_sectors", "participating_countries")

    def save_model(self, request, obj, form, change):
        """Auto-set created_by and approved_by"""
        if not obj.pk:
            obj.created_by = request.user

        # If being published, set approved_by
        if obj.published and not obj.approved_by:
            obj.approved_by = request.user
            obj.approved_date = timezone.now()

        super().save_model(request, obj, form, change)

    # Custom Display Methods
    def reference_number_display(self, obj):
        """Display reference number with link"""
        return format_html("<strong>{}</strong>", obj.reference_number)

    reference_number_display.short_description = "Reference #"
    reference_number_display.admin_order_field = "reference_number"

    def title_display(self, obj):
        """Display title with truncation"""
        max_length = 50
        if len(obj.title) > max_length:
            return format_html("{}&hellip;", obj.title[:max_length])
        return obj.title

    title_display.short_description = "Title"
    title_display.admin_order_field = "title"

    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            "draft": "gray",
            "under_review": "orange",
            "active": "green",
            "negotiation": "blue",
            "funded": "purple",
            "suspended": "red",
            "cancelled": "black",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    # def published_badge(self, obj):
    #     """Display published status"""
    #     if obj.published:
    #         return format_html('<span style="color: green; font-weight: bold;">Published</span>')
    #     return format_html('<span style="color: gray;">Draft</span>')

    # published_badge.short_description = "Published"
    # published_badge.admin_order_field = "published"
    # published_badge.boolean = True

    def featured_badge(self, obj):
        """Display featured status"""
        if obj.featured:
            return format_html('<span style="color: gold; font-size: 16px;">★</span>')
        return ""

    featured_badge.short_description = "Featured"
    featured_badge.admin_order_field = "featured"

    def investment_range(self, obj):
        """Display investment range"""
        return obj.get_investment_range_display()

    investment_range.short_description = "Investment (USD)"

    def stats_display(self, obj):
        """Display analytics stats"""
        return format_html(
            "<small>👁 {} | 💬 {} | ⬇ {}</small>",
            obj.views_count,
            obj.inquiries_count,
            obj.downloads_count,
        )

    stats_display.short_description = "Stats (V/I/D)"

    # Actions
    def publish_opportunities(self, request, queryset):
        """Publish selected opportunities"""
        from django.utils import timezone

        updated = queryset.update(
            published=True, published_date=timezone.now(), approved_by=request.user
        )
        self.message_user(request, f"{updated} opportunities published successfully.")

    publish_opportunities.short_description = "Publish selected opportunities"

    def unpublish_opportunities(self, request, queryset):
        """Unpublish selected opportunities"""
        updated = queryset.update(published=False)
        self.message_user(request, f"{updated} opportunities unpublished.")

    unpublish_opportunities.short_description = "○ Unpublish selected opportunities"

    def mark_as_featured(self, request, queryset):
        """Mark as featured"""
        updated = queryset.update(featured=True)
        self.message_user(request, f"{updated} opportunities marked as featured.")

    mark_as_featured.short_description = "★ Mark as featured"

    def unmark_as_featured(self, request, queryset):
        """Remove featured status"""
        updated = queryset.update(featured=False)
        self.message_user(request, f"{updated} opportunities unmarked as featured.")

    unmark_as_featured.short_description = "☆ Remove featured status"

    def change_to_active(self, request, queryset):
        """Change status to active"""
        updated = queryset.update(status="active")
        self.message_user(request, f"{updated} opportunities set to active.")

    change_to_active.short_description = "→ Change to Active"

    def change_to_draft(self, request, queryset):
        """Change status to draft"""
        updated = queryset.update(status="draft", published=False)
        self.message_user(request, f"{updated} opportunities set to draft.")

    change_to_draft.short_description = "→ Change to Draft"


# ============================================================================
# OPPORTUNITY DOCUMENT ADMIN
# ============================================================================


@admin.register(OpportunityDocument)
class OpportunityDocumentAdmin(admin.ModelAdmin):
    """Admin for Opportunity Documents"""

    list_display = [
        "title",
        "opportunity_link",
        "document_type",
        "file_link",
        "file_size",
        "is_public",
        "requires_nda",
        "download_count",
        "display_order",
        "created_at",
    ]

    list_filter = ["document_type", "is_public", "requires_nda", "created_at"]

    search_fields = ["title", "description", "opportunity__title", "opportunity__reference_number"]

    readonly_fields = ["download_count", "created_at", "updated_at", "uploaded_by"]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "opportunity",
                    "title",
                    "document_type",
                    "description",
                ]
            },
        ),
        (
            "File Information",
            {
                "fields": [
                    "file",
                    "file_size",
                ]
            },
        ),
        (
            "Access Control",
            {
                "fields": [
                    "is_public",
                    "requires_nda",
                    "display_order",
                ]
            },
        ),
        (
            "Metadata",
            {
                "fields": [
                    "download_count",
                    "uploaded_by",
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    def opportunity_link(self, obj):
        """Link to opportunity"""
        url = reverse("admin:opportunities_investmentopportunity_change", args=[obj.opportunity.pk])
        return format_html('<a href="{}">{}</a>', url, obj.opportunity.reference_number)

    opportunity_link.short_description = "Opportunity"

    def file_link(self, obj):
        """Display file link"""
        if obj.file:
            return format_html('<a href="{}" target="_blank">📄 View</a>', obj.file)
        return "-"

    file_link.short_description = "File"

    def save_model(self, request, obj, form, change):
        """Auto-set uploaded_by"""
        if not obj.pk:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================================
# OPPORTUNITY INQUIRY ADMIN
# ============================================================================


@admin.register(OpportunityInquiry)
class OpportunityInquiryAdmin(admin.ModelAdmin):
    """Admin for Opportunity Inquiries"""

    list_display = [
        "reference_number",
        "opportunity_link",
        "full_name",
        "company_name",
        "company_country",
        "status_badge",
        "investment_capacity",
        "requires_site_visit",
        "assigned_to",
        "created_at",
    ]

    list_filter = [
        "status",
        "partnership_interest",
        "requires_site_visit",
        "requires_nda",
        "created_at",
        "assigned_to",
    ]

    search_fields = [
        "reference_number",
        "full_name",
        "email",
        "company_name",
        "company_country",
        "message",
        "opportunity__title",
        "opportunity__reference_number",
    ]

    readonly_fields = [
        "reference_number",
        "ip_address",
        "user_agent",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            "Inquiry Information",
            {
                "fields": [
                    "opportunity",
                    "reference_number",
                    "status",
                    "assigned_to",
                ]
            },
        ),
        (
            "Investor Information",
            {
                "fields": [
                    "full_name",
                    "email",
                    "phone",
                    "company_name",
                    "company_country",
                    "company_website",
                ]
            },
        ),
        (
            "Investment Profile",
            {
                "fields": [
                    "investment_capacity",
                    "investment_timeline",
                    "partnership_interest",
                ]
            },
        ),
        (
            "Inquiry Details",
            {
                "fields": [
                    "message",
                    "specific_questions",
                    "experience_in_sector",
                    "previous_investments",
                    "requires_site_visit",
                    "requires_nda",
                ]
            },
        ),
        (
            "Processing",
            {
                "fields": [
                    "internal_notes",
                    "follow_up_date",
                    "investor_contacted_date",
                    "last_contact_date",
                ]
            },
        ),
        (
            "Metadata",
            {
                "fields": [
                    "ip_address",
                    "user_agent",
                    "created_at",
                    "updated_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    date_hierarchy = "created_at"
    save_on_top = True

    actions = [
        "mark_as_reviewed",
        "mark_as_contacted",
        "mark_as_qualified",
        "assign_to_me",
    ]

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related("opportunity", "assigned_to")

    def opportunity_link(self, obj):
        """Link to opportunity"""
        url = reverse("admin:opportunities_investmentopportunity_change", args=[obj.opportunity.pk])
        return format_html('<a href="{}">{}</a>', url, obj.opportunity.title[:40])

    opportunity_link.short_description = "Opportunity"

    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            "new": "blue",
            "reviewed": "orange",
            "contacted": "purple",
            "qualified": "green",
            "disqualified": "red",
            "closed": "gray",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    # Actions
    def mark_as_reviewed(self, request, queryset):
        """Mark inquiries as reviewed"""
        updated = queryset.update(status="reviewed")
        self.message_user(request, f"{updated} inquiries marked as reviewed.")

    mark_as_reviewed.short_description = "Mark as Reviewed"

    def mark_as_contacted(self, request, queryset):
        """Mark inquiries as contacted"""
        from django.utils import timezone

        updated = queryset.update(status="contacted", investor_contacted_date=timezone.now())
        self.message_user(request, f"{updated} inquiries marked as contacted.")

    mark_as_contacted.short_description = "Mark as Contacted"

    def mark_as_qualified(self, request, queryset):
        """Mark inquiries as qualified"""
        updated = queryset.update(status="qualified")
        self.message_user(request, f"{updated} inquiries marked as qualified.")

    mark_as_qualified.short_description = "Mark as Qualified"

    def assign_to_me(self, request, queryset):
        """Assign inquiries to current user"""
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f"{updated} inquiries assigned to you.")

    assign_to_me.short_description = "Assign to Me"


# ============================================================================
# OPPORTUNITY UPDATE ADMIN
# ============================================================================


@admin.register(OpportunityUpdate)
class OpportunityUpdateAdmin(admin.ModelAdmin):
    """Admin for Opportunity Updates"""

    list_display = [
        "title",
        "opportunity_link",
        "update_type",
        "is_public",
        "created_by",
        "created_at",
    ]

    list_filter = ["update_type", "is_public", "created_at"]

    search_fields = ["title", "description", "opportunity__title", "opportunity__reference_number"]

    readonly_fields = ["created_by", "created_at", "updated_at"]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "opportunity",
                    "update_type",
                    "title",
                    "description",
                    "is_public",
                ]
            },
        ),
        (
            "Metadata",
            {
                "fields": [
                    "created_by",
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    date_hierarchy = "created_at"

    def opportunity_link(self, obj):
        """Link to opportunity"""
        url = reverse("admin:opportunities_investmentopportunity_change", args=[obj.opportunity.pk])
        return format_html('<a href="{}">{}</a>', url, obj.opportunity.reference_number)

    opportunity_link.short_description = "Opportunity"

    def save_model(self, request, obj, form, change):
        """Auto-set created_by"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
