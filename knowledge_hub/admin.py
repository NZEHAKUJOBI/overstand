"""
Knowledge Hub Admin Configuration
==================================

Admin interface for managing Knowledge Hub content integrated with MediaFile system.
"""

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import MediaCategory, MediaKitItem, NewsArticle, PressRelease, Resource, Tag, Topic

# ============================================================================
# INLINE ADMINS
# ============================================================================


class MediaKitAdditionalFilesInline(admin.TabularInline):
    model = MediaKitItem.additional_files.through
    extra = 1
    verbose_name = "Additional File"
    verbose_name_plural = "Additional Files"


# ============================================================================
# MAIN ADMINS
# ============================================================================


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "icon", "color", "content_count", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["content_count", "created_at", "updated_at"]

    fieldsets = [
        ("Basic Information", {"fields": ("name", "slug", "description")}),
        ("Display", {"fields": ("icon", "color")}),
        ("Statistics", {"fields": ("content_count",), "classes": ["collapse"]}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ["collapse"]}),
    ]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "usage_count", "created_at"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["usage_count", "created_at"]


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "author",
        "publication_date",
        "featured",
        "published",
        "view_count",
    ]
    list_filter = ["category", "published", "featured", "publication_date", "created_at"]
    search_fields = ["title", "excerpt", "content", "author"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["view_count", "created_at", "updated_at", "created_by"]
    date_hierarchy = "publication_date"

    filter_horizontal = ["topics", "tags", "related_countries", "related_sectors"]

    fieldsets = [
        ("Basic Information", {"fields": ("title", "slug", "category", "featured")}),
        ("Content", {"fields": ("excerpt", "content")}),
        (
            "Media",
            {"fields": ("featured_media",), "description": "Select image from Media Library"},
        ),
        ("Metadata", {"fields": ("author", "author_title", "publication_date", "reading_time")}),
        (
            "Relationships",
            {
                "fields": ("topics", "tags", "related_countries", "related_sectors"),
                "classes": ["collapse"],
            },
        ),
        ("Publishing", {"fields": ("published",)}),
        (
            "Statistics",
            {
                "fields": ("view_count", "created_at", "updated_at", "created_by"),
                "classes": ["collapse"],
            },
        ),
    ]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("featured_media", "created_by")
            .prefetch_related("topics", "tags")
        )


@admin.register(PressRelease)
class PressReleaseAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "release_date",
        "location",
        "published",
        "view_count",
        "download_count",
    ]
    list_filter = ["published", "release_date"]
    search_fields = ["title", "content", "location"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["view_count", "download_count", "created_at", "updated_at", "created_by"]
    date_hierarchy = "release_date"

    filter_horizontal = ["topics", "tags", "media_assets"]

    fieldsets = [
        ("Basic Information", {"fields": ("title", "slug", "release_date", "location")}),
        ("Content", {"fields": ("summary", "content")}),
        (
            "Contact Information",
            {"fields": ("contact_name", "contact_email", "contact_phone"), "classes": ["collapse"]},
        ),
        (
            "Files & Media",
            {
                "fields": ("pdf_file", "media_assets"),
                "description": "Select files from Media Library",
            },
        ),
        ("Categorization", {"fields": ("topics", "tags"), "classes": ["collapse"]}),
        ("Publishing", {"fields": ("published",)}),
        (
            "Statistics",
            {
                "fields": (
                    "view_count",
                    "download_count",
                    "created_at",
                    "updated_at",
                    "created_by",
                ),
                "classes": ["collapse"],
            },
        ),
    ]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MediaCategory)
class MediaCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category_type",
        "display_order",
        "is_public",
        "file_count",
        "created_at",
    ]
    list_filter = ["category_type", "is_public"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    filter_horizontal = ["media_files"]

    fieldsets = [
        ("Basic Information", {"fields": ("name", "slug", "category_type", "description")}),
        (
            "Media Files",
            {
                "fields": ("media_files",),
                "description": "Select files from Media Library to display in this category",
            },
        ),
        ("Display Settings", {"fields": ("display_order", "is_public")}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ["collapse"]}),
    ]

    def file_count(self, obj):
        return obj.media_files.filter(is_deleted=False).count()

    file_count.short_description = "Files"


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "resource_type",
        "version",
        "last_updated",
        "featured",
        "published",
        "download_count",
    ]
    list_filter = ["resource_type", "published", "featured", "last_updated"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["download_count", "view_count", "created_at", "updated_at", "created_by"]
    date_hierarchy = "last_updated"

    filter_horizontal = ["topics", "related_sectors", "related_countries", "tags"]

    fieldsets = [
        ("Basic Information", {"fields": ("title", "slug", "resource_type", "featured")}),
        ("Content", {"fields": ("description",)}),
        (
            "File",
            {
                "fields": ("resource_file", "version", "last_updated"),
                "description": "Select file from Media Library",
            },
        ),
        (
            "Relationships",
            {
                "fields": ("topics", "related_sectors", "related_countries", "tags"),
                "classes": ["collapse"],
            },
        ),
        ("Publishing", {"fields": ("published",)}),
        (
            "Statistics",
            {
                "fields": (
                    "download_count",
                    "view_count",
                    "created_at",
                    "updated_at",
                    "created_by",
                ),
                "classes": ["collapse"],
            },
        ),
    ]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("resource_file")


@admin.register(MediaKitItem)
class MediaKitItemAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "item_type",
        "display_order",
        "is_featured",
        "is_active",
        "download_count",
        "total_size",
    ]
    list_filter = ["item_type", "is_featured", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["download_count", "created_at", "updated_at", "total_size"]

    inlines = [MediaKitAdditionalFilesInline]

    fieldsets = [
        ("Basic Information", {"fields": ("name", "item_type", "description")}),
        (
            "Files",
            {"fields": ("primary_file",), "description": "Additional files can be added below"},
        ),
        ("Display Settings", {"fields": ("display_order", "is_featured", "is_active")}),
        (
            "Statistics",
            {
                "fields": ("download_count", "total_size", "created_at", "updated_at"),
                "classes": ["collapse"],
            },
        ),
    ]

    def total_size(self, obj):
        if obj.pk:
            return obj.get_total_size()
        return "-"

    total_size.short_description = "Total Size"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("primary_file")


# ============================================================================
# CUSTOM ADMIN ACTIONS
# ============================================================================


@admin.action(description="Publish selected items")
def make_published(modeladmin, request, queryset):
    queryset.update(published=True)


@admin.action(description="Unpublish selected items")
def make_unpublished(modeladmin, request, queryset):
    queryset.update(published=False)


@admin.action(description="Mark as featured")
def make_featured(modeladmin, request, queryset):
    queryset.update(featured=True)


@admin.action(description="Unmark as featured")
def make_unfeatured(modeladmin, request, queryset):
    queryset.update(featured=False)


# Add actions to relevant admins
NewsArticleAdmin.actions = [make_published, make_unpublished, make_featured, make_unfeatured]
PressReleaseAdmin.actions = [make_published, make_unpublished]
ResourceAdmin.actions = [make_published, make_unpublished, make_featured, make_unfeatured]
