import re

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from bs4 import BeautifulSoup

from accounts.models import User
from core.models import Sector
from members.models import MemberStateIPA

# ============================================================================
# SHARED CATEGORIZATION
# ============================================================================


class Topic(models.Model):
    """Topics for categorizing all Knowledge Hub content."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, blank=True, help_text="FontAwesome icon class (e.g., 'fa-chart-line')"
    )
    color = models.CharField(max_length=7, default="#10B981", help_text="Hex color for UI display")

    # Stats
    content_count = models.IntegerField(
        default=0, help_text="Cached count of content with this topic"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topics"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Tags for Knowledge Hub content."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    # Stats
    usage_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class NewsArticle(models.Model):
    """
    News articles for platform-wide (HQ) and country-specific content.

    - HQ News: member_state = NULL, visible to all
    - Country News: member_state = specific country, country-specific visibility
    """

    CATEGORY_CHOICES = [
        ("investment_news", "Investment News"),
        ("regional_updates", "Regional Updates"),
        ("success_stories", "Success Stories"),
        ("policy_updates", "Policy Updates"),
        ("blog", "Blog"),
        ("event_coverage", "Event Coverage"),
    ]

    SCOPE_CHOICES = [
        ("hq", "HQ/Platform-wide"),
        ("country", "Country-specific"),
    ]

    # Core Fields
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)

    # Content
    excerpt = models.TextField(
        max_length=500, help_text="Brief summary for previews and meta descriptions"
    )

    # Legacy content field (kept for backwards compatibility)
    content = models.TextField(help_text="Full article content (HTML supported)", blank=True)

    # NEW: Structured content blocks
    content_blocks = models.JSONField(
        default=list, help_text="Structured content: [{type: 'paragraph', content: '...'}, ...]"
    )

    # Media
    featured_media = models.ForeignKey(
        "media_app.MediaFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="featured_in_articles",
        help_text="Main hero image",
    )

    # NEW: Supporting images for gallery/carousel
    supporting_images = models.ManyToManyField(
        "media_app.MediaFile",
        blank=True,
        related_name="news_article_gallery",
        help_text="Additional images shown in article carousel",
    )

    # Metadata
    author = models.CharField(max_length=200)
    author_title = models.CharField(max_length=200, blank=True)
    publication_date = models.DateTimeField(db_index=True)

    # Reading stats
    reading_time = models.IntegerField(default=5, help_text="Estimated reading time in minutes")
    view_count = models.IntegerField(default=0)

    # NEW: Ownership and Scope
    member_state = models.ForeignKey(
        MemberStateIPA,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="news_articles",
        help_text="If NULL, this is HQ/platform-wide news",
    )

    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default="hq",
        db_index=True,
        help_text="Determines visibility scope",
    )

    # Relationships
    topics = models.ManyToManyField("Topic", blank=True, related_name="news_articles")
    tags = models.ManyToManyField("Tag", blank=True, related_name="news_articles")
    related_countries = models.ManyToManyField(
        MemberStateIPA, blank=True, related_name="related_news_articles"
    )
    related_sectors = models.ManyToManyField(Sector, blank=True, related_name="news_articles")

    # Search
    search_vector = SearchVectorField(null=True, editable=False)

    # Status
    published = models.BooleanField(default=True, db_index=True)
    featured = models.BooleanField(default=False, help_text="Show as featured news")

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="news_articles_created"
    )

    class Meta:
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"
        ordering = ["-publication_date", "-featured"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category", "published"]),
            models.Index(fields=["-publication_date"]),
            models.Index(fields=["featured", "-publication_date"]),
            models.Index(fields=["member_state", "published"]),
            models.Index(fields=["scope", "published"]),
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self):
        scope_str = f"[{self.member_state.country_name}]" if self.member_state else "[HQ]"
        return f"{scope_str} {self.title}"

    def save(self, *args, **kwargs):
        """Auto-generate slug and set scope based on member_state"""

        if not self.slug:
            # Remove special characters
            clean_title = self.title.replace("$", "").replace("€", "").replace("£", "")
            clean_title = re.sub(r"[^\w\s-]", "", clean_title)

            # Generate slug
            base_slug = slugify(clean_title)[:200]
            slug = base_slug
            counter = 1

            while NewsArticle.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        # Auto-set scope based on member_state
        if self.member_state:
            self.scope = "country"
        else:
            self.scope = "hq"

        # Auto-calculate reading time if content_blocks exist
        if self.content_blocks and not kwargs.get("skip_reading_time"):
            self.reading_time = self.calculate_reading_time()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Get URL for this news article"""
        return reverse("knowledge_hub:news_detail", kwargs={"slug": self.slug})

    def is_hq_news(self):
        """Check if this is platform-wide HQ news"""
        return self.member_state is None

    def is_country_news(self):
        """Check if this is country-specific news"""
        return self.member_state is not None

    def get_featured_image_url(self):
        """Get featured image URL with fallback"""
        if self.featured_media:
            return self.featured_media.get_thumbnail()
        return None

    def get_featured_image_medium(self):
        """Get medium-sized featured image"""
        if self.featured_media:
            return self.featured_media.medium_url or self.featured_media.cloudinary_secure_url
        return None

    def get_supporting_images_list(self):
        """Get list of supporting images"""
        return self.supporting_images.filter(is_deleted=False).order_by("id")

    def calculate_reading_time(self):
        """
        Calculate estimated reading time based on content.
        Average reading speed: 200 words per minute
        """
        word_count = 0

        if self.content_blocks:
            for block in self.content_blocks:
                if block.get("type") in ["paragraph", "heading"]:
                    content = block.get("content", "")
                    # Strip HTML tags and count words
                    import re

                    text = re.sub("<[^<]+?>", "", content)
                    word_count += len(text.split())
        elif self.content:
            # Fallback to legacy content field
            import re

            text = re.sub("<[^<]+?>", "", self.content)
            word_count = len(text.split())

        # Calculate minutes, minimum 1 minute
        minutes = max(1, round(word_count / 200))
        return minutes

    def get_related_news(self, limit=3):
        """
        Get related news articles based on:
        - Same category
        - Same tags
        - Same scope
        """
        related = NewsArticle.objects.filter(
            published=True, publication_date__lte=timezone.now()
        ).exclude(pk=self.pk)

        # Prioritize same scope
        if self.scope:
            related = related.filter(scope=self.scope)

        # Same category
        related = related.filter(category=self.category)

        # Order by publication date
        return related.order_by("-publication_date")[:limit]

    def increment_view_count(self):
        """Increment view counter"""
        self.view_count += 1
        self.save(update_fields=["view_count"])

    @classmethod
    def get_published_news(cls):
        """Get all published news"""
        return cls.objects.filter(published=True, publication_date__lte=timezone.now())

    @classmethod
    def get_hq_news(cls):
        """Get platform-wide HQ news"""
        return cls.get_published_news().filter(member_state__isnull=True)

    @classmethod
    def get_country_news(cls, member_state):
        """Get country-specific news"""
        return cls.get_published_news().filter(member_state=member_state)

    @classmethod
    def get_featured_news(cls, limit=3):
        """Get featured news articles"""
        return cls.get_published_news().filter(featured=True).order_by("-publication_date")[:limit]


