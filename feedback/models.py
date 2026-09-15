from django.conf import settings
from django.db import models


class Feedback(models.Model):
    CATEGORY_CHOICES = [
        ("idea", "Idea"),
        ("suggestion", "Suggestion"),
        ("observation", "Observation"),
        ("bug_report", "Bug Report"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("under_review", "Under Review"),
        ("acknowledged", "Acknowledged"),
        ("implemented", "Implemented"),
        ("declined", "Declined"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedback_submissions",
    )
    member_state = models.ForeignKey(
        "members.MemberStateIPA",
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    admin_response = models.TextField(blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feedback_responses",
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"

    def __str__(self):
        return f"{self.get_category_display()} — {self.title}"

    @property
    def category_icon(self):
        return {
            "idea": "fa-lightbulb",
            "suggestion": "fa-comment-dots",
            "observation": "fa-eye",
            "bug_report": "fa-bug",
        }.get(self.category, "fa-comment")

    @property
    def status_color(self):
        return {
            "new": "#3B82F6",
            "under_review": "#F59E0B",
            "acknowledged": "#8B5CF6",
            "implemented": "#10B981",
            "declined": "#EF4444",
        }.get(self.status, "#6B7280")
