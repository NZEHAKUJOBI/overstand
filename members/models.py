"""
IPAWAS Members App Models
=========================

This module contains all database models for the Member States section:
- MemberStateIPA: Core entity for each country's IPA
- MemberStateSector: Country-sector relationships
- InvestmentIncentive: Tax breaks, incentives by country
- SuccessStory: Case studies by country
- InvestorInquiry: Contact form submissions
- FDIDataPoint: Historical FDI data for charts/WAIIS
- IPAStaff: Key personnel (optional)

Note: Mali, Niger, and Burkina Faso are no longer active member states.
They should be marked as is_active=False in the database.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

# Import from core app
from accounts.models import User
from core.models import Sector


class MemberStateIPA(models.Model):
    """
    Core model representing each ECOWAS member state's IPA.

    This is the central entity for the Member States portal,
    containing all country-level information and IPA details.

    Note: Mali, Niger, and Burkina Faso should have is_active=False
    """

    # Basic Information
    country_name = models.CharField(
        max_length=100, unique=True, help_text="Official country name (e.g., 'Nigeria')"
    )

    slug = models.SlugField(
        max_length=100, unique=True, help_text="URL-friendly version (e.g., 'nigeria')"
    )

    country_code = models.CharField(
        max_length=3, unique=True, help_text="ISO 3166-1 alpha-3 code (e.g., 'NGA')"
    )

    flag_emoji = models.CharField(
        max_length=10, help_text="Country flag emoji (e.g., '🇳🇬')", blank=True
    )

    # IPA Information
    ipa_full_name = models.CharField(
        max_length=200, help_text="Full IPA name (e.g., 'Nigerian Investment Promotion Commission')"
    )

    ipa_acronym = models.CharField(max_length=20, help_text="IPA acronym (e.g., 'NIPC')")

    ipa_website = models.URLField(help_text="Official IPA website", blank=True)

    ipa_logo = models.URLField(max_length=500, blank=True, help_text="IPA logo URL (AWS S3)")

    # Media library references (FK to MediaFile — set by the media picker)
    ipa_logo_file = models.ForeignKey(
        "media_app.MediaFile", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="logo_member_states",
    )
    hero_image_file = models.ForeignKey(
        "media_app.MediaFile", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="hero_member_states",
    )
    card_image_file = models.ForeignKey(
        "media_app.MediaFile", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="card_member_states",
    )

    # Overview & Description
    overview = models.TextField(help_text="Country/IPA overview (300-500 words)", blank=True)

    tagline = models.CharField(
        max_length=200,
        help_text="Compelling one-liner (e.g., 'Gateway to West Africa')",
        blank=True,
    )

    # Economic Indicators
    population = models.BigIntegerField(
        help_text="Population count", validators=[MinValueValidator(0)]
    )

    population_display = models.CharField(
        max_length=20, help_text="Display format (e.g., '227M', '33.8M')", blank=True
    )

    population_growth = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Population growth rate (%)",
        null=True,
        blank=True,
        validators=[MinValueValidator(-10)],
    )

    median_age = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="Median age in years",
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    urbanization_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Urbanization rate (%)",
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    literacy_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Literacy rate (%)",
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    gdp = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="GDP in USD billions",
        validators=[MinValueValidator(0)],
    )

    gdp_display = models.CharField(
        max_length=20, help_text="Display format (e.g., '$252B', '$87.5B')", blank=True
    )

    gdp_growth_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="GDP growth rate percentage",
        null=True,
        blank=True,
    )

    gdp_per_capita = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="GDP per capita in USD", null=True, blank=True
    )

    inflation_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Inflation rate (%)",
        null=True,
        blank=True,
        validators=[MinValueValidator(-50)],
    )

    fdi_inflows = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="FDI inflows in USD millions",
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    corporate_tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Corporate tax rate (%)",
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    days_to_start_business = models.IntegerField(
        help_text="Days to start a business",
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    # Trade Data
    total_exports = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total exports in USD millions",
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    total_imports = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total imports in USD millions",
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    key_industries = models.TextField(help_text="Key industries (comma-separated)", blank=True)

    trade_agreements = models.TextField(help_text="Trade agreements (comma-separated)", blank=True)

    # Infrastructure
    electricity_access = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Electricity access (%)",
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    internet_penetration = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Internet penetration (%)",
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    paved_roads_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Paved roads (%)",
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    number_of_airports = models.IntegerField(
        help_text="Number of airports",
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    # Geographic Information
    capital_city = models.CharField(max_length=100, help_text="Capital city name")

    major_cities = models.JSONField(help_text="List of major cities", default=list, blank=True)

    geographic_region = models.CharField(
        max_length=50,
        choices=[
            ("west_coast", "West Coast"),
            ("sahel", "Sahel"),
            ("gulf_of_guinea", "Gulf of Guinea"),
        ],
        help_text="Regional classification",
        blank=True,
    )

    # Language & Currency
    official_language = models.CharField(
        max_length=50,
        choices=[
            ("english", "English"),
            ("french", "French"),
            ("portuguese", "Portuguese"),
        ],
        help_text="Official language",
    )

    currency_name = models.CharField(
        max_length=100, help_text="Currency name (e.g., 'Nigerian Naira')"
    )

    currency_code = models.CharField(max_length=10, help_text="Currency code (e.g., 'NGN')")

    currency_symbol = models.CharField(
        max_length=10, help_text="Currency symbol (e.g., '₦')", blank=True
    )

    # Contact Information
    contact_email = models.EmailField(help_text="Primary IPA contact email")

    contact_phone = models.CharField(max_length=50, help_text="Primary phone number", blank=True)

    physical_address = models.TextField(help_text="Complete physical address", blank=True)

    office_hours = models.CharField(
        max_length=200, help_text="Office hours (e.g., 'Mon-Fri, 8:00 AM - 4:00 PM')", blank=True
    )

    # Social Media
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    # Images
    hero_image = models.URLField(
        max_length=500, blank=True, help_text="Hero banner URL (1920x1080) (AWS S3)"
    )

    card_image = models.URLField(
        max_length=500, blank=True, help_text="Card thumbnail URL (400x250) (AWS S3)"
    )

    # Investment Climate
    ease_of_doing_business_rank = models.IntegerField(
        help_text="World Bank ranking", null=True, blank=True, validators=[MinValueValidator(1)]
    )

    competitiveness_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Global Competitiveness Index score",
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    # Additional Data
    time_zone = models.CharField(
        max_length=50, help_text="Time zone (e.g., 'GMT+1')", default="GMT"
    )

    investment_guide_pdf = models.URLField(
        max_length=500, blank=True, help_text="Downloadable investment guide URL (AWS S3)"
    )

    doing_business_pdf = models.URLField(
        max_length=500, blank=True, help_text="Doing Business guide PDF URL (AWS S3)"
    )

    incentives_brochure_pdf = models.URLField(
        max_length=500, blank=True, help_text="Investment incentives brochure URL"
    )

    infrastructure_report_pdf = models.URLField(
        max_length=500, blank=True, help_text="Infrastructure and logistics report URL"
    )

    legal_framework_pdf = models.URLField(
        max_length=500, blank=True, help_text="Legal and regulatory framework document URL"
    )

    sector_profiles_pdf = models.URLField(
        max_length=500, blank=True, help_text="Sector profiles document URL"
    )

    # SEO Settings
    meta_title = models.CharField(
        max_length=60, blank=True, help_text="Page title for search engines (max 60 chars)"
    )

    meta_description = models.TextField(
        max_length=160, blank=True, help_text="Meta description for search engines (max 160 chars)"
    )

    meta_keywords = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated SEO keywords"
    )

    og_title = models.CharField(
        max_length=100, blank=True, help_text="Open Graph title for social sharing"
    )

    og_description = models.TextField(
        max_length=300, blank=True, help_text="Open Graph description for social sharing"
    )

    og_image_url = models.URLField(
        max_length=500, blank=True, help_text="Open Graph image URL for social sharing"
    )

    # Storage quota — 1 GB per member state (enforced on media upload)
    storage_quota_bytes = models.BigIntegerField(
        default=1_073_741_824, help_text="Media library quota in bytes (default 1 GB)"
    )

    # Metadata
    is_active = models.BooleanField(
        default=True, help_text="Set False for Mali, Niger, Burkina Faso"
    )

    display_order = models.IntegerField(
        default=0, help_text="Custom sort order (lower numbers first)"
    )

    featured = models.BooleanField(
        default=False, help_text="Featured on homepage or special sections"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Member State IPA"
        verbose_name_plural = "Member State IPAs"
        ordering = ["display_order", "country_name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["country_code"]),
            models.Index(fields=["is_active", "country_name"]),
            models.Index(fields=["is_active", "featured"]),
            models.Index(fields=["display_order"]),
            models.Index(fields=["official_language", "is_active"]),
        ]

    def __str__(self):
        return f"{self.country_name} ({self.ipa_acronym})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.country_name)
        # Always recalculate display fields so edits via the dashboard are reflected
        # immediately on the public page — not just on first creation.
        if self.population:
            self.population_display = self._format_population()
        if self.gdp:
            self.gdp_display = self._format_gdp()
        super().save(*args, **kwargs)

    def _format_population(self):
        """Format population for display (e.g., 227M, 33.8M)"""
        if self.population >= 1_000_000:
            return f"{self.population / 1_000_000:.1f}M"
        return str(self.population)

    def _format_gdp(self):
        """Format GDP for display (e.g., $21.7B).

        The field is intended to store USD in BILLIONS (e.g. 21.7 = $21.7B).
        Guard against data-entry mistakes where raw USD was entered instead of
        billions: values ≥ 1,000,000,000 are auto-converted to the right unit.
        No ECOWAS economy exceeds $1 trillion, so the threshold is unambiguous.
        """
        value = float(self.gdp)
        if value >= 1_000_000_000_000:
            return f"${value / 1_000_000_000_000:.1f}T"
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"
        if value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        # Standard path: value already stored in billions
        return f"${value:.1f}B"

    @property
    def formatted_gdp(self):
        """Always-fresh GDP display — use this in templates instead of gdp_display.

        gdp_display is a stored field that may be stale if data was entered before
        _format_gdp() was made magnitude-aware. This property always re-computes.
        """
        return self._format_gdp() if self.gdp else "—"

    @property
    def formatted_gdp_per_capita(self):
        """GDP per capita formatted as a currency string (e.g., $1,500)."""
        if not self.gdp_per_capita:
            return "N/A"
        value = float(self.gdp_per_capita)
        if value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"${value:,.0f}"
        return f"${value:.0f}"

    def get_absolute_url(self):
        return reverse("member_states:detail", kwargs={"country_slug": self.slug})

    def get_profile_completion(self):
        """
        Canonical profile completion calculation — used by all dashboard views.

        Returns a dict:
            {
                "percentage": int (0–100),
                "completed": int,
                "total": int,
                "items": [{"name": str, "completed": bool}, ...]
            }

        10-point checklist covering basic info, visuals, economic data, content, and resources.
        """
        checks = [
            ("Basic Information", bool(self.ipa_full_name and self.overview)),
            ("Contact Email", bool(self.contact_email)),
            ("IPA Logo", bool(self.ipa_logo)),
            ("Hero Image", bool(self.hero_image)),
            ("Economic Data (GDP & Population)", bool(self.gdp and self.population)),
            ("FDI Inflows", bool(self.fdi_inflows)),
            ("Priority Sectors", self.sectors.exists()),
            ("Published Opportunities", self.opportunities.filter(status="active", published=True).exists()),
            ("Investment Guide PDF", bool(self.investment_guide_pdf)),
            ("Doing Business Guide PDF", bool(self.doing_business_pdf)),
        ]

        items = [{"name": name, "completed": done} for name, done in checks]
        completed = sum(1 for _, done in checks if done)
        total = len(checks)

        return {
            "percentage": round((completed / total) * 100),
            "completed": completed,
            "total": total,
            "items": items,
        }

    def get_opportunities_count(self):
        """Get count of active investment opportunities"""
        return self.opportunities.filter(status="active", published=True).count()

    def get_priority_sectors(self):
        """Get priority sectors for this country"""
        return self.sectors.filter(is_priority=True).select_related("sector")

    @property
    def population_millions(self):
        """Return population in millions (e.g., 220.5)"""
        if self.population:
            return round(self.population / 1_000_000, 1)
        return 0

    @property
    def gdp_usd_billions(self):
        """Return GDP in billions USD. gdp field already stores the value in billions
        (e.g. 87.5 means $87.5 billion)."""
        if self.gdp:
            return round(float(self.gdp), 1)
        return 0


class MemberStateSector(models.Model):
    """
    Links member states to sectors with priority indicators.
    Defines which sectors each country focuses on.
    """

    member_state = models.ForeignKey(
        MemberStateIPA, on_delete=models.CASCADE, related_name="sectors"
    )

    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="member_states")

    is_priority = models.BooleanField(
        default=False, help_text="Is this a priority sector for this country?"
    )

    description = models.TextField(help_text="Country-specific sector description", blank=True)

    investment_potential = models.TextField(
        help_text="Investment opportunities in this sector", blank=True
    )

    display_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Member State Sector"
        verbose_name_plural = "Member State Sectors"
        ordering = ["member_state", "display_order", "sector__name"]
        unique_together = ["member_state", "sector"]
        indexes = [
            models.Index(fields=["member_state", "is_priority"]),
            models.Index(fields=["sector", "is_priority"]),
            models.Index(fields=["member_state", "display_order"]),
        ]

    def __str__(self):
        priority = "⭐ " if self.is_priority else ""
        return f"{priority}{self.member_state.country_name} - {self.sector.name}"


class InvestmentIncentive(models.Model):
    """
    Investment incentives offered by each member state.
    Includes tax breaks, exemptions, and special benefits.
    """

    INCENTIVE_TYPES = [
        ("tax_holiday", "Tax Holiday"),
        ("tax_credit", "Tax Credit"),
        ("customs_exemption", "Customs Duty Exemption"),
        ("vat_exemption", "VAT Exemption"),
        ("capital_allowance", "Capital Allowance"),
        ("free_zone", "Free Trade Zone Benefits"),
        ("repatriation", "Profit Repatriation Guarantee"),
        ("other", "Other"),
    ]

    member_state = models.ForeignKey(
        MemberStateIPA, on_delete=models.CASCADE, related_name="incentives"
    )

    title = models.CharField(max_length=200, help_text="Incentive name/title")

    incentive_type = models.CharField(max_length=50, choices=INCENTIVE_TYPES)

    description = models.TextField(help_text="Detailed description of the incentive")

    duration = models.CharField(
        max_length=100, help_text="Duration (e.g., '5-10 years', 'Ongoing')", blank=True
    )

    eligibility_criteria = models.TextField(
        help_text="Who qualifies for this incentive", blank=True
    )

    applicable_sectors = models.ManyToManyField(
        Sector, related_name="incentives", blank=True, help_text="Which sectors can benefit"
    )

    benefit_amount = models.CharField(
        max_length=100,
        help_text="Quantifiable benefit (e.g., '100% tax exemption', '5% annual credit')",
        blank=True,
    )

    document_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Supporting document URL (uploaded to Cloudinary)",
    )

    document_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original filename of the uploaded document",
    )

    # Media library reference (FK replaces document_url for new uploads)
    document_file = models.ForeignKey(
        "media_app.MediaFile", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="incentive_documents",
    )

    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["member_state", "display_order", "title"]
        verbose_name = "Investment Incentive"
        verbose_name_plural = "Investment Incentives"
        indexes = [
            models.Index(fields=["member_state", "incentive_type"]),
            models.Index(fields=["incentive_type", "is_active"]),
            models.Index(fields=["member_state", "display_order"]),
        ]

    def __str__(self):
        return f"{self.member_state.country_name} - {self.title}"

    @property
    def resolved_document_url(self):
        """Returns document URL from MediaFile FK if set, else legacy URLField."""
        if self.document_file_id:
            return self.document_file.cloudinary_secure_url
        return self.document_url

    @property
    def resolved_document_name(self):
        if self.document_file_id:
            return self.document_file.name
        return self.document_name


class SuccessStory(models.Model):
    """
    Investment success stories for each member state.
    Case studies showcasing successful investments.
    """

    member_state = models.ForeignKey(
        MemberStateIPA, on_delete=models.CASCADE, related_name="success_stories"
    )

    title = models.CharField(max_length=200, help_text="Success story headline")

    company_name = models.CharField(max_length=200, help_text="Investing company name")

    company_origin = models.CharField(
        max_length=100, help_text="Company's country of origin", blank=True
    )

    sector = models.ForeignKey(
        Sector, on_delete=models.SET_NULL, null=True, related_name="success_stories"
    )

    investment_amount = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="Investment amount in USD", null=True, blank=True
    )

    investment_amount_display = models.CharField(
        max_length=50, help_text="Display format (e.g., '$50M', '$2.5B')", blank=True
    )

    jobs_created = models.IntegerField(help_text="Number of jobs created", null=True, blank=True)

    year = models.IntegerField(
        help_text="Year of investment",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )

    summary = models.TextField(help_text="Brief summary (2-3 sentences)")

    full_story = models.TextField(help_text="Complete success story", blank=True)

    impact = models.TextField(help_text="Economic/social impact", blank=True)

    image = models.URLField(
        max_length=500, blank=True, help_text="Company/project image URL (AWS S3)"
    )

    published = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["member_state", "-featured", "display_order", "-year"]
        verbose_name = "Success Story"
        verbose_name_plural = "Success Stories"
        indexes = [
            models.Index(fields=["member_state", "published"]),
            models.Index(fields=["sector", "published"]),
            models.Index(fields=["featured", "-year"]),
            models.Index(fields=["-year", "published"]),
        ]

    def __str__(self):
        return f"{self.company_name} in {self.member_state.country_name}"


class InvestorInquiry(models.Model):
    """
    Captures inquiries from investors via IPA contact forms.
    Integrates with email system to notify IPAs.
    """

    INQUIRY_TYPES = [
        ("general", "General Inquiry"),
        ("investment_opportunity", "Investment Opportunity"),
        ("partnership", "Partnership Request"),
        ("market_research", "Market Research"),
        ("site_visit", "Site Visit Request"),
        ("incentives", "Incentives Information"),
        ("registration", "Business Registration"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("in_progress", "In Progress"),
        ("responded", "Responded"),
        ("closed", "Closed"),
    ]

    # Inquiry Details
    member_state = models.ForeignKey(
        MemberStateIPA, on_delete=models.CASCADE, related_name="inquiries"
    )

    inquiry_type = models.CharField(max_length=50, choices=INQUIRY_TYPES)

    reference_number = models.CharField(
        max_length=50, unique=True, help_text="Auto-generated (e.g., INQ-2025-0001)"
    )

    # Investor Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    company_country = models.CharField(max_length=100, blank=True)

    # Investment Details
    sector_of_interest = models.ForeignKey(
        Sector, on_delete=models.SET_NULL, null=True, blank=True, related_name="inquiries"
    )

    estimated_investment = models.CharField(
        max_length=100, help_text="Investment range", blank=True
    )

    # Message
    subject = models.CharField(max_length=200)
    message = models.TextField()

    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")

    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_inquiries"
    )

    internal_notes = models.TextField(blank=True)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Investor Inquiry"
        verbose_name_plural = "Investor Inquiries"
        indexes = [
            models.Index(fields=["member_state", "status"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["reference_number"]),
            models.Index(fields=["assigned_to", "status"]),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.full_name} ({self.member_state.country_name})"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()
        super().save(*args, **kwargs)

    def _generate_reference_number(self):
        """
        Generate a unique sequential reference number for this year.

        Uses select_for_update() inside a transaction to prevent duplicate
        reference numbers when two requests arrive simultaneously.
        """
        from django.db import transaction
        from django.utils import timezone

        year = timezone.now().year
        prefix = f"INQ-{year}-"

        with transaction.atomic():
            # Lock the most-recent row for this year to serialise number generation
            last_inquiry = (
                InvestorInquiry.objects.select_for_update()
                .filter(reference_number__startswith=prefix)
                .order_by("-reference_number")
                .first()
            )

            if last_inquiry:
                try:
                    last_num = int(last_inquiry.reference_number.split("-")[-1])
                except (ValueError, IndexError):
                    last_num = 0
                new_num = last_num + 1
            else:
                new_num = 1

        return f"{prefix}{new_num:04d}"

    def get_absolute_url(self):
        if self.member_state:
            return reverse(
                "dashboard:country:inquiries:detail",
                kwargs={"member_state_slug": self.member_state.slug, "pk": self.pk},
            )
        else:
            return reverse("dashboard:hq:inquiries:detail", kwargs={"pk": self.pk})


class FDIDataPoint(models.Model):
    """
    Historical FDI and economic data for charts and visualizations.
    Supports time-series analysis and trend displays.
    """

    DATA_TYPES = [
        ("fdi_inflow", "FDI Inflow"),
        ("fdi_outflow", "FDI Outflow"),
        ("fdi_stock", "FDI Stock"),
        ("gdp", "GDP"),
        ("trade_volume", "Trade Volume"),
        ("other", "Other"),
    ]

    VALIDATION_STATUS = [
        ("draft", "Draft"),
        ("under_review", "Under Review"),
        ("published", "Published"),
    ]

    member_state = models.ForeignKey(
        MemberStateIPA, on_delete=models.CASCADE, related_name="fdi_data"
    )

    data_type = models.CharField(max_length=50, choices=DATA_TYPES)

    year = models.IntegerField(validators=[MinValueValidator(1990), MaxValueValidator(2100)])

    value = models.DecimalField(max_digits=15, decimal_places=2, help_text="Value in USD millions")

    value_display = models.CharField(max_length=50, help_text="Formatted display value", blank=True)

    data_source = models.CharField(
        max_length=200, help_text="Data source (e.g., 'UNCTAD', 'World Bank')", blank=True
    )

    notes = models.TextField(blank=True)

    validation_status = models.CharField(max_length=20, choices=VALIDATION_STATUS, default="draft")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["member_state", "data_type", "-year"]
        verbose_name = "FDI Data Point"
        verbose_name_plural = "FDI Data Points"
        unique_together = ["member_state", "data_type", "year"]
        indexes = [
            models.Index(fields=["member_state", "data_type", "year"]),
            models.Index(fields=["validation_status", "-year"]),
            models.Index(fields=["data_type", "-year"]),
        ]

    def __str__(self):
        return f"{self.member_state.country_name} - {self.data_type} ({self.year})"


class IPAStaff(models.Model):
    """
    Key personnel at each IPA (optional).
    For showcasing leadership on country pages.
    """

    POSITION_TYPES = [
        ("executive", "Executive Secretary/Director General"),
        ("director", "Director"),
        ("manager", "Manager"),
        ("officer", "Officer"),
        ("other", "Other"),
    ]

    member_state = models.ForeignKey(MemberStateIPA, on_delete=models.CASCADE, related_name="staff")

    full_name = models.CharField(max_length=200)
    position_title = models.CharField(max_length=200)
    position_type = models.CharField(max_length=50, choices=POSITION_TYPES)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    bio = models.TextField(blank=True)
    photo = models.URLField(max_length=500, blank=True, help_text="Staff photo URL (AWS S3)")

    linkedin_url = models.URLField(blank=True)

    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_on_website = models.BooleanField(default=True, help_text="Display on public country page")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["member_state", "display_order", "full_name"]
        verbose_name = "IPA Staff Member"
        verbose_name_plural = "IPA Staff Members"
        indexes = [
            models.Index(fields=["member_state", "is_active"]),
            models.Index(fields=["position_type", "is_active"]),
            models.Index(fields=["member_state", "show_on_website"]),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.position_title} ({self.member_state.ipa_acronym})"


class IPALeadership(models.Model):
    """
    Head of Investment Promotion Agency.

    Stores official information about the CEO/Director-General/Executive Director
    of each member state's IPA. Required for ECOWAS institutional representation
    compliance.
    """

    TITLE_CHOICES = [
        ("ceo", "Chief Executive Officer (CEO)"),
        ("dg", "Director-General (DG)"),
        ("ed", "Executive Director (ED)"),
        ("md", "Managing Director (MD)"),
        ("commissioner", "Commissioner"),
    ]

    # Link to Member State IPA
    member_state = models.OneToOneField(
        "members.MemberStateIPA",
        on_delete=models.CASCADE,
        related_name="ipa_leadership",
        help_text=_("Member state this leader represents"),
    )

    # Personal Information
    full_name = models.CharField(
        max_length=200, help_text=_("Full official name (e.g., Dr. Hinga Sandi)")
    )

    official_title = models.CharField(
        max_length=20, choices=TITLE_CHOICES, help_text=_("Official designation")
    )

    official_photograph = models.URLField(
        max_length=500,
        blank=True,
        help_text=_("Professional headshot - Min 800x1000px, Max 2MB, neutral background"),
    )

    # Biography
    biography = models.TextField(
        help_text=_("Professional biography (200-500 words covering education, career, vision)"),
        blank=True,
    )

    # Appointment Details
    appointment_date = models.DateField(
        null=True, blank=True, help_text=_("Date of appointment to current position")
    )

    # Contact (if publicly available)
    direct_email = models.EmailField(
        blank=True, help_text=_("Direct email (if publicly available)")
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_verified = models.DateField(
        null=True, blank=True, help_text=_("Date when information was last verified")
    )

    class Meta:
        verbose_name = _("IPA Leader")
        verbose_name_plural = _("IPA Leaders")
        ordering = ["member_state__country_name"]

    def __str__(self):
        return f"{self.full_name} - {self.member_state.ipa_acronym}"

    def get_title_display_full(self):
        """Get full title with name"""
        return f"{self.get_official_title_display()}, {self.member_state.ipa_full_name}"

    @property
    def is_verified(self):
        """Check if information is recently verified (within 1 year)"""
        if not self.last_verified:
            return False
        days_since_verification = (timezone.now().date() - self.last_verified).days
        return days_since_verification < 365


class ECOWASLeadershipPosition(models.Model):
    """
    ECOWAS institutional leadership positions.

    Represents key ECOWAS officials:
    - President of ECOWAS Commission
    - Commissioner for Economic Affairs and Agriculture
    - Chairman of ECOWAS Authority (rotating Head of State)
    """

    POSITION_TYPES = [
        ("commission_president", "President of ECOWAS Commission"),
        ("commissioner_economic", "Commissioner for Economic Affairs and Agriculture"),
        ("authority_chairman", "Chairman of ECOWAS Authority of Heads of State"),
        ("resident_rep", "ECOWAS Resident Representative"),
    ]

    # Position Details
    position_type = models.CharField(
        max_length=50, choices=POSITION_TYPES, unique=True, help_text=_("Type of ECOWAS position")
    )

    position_title = models.CharField(max_length=200, help_text=_("Official title of position"))

    position_description = models.TextField(
        help_text=_("Description of role and responsibilities"), blank=True
    )

    # Current Holder
    current_holder_name = models.CharField(
        max_length=200, help_text=_("Full name of current position holder")
    )

    current_holder_title_prefix = models.CharField(
        max_length=50, help_text=_("Title prefix (H.E., Dr., etc.)"), blank=True
    )

    country_of_origin = models.CharField(
        max_length=100, help_text=_("Country of origin/nationality")
    )

    official_portrait = models.URLField(
        max_length=500,
        blank=True,
        help_text=_("Official portrait - Min 1200x1500px, Max 3MB"),
    )

    # Biography
    biography = models.TextField(help_text=_("Comprehensive biography (500-800 words)"))

    # Education & Career
    education = models.TextField(blank=True, help_text=_("Educational background"))

    career_highlights = models.TextField(
        blank=True, help_text=_("Major career achievements before current position")
    )

    vision_statement = models.TextField(
        blank=True, help_text=_("Vision for regional integration and ECOWAS")
    )

    # Tenure
    start_date = models.DateField(help_text=_("Start date of current tenure"))

    end_date = models.DateField(
        null=True, blank=True, help_text=_("End date of tenure (null if ongoing)")
    )

    # Contact (if applicable)
    office_email = models.EmailField(blank=True)
    office_phone = models.CharField(max_length=50, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True, help_text=_("Is this the current holder of the position?")
    )

    class Meta:
        verbose_name = _("ECOWAS Leadership Position")
        verbose_name_plural = _("ECOWAS Leadership Positions")
        ordering = ["position_type"]

    def __str__(self):
        return f"{self.current_holder_name} - {self.get_position_type_display()}"

    def get_full_name_with_title(self):
        """Get full name with title prefix"""
        if self.current_holder_title_prefix:
            return f"{self.current_holder_title_prefix} {self.current_holder_name}"
        return self.current_holder_name

    @property
    def tenure_duration(self):
        """Calculate tenure duration"""
        if self.end_date:
            delta = self.end_date - self.start_date
        else:
            delta = timezone.now().date() - self.start_date

        years = delta.days // 365
        months = (delta.days % 365) // 30

        if years > 0:
            return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"
        else:
            return f"{months} month{'s' if months != 1 else ''}"