# Helper function for content block parsing
def parse_html_to_blocks(html_content):
    """
    Parse HTML content into structured blocks.

    Returns list of blocks:
    [
        {'type': 'paragraph', 'content': '...'},
        {'type': 'heading', 'level': 2, 'content': '...'},
        {'type': 'image', 'media_id': 123, ...},
    ]
    """

    soup = BeautifulSoup(html_content, "html.parser")
    blocks = []

    for element in soup.children:
        if element.name == "p":
            blocks.append({"type": "paragraph", "content": str(element)})
        elif element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            blocks.append(
                {"type": "heading", "level": int(element.name[1]), "content": element.get_text()}
            )
        elif element.name == "figure":
            img = element.find("img")
            caption = element.find("figcaption")
            if img:
                blocks.append(
                    {
                        "type": "image",
                        "media_id": img.get("data-media-id"),
                        "image_url": img.get("src"),
                        "alt_text": img.get("alt", ""),
                        "caption": caption.get_text() if caption else "",
                    }
                )
        elif element.name in ["ul", "ol"]:
            blocks.append(
                {
                    "type": "list",
                    "list_type": "unordered" if element.name == "ul" else "ordered",
                    "items": [li.get_text() for li in element.find_all("li")],
                }
            )

    return blocks


# ============================================================================
# PRESS RELEASES
# ============================================================================


