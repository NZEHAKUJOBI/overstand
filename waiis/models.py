"""
IPAWAS WAIIS App Models
=======================

West Africa Investment Intelligence System (WAIIS)

This module contains models for FDI data management and analytics:
- WaiisDataSubmission: Core FDI data submissions from IPAs
- WaiisQuarterlyData: Quarterly FDI breakdown
- WaiisSourceCountryData: FDI by source country
- WaiisSectorData: FDI by sector
- WaiisDataApproval: Workflow for data review and approval
- WaiisDataAudit: Audit trail for data changes
- WaiisAnalyticsCache: Cached analytics for performance

These models power the regional investment intelligence platform.
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import JSONField
from django.utils import timezone

# Import from other apps
from accounts.models import User
from core.models import Sector
from members.models import MemberStateIPA


class WaiisDataSubmission(models.Model):
    """
    Core FDI data submission from IPAs.

    IPAs submit annual and quarterly FDI data which is reviewed
    by IPAWAS admin before publication.
    """

    VALIDATION_STATUS = [
        ("draft", "Draft"),
        ("submitted", "Submitted for Review"),
        ("under_review", "Under Review"),
        ("revision_requested", "Revision Requested"),
        ("approved", "Approved"),
        ("published", "Published"),
        ("rejected", "Rejected"),
    ]

    DATA_TYPES = [
        ("annual", "Annual Data"),
        ("quarterly", "Quarterly Data"),
    ]

    # Identification
    submission_id = models.CharField(
        max_length=50, unique=True, help_text="Unique submission ID (auto-generated)"
    )

    # Member State
    member_state = models.ForeignKey(
        MemberStateIPA,
        on_delete=models.CASCADE,
        related_name="waiis_submissions",
        help_text="Country submitting data",
    )

    # Time Period
    data_type = models.CharField(
        max_length=20, choices=DATA_TYPES, default="annual", help_text="Annual or quarterly data"
    )

    year = models.IntegerField(
        help_text="Data year", validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    quarter = models.IntegerField(
        null=True,
        blank=True,
        help_text="Quarter (1-4) if quarterly data",
        validators=[MinValueValidator(1), MaxValueValidator(4)],
    )

    # FDI Data (in USD millions)
    fdi_inflow = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="FDI Inflow (USD millions)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    fdi_outflow = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="FDI Outflow (USD millions)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    fdi_stock = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total FDI Stock (USD millions)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    # Project Data
    number_of_projects = models.IntegerField(
        null=True, blank=True, help_text="Number of FDI projects", validators=[MinValueValidator(0)]
    )

    greenfield_projects = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of greenfield projects",
        validators=[MinValueValidator(0)],
    )

    expansion_projects = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of expansion projects",
        validators=[MinValueValidator(0)],
    )

    # Economic Impact
    jobs_created = models.IntegerField(
        null=True, blank=True, help_text="Jobs created by FDI", validators=[MinValueValidator(0)]
    )

    jobs_sustained = models.IntegerField(
        null=True, blank=True, help_text="Jobs sustained by FDI", validators=[MinValueValidator(0)]
    )

    # Additional Metrics
    gdp_contribution = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated GDP contribution (USD millions)",
    )

    tax_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tax revenue from FDI (USD millions)",
    )

    # Data Source and Quality
    data_source = models.CharField(
        max_length=300, help_text="Primary data source (e.g., 'Central Bank of Nigeria')"
    )

    secondary_sources = models.TextField(blank=True, help_text="Additional data sources")

    methodology_notes = models.TextField(blank=True, help_text="Data collection methodology")

    data_quality_notes = models.TextField(
        blank=True, help_text="Notes on data quality or limitations"
    )

    # Supporting Documents
    supporting_document = models.URLField(
        max_length=500, blank=True, help_text="Supporting documentation URL (PDF, Excel) (AWS S3)"
    )

    # Validation Workflow
    validation_status = models.CharField(
        max_length=30,
        choices=VALIDATION_STATUS,
        default="draft",
        help_text="Current validation status",
    )

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="waiis_submissions",
        help_text="IPA user who submitted data",
    )

    submitted_date = models.DateTimeField(
        null=True, blank=True, help_text="When data was submitted for review"
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waiis_reviews",
        help_text="IPAWAS admin who reviewed",
    )

    reviewed_date = models.DateTimeField(null=True, blank=True, help_text="When data was reviewed")

    review_notes = models.TextField(blank=True, help_text="Reviewer's notes or feedback")

    revision_notes = models.TextField(blank=True, help_text="Notes for revision if requested")

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waiis_approvals",
        help_text="Admin who approved publication",
    )

    approved_date = models.DateTimeField(null=True, blank=True, help_text="When data was approved")

    published_date = models.DateTimeField(
        null=True, blank=True, help_text="When data was published"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "WAIIS Data Submission"
        verbose_name_plural = "WAIIS Data Submissions"
        ordering = ["-year", "-quarter", "member_state"]
        unique_together = [["member_state", "year", "quarter", "data_type"]]
        indexes = [
            models.Index(fields=["member_state", "year", "quarter"]),
            models.Index(fields=["validation_status", "-submitted_date"]),
            models.Index(fields=["year", "data_type"]),
        ]

    def __str__(self):
        period = f"Q{self.quarter}" if self.quarter else "Annual"
        return f"{self.submission_id}: {self.member_state.country_name} - {self.year} {period}"

    def save(self, *args, **kwargs):
        if not self.submission_id:
            self.submission_id = self._generate_submission_id()

        # Auto-set dates based on status changes
        if self.validation_status == "submitted" and not self.submitted_date:
            self.submitted_date = timezone.now()

        if self.validation_status in ["approved", "published"] and not self.approved_date:
            self.approved_date = timezone.now()

        if self.validation_status == "published" and not self.published_date:
            self.published_date = timezone.now()

        super().save(*args, **kwargs)

    def _generate_submission_id(self):
        """Generate unique submission ID: WAIIS-{COUNTRY_CODE}-{YEAR}-{Q}-{NUM}"""
        country_code = self.member_state.country_code
        quarter_str = f"Q{self.quarter}" if self.quarter else "ANN"

        # Get last submission for this country, year, quarter
        last_sub = (
            WaiisDataSubmission.objects.filter(
                submission_id__startswith=f"WAIIS-{country_code}-{self.year}-{quarter_str}-"
            )
            .order_by("-submission_id")
            .first()
        )

        if last_sub:
            last_num = int(last_sub.submission_id.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"WAIIS-{country_code}-{self.year}-{quarter_str}-{new_num:02d}"

    def get_period_display(self):
        """Display the time period"""
        if self.quarter:
            return f"Q{self.quarter} {self.year}"
        return f"{self.year}"

    def can_edit(self, user):
        """Check if user can edit this submission"""
        if user.is_ipawas_admin:
            return True
        if hasattr(user, "ipa_profile"):
            return (
                user.ipa_profile.member_state == self.member_state
                and self.validation_status in ["draft", "revision_requested"]
            )
        return False

    def can_submit(self, user):
        """Check if user can submit for review"""
        if hasattr(user, "ipa_profile"):
            return (
                user.ipa_profile.member_state == self.member_state
                and user.ipa_profile.role in ["ipa_director", "ipa_manager", "ipa_data_entry"]
                and self.validation_status == "draft"
            )
        return False

    def can_approve(self, user):
        """Check if user can approve"""
        return user.is_ipawas_admin and self.validation_status == "under_review"


class WaiisSectorData(models.Model):
    """
    FDI breakdown by sector for each data submission.
    Allows detailed sector-level analysis.
    """

    submission = models.ForeignKey(
        WaiisDataSubmission,
        on_delete=models.CASCADE,
        related_name="sector_data",
        help_text="Parent submission",
    )

    sector = models.ForeignKey(
        Sector, on_delete=models.PROTECT, related_name="waiis_data", help_text="Investment sector"
    )

    fdi_inflow = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="FDI Inflow for this sector (USD millions)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    number_of_projects = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of projects in this sector",
        validators=[MinValueValidator(0)],
    )

    jobs_created = models.IntegerField(
        null=True,
        blank=True,
        help_text="Jobs created in this sector",
        validators=[MinValueValidator(0)],
    )

    percentage_of_total = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage of total FDI",
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
    )

    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "WAIIS Sector Data"
        verbose_name_plural = "WAIIS Sector Data"
        ordering = ["submission", "-fdi_inflow"]
        unique_together = ["submission", "sector"]
        indexes = [
            models.Index(fields=["submission", "sector"]),
            models.Index(fields=["sector", "-fdi_inflow"]),
        ]

    def __str__(self):
        return f"{self.submission.submission_id} - {self.sector.name}: ${self.fdi_inflow}M"


class WaiisSourceCountryData(models.Model):
    """
    FDI breakdown by source country for each submission.
    Tracks where investments are coming from.
    """

    submission = models.ForeignKey(
        WaiisDataSubmission,
        on_delete=models.CASCADE,
        related_name="source_country_data",
        help_text="Parent submission",
    )

    source_country_name = models.CharField(max_length=100, help_text="Country of origin for FDI")

    source_country_code = models.CharField(max_length=3, help_text="ISO country code", blank=True)

    fdi_inflow = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="FDI from this country (USD millions)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    number_of_projects = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of projects from this country",
        validators=[MinValueValidator(0)],
    )

    percentage_of_total = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage of total FDI",
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
    )

    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "WAIIS Source Country Data"
        verbose_name_plural = "WAIIS Source Country Data"
        ordering = ["submission", "-fdi_inflow"]
        unique_together = ["submission", "source_country_name"]
        indexes = [
            models.Index(fields=["submission", "source_country_name"]),
            models.Index(fields=["source_country_name", "-fdi_inflow"]),
        ]

    def __str__(self):
        return f"{self.submission.submission_id} - From {self.source_country_name}: ${self.fdi_inflow}M"


class WaiisDataAudit(models.Model):
    """
    Audit trail for all WAIIS data changes.
    Tracks who changed what and when for compliance.
    """

    ACTION_TYPES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("submitted", "Submitted for Review"),
        ("reviewed", "Reviewed"),
        ("approved", "Approved"),
        ("published", "Published"),
        ("rejected", "Rejected"),
        ("deleted", "Deleted"),
        ("revision_requested", "Revision Requested"),
    ]

    submission = models.ForeignKey(
        WaiisDataSubmission, on_delete=models.CASCADE, related_name="audit_trail"
    )

    action_type = models.CharField(
        max_length=30, choices=ACTION_TYPES, help_text="Type of action performed"
    )

    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, help_text="User who performed action"
    )

    changes = JSONField(null=True, blank=True, help_text="JSON of what changed")

    notes = models.TextField(blank=True, help_text="Additional notes")

    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of user")

    timestamp = models.DateTimeField(auto_now_add=True, help_text="When action occurred")

    class Meta:
        verbose_name = "WAIIS Data Audit Log"
        verbose_name_plural = "WAIIS Data Audit Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["submission", "-timestamp"]),
            models.Index(fields=["performed_by", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.submission.submission_id} - {self.action_type} by {self.performed_by} at {self.timestamp}"


class WaiisAnalyticsCache(models.Model):
    """
    Cached analytics and aggregated data for performance.
    Pre-computed statistics for dashboards.
    """

    CACHE_TYPES = [
        ("regional_total", "Regional Total"),
        ("country_comparison", "Country Comparison"),
        ("sector_breakdown", "Sector Breakdown"),
        ("source_country_analysis", "Source Country Analysis"),
        ("time_series", "Time Series Data"),
        ("top_performers", "Top Performing Countries"),
        ("growth_rates", "Growth Rates"),
    ]

    cache_type = models.CharField(
        max_length=50, choices=CACHE_TYPES, help_text="Type of cached data"
    )

    cache_key = models.CharField(max_length=200, unique=True, help_text="Unique cache identifier")

    year = models.IntegerField(null=True, blank=True, help_text="Data year (if applicable)")

    member_state = models.ForeignKey(
        MemberStateIPA,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="analytics_cache",
        help_text="Specific country (if applicable)",
    )

    sector = models.ForeignKey(
        Sector,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="analytics_cache",
        help_text="Specific sector (if applicable)",
    )

    cached_data = JSONField(help_text="Cached analytical data")

    expires_at = models.DateTimeField(help_text="When cache expires")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "WAIIS Analytics Cache"
        verbose_name_plural = "WAIIS Analytics Caches"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["cache_type", "year"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.cache_type} - {self.cache_key}"

    @property
    def is_expired(self):
        """Check if cache is expired"""
        return timezone.now() > self.expires_at

    @classmethod
    def get_cached(cls, cache_key):
        """Get cached data if not expired"""
        try:
            cache = cls.objects.get(cache_key=cache_key)
            if not cache.is_expired:
                return cache.cached_data
        except cls.DoesNotExist:
            pass
        return None

    @classmethod
    def set_cache(cls, cache_type, cache_key, data, expiry_hours=24, **kwargs):
        """Set cached data with expiry"""
        expires_at = timezone.now() + timezone.timedelta(hours=expiry_hours)

        cache, created = cls.objects.update_or_create(
            cache_key=cache_key,
            defaults={
                "cache_type": cache_type,
                "cached_data": data,
                "expires_at": expires_at,
                **kwargs,
            },
        )
        return cache


class WaiisDataExport(models.Model):
    """
    Track data exports for analytics and access control.
    Records when users download WAIIS data.
    """

    EXPORT_FORMATS = [
        ("csv", "CSV"),
        ("excel", "Excel"),
        ("pdf", "PDF"),
        ("json", "JSON"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waiis_exports",
        help_text="User who exported (if logged in)",
    )

    export_type = models.CharField(
        max_length=50, help_text="What was exported (e.g., 'regional_fdi', 'country_data')"
    )

    export_format = models.CharField(
        max_length=20, choices=EXPORT_FORMATS, help_text="Export file format"
    )

    filters_applied = JSONField(
        null=True, blank=True, help_text="Filters used (year, country, sector, etc.)"
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    user_agent = models.TextField(blank=True)

    file_generated = models.URLField(
        max_length=500,
        blank=True,
        help_text="Generated export file URL (optional storage) (AWS S3)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "WAIIS Data Export"
        verbose_name_plural = "WAIIS Data Exports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else "Anonymous"
        return f"{self.export_type} ({self.export_format}) by {user_str}"
