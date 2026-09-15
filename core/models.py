"""
IPAWAS Core App Models
======================

This module contains core/shared models used across the entire platform:
- User authentication and authorization
- IPAUser: Extended user model for IPA staff
- Sector: Investment sectors (shared across opportunities, member states, etc.)
- Partner: Development partners and organizations
- Publication: Knowledge hub content
- Event: Regional events and conferences
- EventRegistration: Event participant management

These are foundational models that other apps depend on.
"""

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import User


class Sector(models.Model):
    """
    Investment sectors used across the platform.
    Shared by opportunities, member states, and success stories.

    Examples: Agriculture, Energy, ICT, Manufacturing, etc.
    """

    name = models.CharField(
        max_length=100, unique=True, help_text="Sector name (e.g., 'Agriculture & Agribusiness')"
    )

    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly version")

    description = models.TextField(help_text="Sector overview and importance", blank=True)

    # Visual representation
    icon_class = models.CharField(
        max_length=100, help_text="CSS icon class (e.g., 'fas fa-tractor')", blank=True
    )

    icon_image = models.URLField(
        max_length=500, blank=True, help_text="Custom icon image URL (AWS S3)"
    )

    color = models.CharField(
        max_length=20, default="#1B7A4C", help_text="Brand color for this sector (hex code)"
    )

    # Detailed content
    market_overview = models.TextField(blank=True, help_text="Market size and opportunity")

    regional_advantages = models.TextField(blank=True, help_text="Why West Africa for this sector")

    investment_requirements = models.TextField(
        blank=True, help_text="Typical investment requirements"
    )

    # Media
    hero_image = models.URLField(max_length=500, blank=True, help_text="Hero banner URL (AWS S3)")

    # Display settings
    featured = models.BooleanField(default=False, help_text="Featured on homepage?")

    display_order = models.IntegerField(default=0, help_text="Display order (lower first)")

    is_active = models.BooleanField(default=True, help_text="Is this sector active?")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectors"
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "featured"]),
            models.Index(fields=["display_order"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("sector_detail", kwargs={"slug": self.slug})


class Partner(models.Model):
    """
    Development partners, international organizations, and strategic partners.
    Examples: WAIPA, UNCTAD, UNIDO, World Bank, AfDB, etc.
    """

    PARTNER_TYPES = [
        ("development", "Development Partner"),
        ("international_org", "International Organization"),
        ("private_sector", "Private Sector"),
        ("research", "Research Institution"),
        ("network", "Investment Network"),
        ("government", "Government Agency"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=200, unique=True, help_text="Partner organization name")

    slug = models.SlugField(max_length=200, unique=True)

    partner_type = models.CharField(
        max_length=50, choices=PARTNER_TYPES, help_text="Type of partner organization"
    )

    acronym = models.CharField(
        max_length=20, blank=True, help_text="Acronym (e.g., 'WAIPA', 'UNCTAD')"
    )

    description = models.TextField(help_text="Partner description and collaboration", blank=True)

    website = models.URLField(blank=True, help_text="Partner's official website")

    logo = models.URLField(max_length=500, blank=True, help_text="Partner logo URL (AWS S3)")

    # Partnership details
    partnership_start_date = models.DateField(
        null=True, blank=True, help_text="When partnership began"
    )

    partnership_areas = models.TextField(blank=True, help_text="Areas of collaboration")

    # Contact
    contact_person = models.CharField(
        max_length=200, blank=True, help_text="Primary contact person"
    )

    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    # Display
    featured = models.BooleanField(default=False, help_text="Featured partner (show on homepage)")

    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Partner"
        verbose_name_plural = "Partners"
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["partner_type", "is_active"]),
            models.Index(fields=["featured", "display_order"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.acronym})" if self.acronym else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Publication(models.Model):
    """
    Publications, reports, and documents in the Knowledge Hub.
    """

    PUBLICATION_TYPES = [
        ("annual_report", "Annual Report"),
        ("investment_report", "Investment Report"),
        ("policy_brief", "Policy Brief"),
        ("research_paper", "Research Paper"),
        ("guide", "Investment Guide"),
        ("newsletter", "Newsletter"),
        ("brochure", "Brochure"),
        ("case_study", "Case Study"),
        ("presentation", "Presentation"),
        ("infographic", "Infographic"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=300, help_text="Publication title")

    slug = models.SlugField(max_length=300, unique=True)

    publication_type = models.CharField(max_length=50, choices=PUBLICATION_TYPES)

    description = models.TextField(help_text="Abstract or summary", blank=True)

    # File
    file = models.URLField(max_length=500, help_text="PDF or document URL (AWS S3)")

    file_size = models.CharField(max_length=20, blank=True, help_text="File size (e.g., '2.5 MB')")

    # Metadata
    author = models.CharField(max_length=200, help_text="Author or organization", blank=True)

    publication_date = models.DateField(help_text="Publication date")

    year = models.IntegerField(help_text="Publication year")

    language = models.CharField(
        max_length=10,
        choices=[
            ("en", "English"),
            ("fr", "French"),
            ("pt", "Portuguese"),
        ],
        default="en",
    )

    # Related data
    related_sectors = models.ManyToManyField(
        Sector, blank=True, related_name="publications", help_text="Related sectors"
    )

    related_countries = models.ManyToManyField(
        "members.MemberStateIPA",
        blank=True,
        related_name="publications",
        help_text="Related countries",
    )

    # Visual
    cover_image = models.URLField(
        max_length=500, blank=True, help_text="Cover image or thumbnail URL (AWS S3)"
    )

    # Status
    published = models.BooleanField(default=True, help_text="Is publication published?")

    featured = models.BooleanField(default=False, help_text="Featured publication?")

    # Stats
    download_count = models.IntegerField(default=0, help_text="Number of downloads")

    view_count = models.IntegerField(default=0, help_text="Number of views")

    topics = models.ManyToManyField("knowledge_hub.Topic", blank=True, related_name="publications")

    tags = models.ManyToManyField("knowledge_hub.Tag", blank=True, related_name="publications")

    # Optional: Link to MediaFile for cover images stored in media library
    cover_media = models.ForeignKey(
        "media_app.MediaFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publication_covers",
        help_text="Cover image from Media Library (overrides cover_image URL)",
    )
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="publications_created"
    )

    class Meta:
        verbose_name = "Publication"
        verbose_name_plural = "Publications"
        ordering = ["-publication_date", "-featured"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["publication_type", "published"]),
            models.Index(fields=["-publication_date"]),
            models.Index(fields=["year", "published"]),
            models.Index(fields=["featured", "-publication_date"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.year})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.year and self.publication_date:
            self.year = self.publication_date.year
        super().save(*args, **kwargs)


class Event(models.Model):
    """
    Regional events, conferences, forums, and workshops.
    """

    EVENT_TYPES = [
        ("forum", "Investment Forum"),
        ("conference", "Conference"),
        ("workshop", "Workshop"),
        ("training", "Training Program"),
        ("webinar", "Webinar"),
        ("mission", "Investment Mission"),
        ("roadshow", "Roadshow"),
        ("meeting", "Meeting"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    title = models.CharField(max_length=300, help_text="Event title")

    slug = models.SlugField(max_length=300, unique=True)

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)

    description = models.TextField(help_text="Event description")

    # Date and time
    start_date = models.DateField(help_text="Event start date")
    end_date = models.DateField(help_text="Event end date")
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    timezone = models.CharField(max_length=50, default="GMT", help_text="Event timezone")

    # Location
    is_virtual = models.BooleanField(default=False, help_text="Is this a virtual event?")

    venue = models.CharField(max_length=300, blank=True, help_text="Venue name")

    city = models.CharField(max_length=100, blank=True, help_text="City")

    host_country = models.ForeignKey(
        "members.MemberStateIPA",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hosted_events",
    )

    venue_address = models.TextField(blank=True)

    virtual_link = models.URLField(blank=True, help_text="Virtual meeting link")

    # Event details
    agenda = models.TextField(blank=True, help_text="Event agenda")

    target_audience = models.JSONField(default=list, blank=True, help_text="Target audience groups")

    learning_objectives = models.TextField(blank=True, help_text="What participants will learn")

    speakers = models.TextField(blank=True, help_text="Speakers and facilitators")

    # Registration
    registration_required = models.BooleanField(default=True, help_text="Is registration required?")

    registration_deadline = models.DateField(
        null=True, blank=True, help_text="Registration deadline"
    )

    registration_link = models.URLField(blank=True, help_text="External registration link")

    max_participants = models.IntegerField(
        null=True, blank=True, help_text="Maximum number of participants"
    )

    registration_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Registration fee in USD (0 for free)",
    )

    # Media
    banner_image = models.URLField(
        max_length=500, blank=True, help_text="Event banner URL (AWS S3)"
    )

    # Related data
    related_sectors = models.ManyToManyField(Sector, blank=True, related_name="events")

    organizing_partners = models.ManyToManyField(
        Partner,
        blank=True,
        related_name="organized_events",
        help_text="Partners organizing the event",
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")

    featured = models.BooleanField(default=False, help_text="Featured event?")

    # Post-event
    event_report = models.URLField(
        max_length=500, blank=True, help_text="Post-event report URL (AWS S3)"
    )

    attendance_count = models.IntegerField(null=True, blank=True, help_text="Number of attendees")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="events_created"
    )

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ["-start_date", "-featured"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["event_type", "status"]),
            models.Index(fields=["-start_date", "status"]),
            models.Index(fields=["host_country", "status"]),
            models.Index(fields=["featured", "-start_date"]),
            models.Index(fields=["registration_required", "status"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.start_date.year})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-update status based on dates
        today = timezone.now().date()
        if self.status != "cancelled":
            if self.end_date < today:
                self.status = "completed"
            elif self.start_date <= today <= self.end_date:
                self.status = "ongoing"
            else:
                self.status = "upcoming"

        super().save(*args, **kwargs)

    @property
    def is_past(self):
        return self.end_date < timezone.now().date()

    @property
    def is_ongoing(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    @property
    def registration_open(self):
        if not self.registration_required:
            return False
        if self.registration_deadline:
            return timezone.now().date() <= self.registration_deadline
        return self.start_date >= timezone.now().date()


class EventRegistration(models.Model):
    """
    Event participant registrations.
    """

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("waived", "Waived"),
        ("refunded", "Refunded"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")

    # Participant info
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)

    organization = models.CharField(max_length=200, blank=True, help_text="Organization/Company")

    job_title = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Registration details
    participant_type = models.CharField(
        max_length=50,
        choices=[
            ("investor", "Investor"),
            ("ipa_staff", "IPA Staff"),
            ("government", "Government Official"),
            ("service_provider", "Service Provider"),
            ("researcher", "Researcher/Academic"),
            ("media", "Media"),
            ("other", "Other"),
        ],
        blank=True,
    )

    dietary_requirements = models.TextField(blank=True)
    special_needs = models.TextField(blank=True)

    # Payment (if applicable)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="pending")

    payment_reference = models.CharField(
        max_length=100, blank=True, help_text="Payment transaction reference"
    )

    # Attendance
    attended = models.BooleanField(default=False, help_text="Did participant attend?")

    certificate_issued = models.BooleanField(default=False, help_text="Was certificate issued?")

    # Metadata
    registration_number = models.CharField(
        max_length=50, unique=True, help_text="Unique registration number"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Event Registration"
        verbose_name_plural = "Event Registrations"
        ordering = ["-created_at"]
        unique_together = ["event", "email"]
        indexes = [
            models.Index(fields=["event", "payment_status"]),
            models.Index(fields=["registration_number"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["event", "attended"]),
        ]

    def __str__(self):
        return f"{self.registration_number} - {self.full_name} ({self.event.title})"

    def save(self, *args, **kwargs):
        if not self.registration_number:
            self.registration_number = self._generate_registration_number()
        super().save(*args, **kwargs)

    def _generate_registration_number(self):
        """Generate unique registration number"""
        year = timezone.now().year
        # Get last registration for this event
        last_reg = (
            EventRegistration.objects.filter(
                event=self.event, registration_number__startswith=f"EVT-{self.event.id}-{year}-"
            )
            .order_by("-registration_number")
            .first()
        )

        if last_reg:
            last_num = int(last_reg.registration_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"EVT-{self.event.id}-{year}-{new_num:04d}"


class NewsletterSubscriber(models.Model):
    """Newsletter subscriber model."""

    email = models.EmailField(unique=True, db_index=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-subscribed_at"]
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"

    def __str__(self):
        return self.email