class PressRelease(models.Model):
    """Press releases for Media Center."""

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, db_index=True)

    # Content
    summary = models.TextField(max_length=500)
    content = models.TextField(help_text="Full press release content")

    # Metadata
    release_date = models.DateField(db_index=True)
    location = models.CharField(max_length=200, blank=True, help_text="e.g., 'Abuja, Nigeria'")

    # Contact Information
    contact_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    # Attachments (from MediaFile)
    pdf_file = models.ForeignKey(
        "media_app.MediaFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="press_releases",
        help_text="PDF version from Media Library",
    )

    # Media assets (photos/videos from press event)
    media_assets = models.ManyToManyField(
        "media_app.MediaFile",
        blank=True,
        related_name="related_press_releases",
        help_text="Photos/videos from the press event",
    )

    # Related
    topics = models.ManyToManyField(Topic, blank=True, related_name="press_releases")
    tags = models.ManyToManyField(Tag, blank=True, related_name="press_releases")

    # Status
    published = models.BooleanField(default=True, db_index=True)

    # Approval workflow
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending_review", "Pending HQ Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", db_index=True)
    member_state = models.ForeignKey(
        "members.MemberStateIPA",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="press_releases",
    )
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_press_releases",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Stats
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="press_releases_created"
    )

    class Meta:
        verbose_name = "Press Release"
        verbose_name_plural = "Press Releases"
        ordering = ["-release_date"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["-release_date", "published"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.release_date}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:280]
            slug = base_slug
            counter = 1
            while PressRelease.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        self.published = (self.status == "approved")
        super().save(*args, **kwargs)


class MediaCenterSubmission(models.Model):
    """
    IPA-submitted media (photos/videos) pending HQ approval for the public Media Center.
    """
    STATUS_CHOICES = [
        ("pending", "Pending HQ Review"),
        ("approved", "Approved - Live"),
        ("rejected", "Rejected"),
    ]
    TYPE_CHOICES = [
        ("photo", "Photo"),
        ("video", "Video"),
    ]

    media_file = models.OneToOneField(
        "media_app.MediaFile",
        on_delete=models.CASCADE,
        related_name="media_center_submission",
    )
    member_state = models.ForeignKey(
        "members.MemberStateIPA",
        on_delete=models.CASCADE,
        related_name="media_center_submissions",
    )
    submission_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    caption = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="media_submissions",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    rejection_reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_media_submissions",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Media Center Submission"
        verbose_name_plural = "Media Center Submissions"

    def __str__(self):
        return f"{self.member_state.country_name} - {self.media_file.name} ({self.status})"


# ============================================================================
# MEDIA CENTER CATEGORIES
# ============================================================================


