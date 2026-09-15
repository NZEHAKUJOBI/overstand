"""
Media Management Admin - IPAWAS Platform
=========================================

Django admin configuration for media management.
"""

from django.contrib import admin
from django.utils.html import format_html

from media_app.models import MediaFile, MediaFolder


@admin.register(MediaFolder)
class MediaFolderAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "member_state",
        "folder_type",
        "level",
        "file_count",
        "is_system",
        "is_deleted",
        "created_at",
    ]
    list_filter = ["folder_type", "is_system", "is_deleted", "member_state", "level"]
    search_fields = ["name", "description", "member_state__country_name"]
    readonly_fields = [
        "slug",
        "level",
        "full_path",
        "cloudinary_folder",
        "created_at",
        "updated_at",
        "deleted_at",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("member_state", "name", "slug", "description")}),
        ("Hierarchy", {"fields": ("parent", "level", "folder_type", "is_system")}),
        ("Cloudinary", {"fields": ("cloudinary_folder", "full_path")}),
        ("Metadata", {"fields": ("created_by", "created_at", "updated_at")}),
        (
            "Deletion",
            {"fields": ("is_deleted", "deleted_at", "deleted_by"), "classes": ("collapse",)},
        ),
    )

    def file_count(self, obj):
        return obj.get_file_count()

    file_count.short_description = "Files"


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = [
        "thumbnail_preview",
        "name",
        "file_type",
        "folder",
        "member_state",
        "size_display",
        "uploaded_by",
        "uploaded_at",
    ]
    list_filter = ["file_type", "is_deleted", "is_optimized", "member_state", "uploaded_at"]
    search_fields = ["name", "original_filename", "caption", "alt_text", "cloudinary_public_id"]
    readonly_fields = [
        "thumbnail_display",
        "cloudinary_public_id",
        "cloudinary_resource_type",
        "cloudinary_url",
        "cloudinary_secure_url",
        "thumbnail_url",
        "medium_url",
        "width",
        "height",
        "duration",
        "size_bytes",
        "uploaded_at",
        "updated_at",
        "deleted_at",
    ]

    fieldsets = (
        (
            "File Information",
            {
                "fields": (
                    "thumbnail_display",
                    "name",
                    "original_filename",
                    "file_type",
                    "mime_type",
                    "size_bytes",
                )
            },
        ),
        ("Location", {"fields": ("member_state", "folder")}),
        (
            "Cloudinary Data",
            {
                "fields": (
                    "cloudinary_public_id",
                    "cloudinary_resource_type",
                    "cloudinary_url",
                    "cloudinary_secure_url",
                )
            },
        ),
        (
            "Optimized Versions",
            {"fields": ("thumbnail_url", "medium_url", "is_optimized", "optimization_status")},
        ),
        ("Dimensions", {"fields": ("width", "height", "duration")}),
        ("SEO & Metadata", {"fields": ("alt_text", "caption", "tags", "metadata")}),
        ("Upload Info", {"fields": ("uploaded_by", "uploaded_at", "updated_at")}),
        (
            "Deletion",
            {"fields": ("is_deleted", "deleted_at", "deleted_by"), "classes": ("collapse",)},
        ),
    )

    def thumbnail_preview(self, obj):
        """Small thumbnail for list view"""
        if obj.is_image() and obj.thumbnail_url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.thumbnail_url
            )
        return format_html('<i class="fas {} fa-2x"></i>', obj.get_file_icon())

    thumbnail_preview.short_description = "Preview"

    def thumbnail_display(self, obj):
        """Larger thumbnail for detail view"""
        if obj.is_image() and obj.medium_url:
            return format_html('<img src="{}" style="max-width: 400px;" />', obj.medium_url)
        elif obj.is_video() and obj.thumbnail_url:
            return format_html('<img src="{}" style="max-width: 400px;" />', obj.thumbnail_url)
        return format_html('<i class="fas {} fa-4x"></i>', obj.get_file_icon())

    thumbnail_display.short_description = "Preview"

    def size_display(self, obj):
        return obj.get_display_size()

    size_display.short_description = "Size"
