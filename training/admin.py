from django.contrib import admin

from .models import PostTrainingFeedback, PreTrainingAssessment, TrainingInvitation, TrainingSession


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ["title", "training_date", "phase", "is_active", "total_invited", "pre_responses_count", "post_responses_count"]
    list_filter = ["phase", "is_active"]
    search_fields = ["title"]


@admin.register(TrainingInvitation)
class TrainingInvitationAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "country", "session", "status", "sent_at"]
    list_filter = ["status", "session"]
    search_fields = ["name", "email"]
    readonly_fields = ["token", "sent_at", "registered_at"]


@admin.register(PreTrainingAssessment)
class PreTrainingAssessmentAdmin(admin.ModelAdmin):
    list_display = ["invitation", "current_role", "knowledge_ipawas", "submitted_at"]
    readonly_fields = ["submitted_at"]


@admin.register(PostTrainingFeedback)
class PostTrainingFeedbackAdmin(admin.ModelAdmin):
    list_display = ["invitation", "overall_rating", "would_recommend", "submitted_at"]
    readonly_fields = ["submitted_at"]
