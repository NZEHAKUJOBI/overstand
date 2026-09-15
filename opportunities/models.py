"""
IPAWAS Opportunities App Models
================================

This module contains all database models for Investment Opportunities:
- InvestmentOpportunity: Core project/opportunity entity
- OpportunityDocument: Supporting documents and files
- OpportunityInquiry: Investor expressions of interest
- OpportunitySector: Links opportunities to sectors (if multiple)
- OpportunityUpdate: Status updates and progress tracking

These models support the investment marketplace functionality.
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

# Import from other apps
from accounts.models import User
from core.models import Sector
from members.models import MemberStateIPA


class InvestmentOpportunity(models.Model):
    """
    Core investment opportunity/project model.

    Represents investment projects from member states.
    Can be country-specific or regional (multi-country).
    """

    OPPORTUNITY_TYPES = [
        ("greenfield", "Greenfield Project"),
        ("brownfield", "Brownfield Project"),
        ("ppp", "Public-Private Partnership"),
        ("privatization", "Privatization"),
        ("joint_venture", "Joint Venture"),
        ("expansion", "Expansion Opportunity"),
        ("acquisition", "Acquisition"),
        ("concession", "Concession"),
    ]

    PROJECT_STAGES = [
        ("concept", "Concept Stage"),
        ("feasibility", "Feasibility Study Complete"),
        ("ready", "Investment Ready"),
        ("partial", "Partially Funded"),
        ("negotiation", "Under Negotiation"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("under_review", "Under Review"),
        ("active", "Published / Active"),
        ("negotiation", "Under Negotiation"),
        ("funded", "Funded / Closed"),
        ("suspended", "Archived"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_LEVELS = [
        ("high", "High Priority"),
        ("medium", "Medium Priority"),
        ("standard", "Standard"),
    ]

    # Basic Information
    title = models.CharField(max_length=300, help_text="Opportunity title")

    slug = models.SlugField(max_length=300, unique=True, help_text="URL-friendly version")

    reference_number = models.CharField(
        max_length=50, unique=True, help_text="Unique reference (e.g., OPP-NGA-2025-001)"
    )

    summary = models.TextField(
        help_text="Brief summary (2-3 sentences, 200 chars max)", max_length=500
    )

    description = models.TextField(help_text="Detailed project description")

    # Classification
    opportunity_type = models.CharField(
        max_length=50, choices=OPPORTUNITY_TYPES, help_text="Type of investment opportunity"
    )

    primary_sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="primary_opportunities",
        help_text="Main sector for this opportunity",
    )

    secondary_sectors = models.ManyToManyField(
        Sector,
        blank=True,
        related_name="secondary_opportunities",
        help_text="Additional relevant sectors",
    )

    sub_sector = models.CharField(
        max_length=200, blank=True, help_text="Specific sub-sector or industry"
    )

    # Location
    primary_country = models.ForeignKey(
        MemberStateIPA,
        on_delete=models.CASCADE,
        related_name="opportunities",
        help_text="Primary country for this opportunity",
    )

    is_regional = models.BooleanField(
        default=False, help_text="Is this a regional/multi-country opportunity?"
    )

    participating_countries = models.ManyToManyField(
        MemberStateIPA,
        blank=True,
        related_name="regional_opportunities",
        help_text="Countries involved (if regional)",
    )

    specific_location = models.CharField(
        max_length=300, blank=True, help_text="Specific city, state, or region"
    )

    geographic_coordinates = models.JSONField(
        null=True,
        blank=True,
        help_text="Lat/Long for mapping (e.g., {'lat': 9.0765, 'lng': 7.3986})",
    )

    # Investment Details
    investment_required_min = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Minimum investment required (USD)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    investment_required_max = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum investment (USD) - optional",
    )

    investment_breakdown = models.JSONField(
        null=True,
        blank=True,
        help_text="Cost breakdown (e.g., {'land': 1000000, 'equipment': 5000000})",
    )

    expected_roi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected ROI percentage",
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("999.99"))],
    )

    payback_period = models.CharField(
        max_length=100, blank=True, help_text="Expected payback period (e.g., '3-5 years')"
    )

    # Project Status
    project_stage = models.CharField(
        max_length=50,
        choices=PROJECT_STAGES,
        default="concept",
        help_text="Current stage of project development",
    )

    implementation_timeline = models.CharField(
        max_length=200, blank=True, help_text="Expected timeline (e.g., '18-24 months')"
    )

    start_date_target = models.DateField(null=True, blank=True, help_text="Target start date")

    # Implementing Entity
    implementing_agency = models.CharField(
        max_length=300, blank=True, help_text="Government agency or organization implementing"
    )

    implementing_agency_contact = models.CharField(
        max_length=300, blank=True, help_text="Contact person at implementing agency"
    )

    # Investor Requirements
    investor_profile = models.TextField(
        blank=True, help_text="Desired investor profile and qualifications"
    )

    technical_requirements = models.TextField(
        blank=True, help_text="Technical capabilities or expertise required"
    )

    minimum_equity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum equity required (USD)",
    )

    local_content_requirements = models.TextField(
        blank=True, help_text="Local content or local partnership requirements"
    )

    # Market & Financial
    market_analysis = models.TextField(blank=True, help_text="Market opportunity and analysis")

    target_market = models.CharField(
        max_length=300, blank=True, help_text="Target market (e.g., 'Regional - ECOWAS', 'Global')"
    )

    revenue_projections = models.TextField(blank=True, help_text="Expected revenue projections")

    financial_incentives_available = models.TextField(
        blank=True, help_text="Tax incentives and financial support available"
    )

    # Regulatory & Legal
    regulatory_framework = models.TextField(blank=True, help_text="Relevant laws and regulations")

    approval_process = models.TextField(blank=True, help_text="Steps to get project approved")

    licenses_required = models.TextField(blank=True, help_text="Required licenses and permits")

    land_availability = models.TextField(
        blank=True, help_text="Land availability and acquisition process"
    )

    # Risk Assessment
    risk_factors = models.TextField(blank=True, help_text="Key risk factors to consider")

    mitigation_measures = models.TextField(
        blank=True, help_text="Risk mitigation strategies in place"
    )

    # Status & Management
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", help_text="Publication status"
    )

    priority_level = models.CharField(
        max_length=20,
        choices=PRIORITY_LEVELS,
        default="standard",
        help_text="Priority level for marketing",
    )

    published = models.BooleanField(default=False, help_text="Is this opportunity published?")

    published_date = models.DateTimeField(null=True, blank=True, help_text="Date when published")

    featured = models.BooleanField(default=False, help_text="Featured opportunity (homepage, etc.)")

    # Media
    thumbnail_image = models.URLField(
        max_length=500, blank=True, help_text="Thumbnail URL for cards (400x250) (AWS S3)"
    )
    thumbnail_image_file = models.ForeignKey(
        "media_app.MediaFile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="opportunity_thumbnails",
    )

    hero_image = models.URLField(
        max_length=500, blank=True, help_text="Hero banner URL (1920x1080) (AWS S3)"
    )
    hero_image_file = models.ForeignKey(
        "media_app.MediaFile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="opportunity_heroes",
    )

    gallery_images = models.JSONField(
        default=list, blank=True, help_text="List of image URLs for gallery"
    )

    video_url = models.URLField(blank=True, help_text="YouTube or Vimeo video URL")

    factsheet_url = models.URLField(
        blank=True,
        help_text="Public link to the opportunity factsheet (Google Drive, Dropbox, S3, etc.)",
    )

    # Analytics
    views_count = models.IntegerField(default=0, help_text="Number of views")

    inquiries_count = models.IntegerField(default=0, help_text="Number of inquiries received")

    downloads_count = models.IntegerField(default=0, help_text="Number of document downloads")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="opportunities_created",
        help_text="User who created this opportunity",
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunities_approved",
        help_text="Admin who approved publication",
    )

    approved_date = models.DateTimeField(null=True, blank=True, help_text="Date when approved")

    class Meta:
        verbose_name = "Investment Opportunity"
        verbose_name_plural = "Investment Opportunities"
        ordering = ["-featured", "-priority_level", "-published_date", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published"]),
            models.Index(fields=["primary_country", "status"]),
            models.Index(fields=["primary_sector", "status"]),
            models.Index(fields=["-featured", "-priority_level"]),
        ]

    def __str__(self):
        return f"{self.reference_number}: {self.title}"

    def save(self, *args, **kwargs):
        # Generate slug
        if not self.slug:
            self.slug = slugify(self.title)

        # Generate reference number
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()

        # Set published_date when first published
        if self.published and not self.published_date:
            self.published_date = timezone.now()

        super().save(*args, **kwargs)

    def _generate_reference_number(self):
        """Generate unique reference number: OPP-{COUNTRY_CODE}-{YEAR}-{NUM}"""
        year = timezone.now().year
        country_code = self.primary_country.country_code

        # Get last opportunity for this country and year
        last_opp = (
            InvestmentOpportunity.objects.filter(
                reference_number__startswith=f"OPP-{country_code}-{year}-"
            )
            .order_by("-reference_number")
            .first()
        )

        if last_opp:
            last_num = int(last_opp.reference_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"OPP-{country_code}-{year}-{new_num:03d}"

    @property
    def resolved_thumbnail_url(self):
        if self.thumbnail_image_file_id:
            return self.thumbnail_image_file.cloudinary_secure_url
        return self.thumbnail_image

    @property
    def resolved_hero_url(self):
        if self.hero_image_file_id:
            return self.hero_image_file.cloudinary_secure_url
        return self.hero_image

    def get_absolute_url(self):
        return reverse("opportunities:detail", kwargs={"slug": self.slug})

    def get_investment_range_display(self):
        """Format investment range for display (full comma-formatted numbers)."""
        min_val = f"${self.investment_required_min:,.0f}"
        if self.investment_required_max:
            max_val = f"${self.investment_required_max:,.0f}"
            return f"{min_val} - {max_val}"
        return f"{min_val}+"

    def get_investment_range_short(self):
        """
        Abbreviated investment range for display cards (e.g. $50M, $1.5B).
        Keeps card labels short so they don't overflow at large font sizes.
        """
        def _fmt(value):
            v = float(value)
            if v >= 1_000_000_000:
                n = v / 1_000_000_000
                return f"${n:.1f}B".replace(".0B", "B")
            if v >= 1_000_000:
                n = v / 1_000_000
                return f"${n:.1f}M".replace(".0M", "M")
            if v >= 1_000:
                n = v / 1_000
                return f"${n:.1f}K".replace(".0K", "K")
            return f"${v:,.0f}"

        min_val = _fmt(self.investment_required_min)
        if self.investment_required_max:
            max_val = _fmt(self.investment_required_max)
            return f"{min_val} – {max_val}"
        return f"{min_val}+"

    def increment_views(self):
        """Increment view count atomically to avoid race conditions."""
        from django.db.models import F
        InvestmentOpportunity.objects.filter(pk=self.pk).update(
            views_count=F("views_count") + 1
        )

    def increment_inquiries(self):
        """Increment inquiry count atomically to avoid race conditions."""
        from django.db.models import F
        InvestmentOpportunity.objects.filter(pk=self.pk).update(
            inquiries_count=F("inquiries_count") + 1
        )

    def increment_downloads(self):
        """Increment download count atomically to avoid race conditions."""
        from django.db.models import F
        InvestmentOpportunity.objects.filter(pk=self.pk).update(
            downloads_count=F("downloads_count") + 1
        )


class OpportunityDocument(models.Model):
    """
    Supporting documents for opportunities.
    Examples: Feasibility studies, business plans, technical specs, etc.
    """

    DOCUMENT_TYPES = [
        ("feasibility", "Feasibility Study"),
        ("business_plan", "Business Plan"),
        ("technical", "Technical Specifications"),
        ("financial", "Financial Projections"),
        ("legal", "Legal Documents"),
        ("environmental", "Environmental Assessment"),
        ("market_study", "Market Study"),
        ("presentation", "Presentation"),
        ("brochure", "Brochure"),
        ("other", "Other"),
    ]

    opportunity = models.ForeignKey(
        InvestmentOpportunity, on_delete=models.CASCADE, related_name="documents"
    )

    title = models.CharField(max_length=300, help_text="Document title")

    document_type = models.CharField(
        max_length=50, choices=DOCUMENT_TYPES, help_text="Type of document"
    )

    file = models.URLField(
        max_length=500, help_text="Document URL (PDF, Word, Excel, etc.) (AWS S3)"
    )

    file_size = models.CharField(max_length=20, blank=True, help_text="File size (auto-calculated)")

    description = models.TextField(blank=True, help_text="Brief description of document")

    is_public = models.BooleanField(
        default=True, help_text="Publicly downloadable? (False = requires login/approval)"
    )

    requires_nda = models.BooleanField(default=False, help_text="Does this require NDA to access?")

    download_count = models.IntegerField(default=0, help_text="Number of downloads")

    display_order = models.IntegerField(default=0, help_text="Display order")

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Opportunity Document"
        verbose_name_plural = "Opportunity Documents"
        ordering = ["opportunity", "display_order", "title"]
        indexes = [
            models.Index(fields=["opportunity", "document_type"]),
            models.Index(fields=["document_type", "is_public"]),
            models.Index(fields=["opportunity", "display_order"]),
        ]

    def __str__(self):
        return f"{self.opportunity.reference_number} - {self.title}"

    def increment_downloads(self):
        """Increment download count"""
        self.download_count += 1
        self.save(update_fields=["download_count"])


class OpportunityInquiry(models.Model):
    """
    Investor inquiries/expressions of interest for specific opportunities.
    """

    INQUIRY_STATUS = [
        ("new", "New"),
        ("reviewed", "Reviewed"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("disqualified", "Disqualified"),
        ("closed", "Closed"),
    ]

    # Linked opportunity
    opportunity = models.ForeignKey(
        InvestmentOpportunity, on_delete=models.CASCADE, related_name="inquiries"
    )

    reference_number = models.CharField(
        max_length=50, unique=True, help_text="Unique inquiry reference"
    )

    # Investor Information
    full_name = models.CharField(max_length=200, help_text="Investor/representative name")

    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)

    company_name = models.CharField(
        max_length=200, blank=True, help_text="Company/Organization name"
    )

    company_country = models.CharField(
        max_length=100, blank=True, help_text="Country where company is based"
    )

    company_website = models.URLField(blank=True)

    # Investment Profile
    investment_capacity = models.CharField(
        max_length=100, blank=True, help_text="Investment capacity range"
    )

    investment_timeline = models.CharField(
        max_length=100, blank=True, help_text="Expected investment timeline"
    )

    partnership_interest = models.CharField(
        max_length=50,
        choices=[
            ("full_ownership", "Full Ownership"),
            ("majority", "Majority Stake"),
            ("minority", "Minority Stake"),
            ("joint_venture", "Joint Venture"),
            ("other", "Other"),
        ],
        blank=True,
        help_text="Ownership/partnership preference",
    )

    # Inquiry Details
    message = models.TextField(help_text="Investor's message/inquiry")

    specific_questions = models.TextField(
        blank=True, help_text="Specific questions about the opportunity"
    )

    # Additional Information
    experience_in_sector = models.TextField(
        blank=True, help_text="Relevant experience in this sector"
    )

    previous_investments = models.TextField(
        blank=True, help_text="Previous investments in region/sector"
    )

    requires_site_visit = models.BooleanField(
        default=False, help_text="Does investor want to schedule site visit?"
    )

    requires_nda = models.BooleanField(
        default=False, help_text="Does investor require NDA before sharing details?"
    )

    # Processing
    status = models.CharField(
        max_length=20, choices=INQUIRY_STATUS, default="new", help_text="Inquiry processing status"
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_opportunity_inquiries",
        help_text="IPA staff handling this inquiry",
    )

    internal_notes = models.TextField(
        blank=True, help_text="Internal notes (not visible to investor)"
    )

    follow_up_date = models.DateField(null=True, blank=True, help_text="Scheduled follow-up date")

    # Communication
    investor_contacted_date = models.DateTimeField(
        null=True, blank=True, help_text="When investor was first contacted"
    )

    last_contact_date = models.DateTimeField(
        null=True, blank=True, help_text="Last communication date"
    )

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Opportunity Inquiry"
        verbose_name_plural = "Opportunity Inquiries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["opportunity", "status"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.full_name} ({self.opportunity.title})"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()
        super().save(*args, **kwargs)

        # Increment opportunity inquiry count
        if self._state.adding:  # Only on creation
            self.opportunity.increment_inquiries()

    def _generate_reference_number(self):
        """Generate unique reference: INQ-{OPP_REF}-{NUM}"""
        opp_ref = self.opportunity.reference_number

        # Get last inquiry for this opportunity
        last_inq = (
            OpportunityInquiry.objects.filter(reference_number__startswith=f"INQ-{opp_ref}-")
            .order_by("-reference_number")
            .first()
        )

        if last_inq:
            last_num = int(last_inq.reference_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"INQ-{opp_ref}-{new_num:03d}"


class OpportunityUpdate(models.Model):
    """
    Status updates and progress tracking for opportunities.
    Allows IPAs to post updates as projects progress.
    """

    UPDATE_TYPES = [
        ("status_change", "Status Change"),
        ("milestone", "Milestone Achieved"),
        ("funding", "Funding Update"),
        ("partnership", "Partnership Announcement"),
        ("progress", "General Progress"),
        ("other", "Other"),
    ]

    opportunity = models.ForeignKey(
        InvestmentOpportunity, on_delete=models.CASCADE, related_name="updates"
    )

    update_type = models.CharField(max_length=50, choices=UPDATE_TYPES, help_text="Type of update")

    title = models.CharField(max_length=300, help_text="Update title")

    description = models.TextField(help_text="Detailed update description")

    is_public = models.BooleanField(default=True, help_text="Visible to public?")

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="opportunity_updates_created"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Opportunity Update"
        verbose_name_plural = "Opportunity Updates"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["opportunity", "-created_at"]),
            models.Index(fields=["update_type", "is_public"]),
            models.Index(fields=["opportunity", "is_public"]),
        ]

    def __str__(self):
        return f"{self.opportunity.reference_number} - {self.title}"