class MediaCategory(models.Model):
    """
    Categories for organizing public-facing media from MediaFile.
    Links existing MediaFiles to Media Center display categories.
    """

    CATEGORY_TYPES = [
        ("press_event", "Press Event"),
        ("leadership", "Leadership Photos"),
        ("facilities", "Facilities"),
        ("projects", "Project Photos"),
        ("meetings", "Meetings & Conferences"),
        ("branding", "Branding & Logos"),
        ("promotional", "Promotional Videos"),
        ("documentary", "Documentary"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category_type = models.CharField(max_length=50, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)

    # Associated MediaFiles
    media_files = models.ManyToManyField(
        "media_app.MediaFile",
        related_name="public_categories",
        help_text="Files from Media Library to display publicly",
    )

    # Display order
    display_order = models.IntegerField(default=0)

    # Status
    is_public = models.BooleanField(default=True, help_text="Show in public Media Center")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Media Category"
        verbose_name_plural = "Media Categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_photos(self):
        """Get all photos in this category."""
        return self.media_files.filter(file_type="image", is_deleted=False).order_by("-uploaded_at")

    def get_videos(self):
        """Get all videos in this category."""
        return self.media_files.filter(file_type="video", is_deleted=False).order_by("-uploaded_at")


# ============================================================================
# RESOURCES
# ============================================================================


class Resource(models.Model):
    """Downloadable resources for Resources Library."""

    RESOURCE_TYPES = [
        ("investment_guide", "Investment Guide"),
        ("toolkit", "Toolkit"),
        ("template", "Template"),
        ("legal_document", "Legal Document"),
        ("data_tool", "Data Tool"),
        ("checklist", "Checklist"),
        ("handbook", "Handbook"),
        ("form", "Form"),
    ]

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, db_index=True)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES, db_index=True)

    # Content
    description = models.TextField()

    # File (from MediaFile)
    resource_file = models.ForeignKey(
        "media_app.MediaFile",
        on_delete=models.CASCADE,
        related_name="resources",
        help_text="Resource file from Media Library",
    )

    # Metadata
    version = models.CharField(max_length=50, blank=True, help_text="e.g., 'v2.0', '2024 Edition'")
    last_updated = models.DateField(db_index=True)

    # Related
    topics = models.ManyToManyField(Topic, blank=True, related_name="resources")
    related_sectors = models.ManyToManyField(Sector, blank=True, related_name="resources")
    related_countries = models.ManyToManyField(MemberStateIPA, blank=True, related_name="resources")
    tags = models.ManyToManyField(Tag, blank=True, related_name="resources")

    # Status
    published = models.BooleanField(default=True, db_index=True)
    featured = models.BooleanField(default=False)

    # Stats (delegated from MediaFile but cached)
    download_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="resources_created"
    )

    class Meta:
        verbose_name = "Resource"
        verbose_name_plural = "Resources"
        ordering = ["-last_updated", "-featured"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["resource_type", "published"]),
            models.Index(fields=["-last_updated"]),
            models.Index(fields=["featured", "-last_updated"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_file_info(self):
        """Get file information from associated MediaFile."""
        if self.resource_file:
            return {
                "format": self.resource_file.mime_type.split("/")[-1].upper(),
                "size": self.resource_file.get_display_size(),
                "url": self.resource_file.get_download_url(),
            }
        return None

    def increment_download(self):
        """Increment download counter."""
        self.download_count += 1
        self.save(update_fields=["download_count"])
        # Also increment on the MediaFile
        if self.resource_file:
            self.resource_file.increment_download()


# ============================================================================
# MEDIA KIT ITEMS
# ============================================================================


class MediaKitItem(models.Model):
    """
    Items available in the downloadable Media Kit.
    References existing MediaFiles organized for media/press use.
    """

    ITEM_TYPES = [
        ("logo_pack", "Logo Package"),
        ("brand_guide", "Brand Guidelines"),
        ("fact_sheet", "Fact Sheet"),
        ("leadership_photos", "Leadership Photos"),
        ("facility_photos", "Facility Photos"),
        ("infographic", "Infographic"),
        ("presentation", "Presentation Template"),
    ]

    name = models.CharField(max_length=200)
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES)
    description = models.TextField(blank=True)

    # Associated file(s)
    primary_file = models.ForeignKey(
        "media_app.MediaFile",
        on_delete=models.CASCADE,
        related_name="mediakit_primary",
        help_text="Main file for this media kit item",
    )

    additional_files = models.ManyToManyField(
        "media_app.MediaFile",
        blank=True,
        related_name="mediakit_additional",
        help_text="Additional files in this package",
    )

    # Display
    display_order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    # Status
    is_active = models.BooleanField(default=True)

    # Stats
    download_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Media Kit Item"
        verbose_name_plural = "Media Kit Items"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_item_type_display()})"

    def get_all_files(self):
        """Get primary file + additional files."""
        files = [self.primary_file]
        files.extend(self.additional_files.all())
        return files

    def get_total_size(self):
        """Calculate total size of all files."""
        total = self.primary_file.size_bytes
        total += sum(f.size_bytes for f in self.additional_files.all())

        # Convert to readable format
        size = total
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
