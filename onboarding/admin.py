from django.contrib import admin
from django.utils.html import format_html

from onboarding.models import OnboardingRequest, OnboardingSession


@admin.register(OnboardingSession)
class OnboardingSessionAdmin(admin.ModelAdmin):
    list_display = ("label", "is_active", "is_open_display", "total_count", "pending_count", "created_at", "expires_at")
    list_filter = ("is_active",)
    readonly_fields = ("slug_token", "created_at", "created_by")
    search_fields = ("label", "notes")

    def is_open_display(self, obj):
        colour = "green" if obj.is_open else "red"
        label = "Open" if obj.is_open else "Closed"
        return format_html('<span style="color:{};">{}</span>', colour, label)
    is_open_display.short_description = "Open?"

    def total_count(self, obj):
        return obj.total_count
    total_count.short_description = "Total"

    def pending_count(self, obj):
        return obj.pending_count
    pending_count.short_description = "Pending"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OnboardingRequest)
class OnboardingRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "member_state", "requested_role", "status", "submitted_at", "ip_address")
    list_filter = ("status", "member_state", "requested_role")
    readonly_fields = ("submitted_at", "ip_address", "user_agent", "invitation")
    search_fields = ("full_name", "email", "job_title")
    ordering = ("-submitted_at",)
    raw_id_fields = ("reviewed_by",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("member_state", "session", "reviewed_by")
