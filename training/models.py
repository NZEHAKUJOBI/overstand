"""
Training Session & Assessment Models

Supports:
- Training session management with pre/post phase toggle
- Token-based invitations (auto-email on creation)
- Pre-training knowledge assessment
- Post-training satisfaction feedback
"""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TrainingSession(models.Model):
    PHASE_PRE = "pre"
    PHASE_POST = "post"
    PHASE_CHOICES = [
        (PHASE_PRE, _("Pre-Training Assessment")),
        (PHASE_POST, _("Post-Training Feedback")),
    ]

    title = models.CharField(max_length=200, verbose_name=_("Session Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    training_date = models.DateField(verbose_name=_("Training Date"))
    location = models.CharField(max_length=200, blank=True, verbose_name=_("Location / Platform"))

    # Phase toggle — admin flips this from pre → post after the training day
    phase = models.CharField(
        max_length=4,
        choices=PHASE_CHOICES,
        default=PHASE_PRE,
        verbose_name=_("Current Phase"),
        help_text=_("Switch to Post-Training after the training is complete."),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Only active sessions accept new responses."),
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="training_sessions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-training_date"]
        verbose_name = _("Training Session")
        verbose_name_plural = _("Training Sessions")

    def __str__(self):
        return f"{self.title} ({self.training_date})"

    @property
    def is_pre_phase(self):
        return self.phase == self.PHASE_PRE

    @property
    def total_invited(self):
        return self.invitations.count()

    @property
    def total_registered(self):
        return self.invitations.exclude(registered_at=None).count()

    @property
    def pre_responses_count(self):
        return PreTrainingAssessment.objects.filter(invitation__session=self).count()

    @property
    def post_responses_count(self):
        return PostTrainingFeedback.objects.filter(invitation__session=self).count()


# ---------------------------------------------------------------------------
# 12 IPAWAS Member States for country dropdown
# Loaded dynamically from DB; this constant is the fallback used in migrations.
# ---------------------------------------------------------------------------
IPAWAS_MEMBER_STATES = [
    ("Benin", "Benin"),
    ("Burkina Faso", "Burkina Faso"),
    ("Cabo Verde", "Cabo Verde"),
    ("Côte d'Ivoire", "Côte d'Ivoire"),
    ("The Gambia", "The Gambia"),
    ("Ghana", "Ghana"),
    ("Guinea", "Guinea"),
    ("Guinea-Bissau", "Guinea-Bissau"),
    ("Liberia", "Liberia"),
    ("Mali", "Mali"),
    ("Niger", "Niger"),
    ("Nigeria", "Nigeria"),
    ("Senegal", "Senegal"),
    ("Sierra Leone", "Sierra Leone"),
    ("Togo", "Togo"),
]

ROLE_CHOICES = [
    ("", _("Select your role…")),
    ("director_general", _("Director General / CEO")),
    ("director", _("Director")),
    ("manager", _("Manager")),
    ("analyst", _("Analyst / Officer")),
    ("specialist", _("Specialist / Advisor")),
    ("coordinator", _("Coordinator")),
    ("other", _("Other")),
]

YEARS_CHOICES = [
    ("", _("Select…")),
    ("0-1", _("Less than 1 year")),
    ("1-3", _("1–3 years")),
    ("3-5", _("3–5 years")),
    ("5-10", _("5–10 years")),
    ("10+", _("More than 10 years")),
]

RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1-5


class TrainingInvitation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_REGISTERED = "registered"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending")),
        (STATUS_SENT, _("Sent")),
        (STATUS_REGISTERED, _("Registered")),
        (STATUS_COMPLETED, _("Completed")),
    ]

    session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name=_("Training Session"),
    )

    # Invitee info (pre-filled on the public form)
    name = models.CharField(max_length=200, verbose_name=_("Full Name"))
    email = models.EmailField(verbose_name=_("Email Address"))
    organization = models.CharField(max_length=200, blank=True, verbose_name=_("Organization"))
    country = models.CharField(max_length=100, verbose_name=_("Country"))
    job_title = models.CharField(max_length=200, blank=True, verbose_name=_("Job Title"))

    # Token-based unique link
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=_("Status"),
    )

    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Email Sent At"))
    registered_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Registered At"))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["session", "email"]]
        ordering = ["name"]
        verbose_name = _("Training Invitation")
        verbose_name_plural = _("Training Invitations")

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.session}"

    @property
    def has_pre_assessment(self):
        return hasattr(self, "pre_assessment")

    @property
    def has_post_feedback(self):
        return hasattr(self, "post_feedback")

    def mark_sent(self):
        self.sent_at = timezone.now()
        self.status = self.STATUS_SENT
        self.save(update_fields=["sent_at", "status"])

    def mark_registered(self):
        self.registered_at = timezone.now()
        self.status = self.STATUS_REGISTERED
        self.save(update_fields=["registered_at", "status"])

    def mark_completed(self):
        self.status = self.STATUS_COMPLETED
        self.save(update_fields=["status"])


class PreTrainingAssessment(models.Model):
    """One response per invitation. Submitted before the training day."""

    CHALLENGING_AREAS = [
        ("digital_tools", "Digital tools & platforms"),
        ("investor_targeting", "Investor targeting & outreach"),
        ("data_analysis", "Data collection & analysis"),
        ("policy_advocacy", "Policy advocacy"),
        ("deal_facilitation", "Deal facilitation & aftercare"),
        ("communication", "Communication & stakeholder engagement"),
        ("monitoring", "Monitoring & evaluation"),
        ("regional_cooperation", "Regional / ECOWAS cooperation"),
    ]

    invitation = models.OneToOneField(
        TrainingInvitation,
        on_delete=models.CASCADE,
        related_name="pre_assessment",
    )

    # Section A — Background
    current_role = models.CharField(max_length=50, choices=ROLE_CHOICES, verbose_name=_("Current Role"))
    years_in_role = models.CharField(max_length=10, choices=YEARS_CHOICES, verbose_name=_("Years in Role"))

    # Section B — Self-assessment (1-5)
    knowledge_ipawas = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Knowledge of IPAWAS Platform"),
        help_text=_("1 = None at all, 5 = Expert"),
    )
    knowledge_investment_promotion = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Investment Promotion Skills"),
        help_text=_("1 = Beginner, 5 = Expert"),
    )
    knowledge_data_tools = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Data & Digital Tools Proficiency"),
        help_text=_("1 = None at all, 5 = Expert"),
    )
    knowledge_regional_collab = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Regional Collaboration Experience"),
        help_text=_("1 = No experience, 5 = Extensive"),
    )

    # Section C — Expectations
    training_expectations = models.TextField(
        verbose_name=_("Training Expectations"),
        help_text=_("What do you hope to achieve from this training?"),
    )
    challenging_areas = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Challenging Areas"),
        help_text=_("Select all that apply"),
    )
    prior_ipawas_experience = models.TextField(
        blank=True,
        verbose_name=_("Prior IPAWAS Experience"),
        help_text=_("Describe any experience you have with the IPAWAS platform (leave blank if none)."),
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Pre-Training Assessment")
        verbose_name_plural = _("Pre-Training Assessments")

    def __str__(self):
        return f"Pre-Assessment: {self.invitation.name}"


class PostTrainingFeedback(models.Model):
    """One response per invitation. Submitted after the training day."""

    APPLICATION_CHOICES = [
        ("", _("Select…")),
        ("immediately", _("Immediately (within 1 week)")),
        ("soon", _("Within 1 month")),
        ("quarter", _("Within 3 months")),
        ("unsure", _("Unsure")),
    ]

    invitation = models.OneToOneField(
        TrainingInvitation,
        on_delete=models.CASCADE,
        related_name="post_feedback",
    )

    # Section A — Ratings (1-5)
    overall_rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Overall Training Rating"),
    )
    content_relevance = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Content Relevance to My Work"),
    )
    trainer_effectiveness = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Facilitator Effectiveness"),
    )
    platform_usability = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("IPAWAS Platform Usability"),
    )
    pace_and_structure = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Pace & Structure of the Training"),
    )

    # Section B — Open questions
    most_valuable = models.TextField(
        verbose_name=_("Most Valuable Element"),
        help_text=_("What was the most valuable part of this training for you?"),
    )
    needs_improvement = models.TextField(
        verbose_name=_("Areas for Improvement"),
        help_text=_("What could be improved in future sessions?"),
    )
    key_takeaway = models.TextField(
        verbose_name=_("Key Takeaway"),
        help_text=_("Describe one concrete action you will take as a result of this training."),
    )
    apply_learning_timeline = models.CharField(
        max_length=15,
        choices=APPLICATION_CHOICES,
        verbose_name=_("When Will You Apply What You Learned?"),
    )

    # Section C — Recommendation
    would_recommend = models.BooleanField(
        verbose_name=_("Would Recommend to a Colleague"),
    )
    additional_comments = models.TextField(
        blank=True,
        verbose_name=_("Additional Comments"),
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Post-Training Feedback")
        verbose_name_plural = _("Post-Training Feedback")

    def __str__(self):
        return f"Post-Feedback: {self.invitation.name}"
