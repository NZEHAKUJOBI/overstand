"""
Media Management Models - IPAWAS Platform
==========================================

Fat models with business logic for robust media file management.
Supports hierarchical folder structure with 4-level depth limit.
Cloudinary integration for storage and optimization.
"""

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import User
from members.models import MemberStateIPA


class MediaFolder(models.Model):
    """
    Hierarchical folder structure for organizing media files.

    Analogy: Like a filing cabinet where each member state has their own
    locked drawer, with labeled dividers inside.

    Hierarchy:
        Level 0: Root folder (auto-created per member state)
        Level 1: System folders (Documents, Images, Videos, Others)
        Level 2-3: Custom admin-created folders
        Level 4: Files only (no more nesting)
    """

    FOLDER_TYPES = [
        ("root", "Root Folder"),
        ("documents", "Documents"),
        ("images", "Images"),
        ("videos", "Videos"),
        ("others", "Others"),
        ("custom", "Custom Folder"),
    ]

    # Core Fields
    member_state = models.ForeignKey(
        MemberStateIPA, on_delete=models.CASCADE, related_name="media_folders", db_index=True
    )

    name = models.CharField(
        max_length=100, help_text="Folder name (e.g., 'Annual Reports', 'Project Photos')"
    )

    slug = models.SlugField(max_length=120)

    # Hierarchy Management
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subfolders",
        db_index=True,
    )

    level = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text="Depth in hierarchy (0=root, 1=system, 2-3=custom)",
    )

    folder_type = models.CharField(max_length=20, choices=FOLDER_TYPES, default="custom")

    is_system = models.BooleanField(
        default=False, help_text="System folders cannot be deleted or renamed"
    )

    # Cloudinary Integration
    cloudinary_folder = models.CharField(
        max_length=500,
        help_text="Full path in Cloudinary (e.g., 'ipawas/nigeria/documents')",
        blank=True,
    )

    full_path = models.CharField(
        max_length=500, help_text="Computed full path for display", blank=True
    )

    # Metadata
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_folders"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft Delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deleted_folders"
    )

    class Meta:
        ordering = ["member_state", "level", "folder_type", "name"]
        verbose_name = "Media Folder"
        verbose_name_plural = "Media Folders"
        unique_together = [["member_state", "parent", "slug"]]
        indexes = [
            models.Index(fields=["member_state", "parent"]),
            models.Index(fields=["member_state", "is_system"]),
            models.Index(fields=["member_state", "is_deleted"]),
            models.Index(fields=["level", "folder_type"]),
            models.Index(fields=["cloudinary_folder"]),
        ]

    def __str__(self):
        return f"{self.member_state.country_name} - {self.get_display_path()}"

    def save(self, *args, **kwargs):
        """Auto-compute slug, level, and paths"""
        if not self.slug:
            self.slug = slugify(self.name)

        # Compute level from parent
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0

        # Compute paths
        self.full_path = self.compute_full_path()
        self.cloudinary_folder = self.compute_cloudinary_path()

        super().save(*args, **kwargs)

    def clean(self):
        """Validate folder creation rules"""
        # Level validation
        if self.parent and self.parent.level >= 3:
            raise ValidationError("Cannot create folders beyond level 3. Maximum depth reached.")

        # System folder protection
        if self.pk and self.is_system:
            old_folder = MediaFolder.objects.get(pk=self.pk)
            if old_folder.name != self.name:
                raise ValidationError("System folders cannot be renamed.")

        # Parent must belong to same member state
        if self.parent and self.parent.member_state != self.member_state:
            raise ValidationError("Parent folder must belong to the same member state.")

        # Circular reference check
        if self.parent:
            current = self.parent
            while current:
                if current.pk == self.pk:
                    raise ValidationError("Circular folder reference detected.")
                current = current.parent

    def compute_full_path(self):
        """Build human-readable path (e.g., 'Documents/Annual Reports')"""
        if not self.parent:
            return self.name

        path_parts = []
        current = self
        while current:
            path_parts.insert(0, current.name)
            current = current.parent

        return " / ".join(path_parts[1:]) if len(path_parts) > 1 else self.name

    def compute_cloudinary_path(self):
        """Build Cloudinary folder path (e.g., 'ipawas/nigeria/documents')"""
        path_parts = ["ipawas", self.member_state.slug]

        current = self
        temp_parts = []
        while current and current.parent:  # Exclude root
            temp_parts.insert(0, current.slug)
            current = current.parent

        path_parts.extend(temp_parts)
        return "/".join(path_parts)

    def get_display_path(self):
        """Short display path for UI"""
        if self.folder_type == "root":
            return f"{self.member_state.country_name} Media"
        return self.full_path

    def get_file_count(self):
        """Count files directly in this folder"""
        return self.files.filter(is_deleted=False).count()

    def get_total_file_count(self):
        """Count all files in this folder and subfolders"""
        count = self.get_file_count()
        for subfolder in self.subfolders.filter(is_deleted=False):
            count += subfolder.get_total_file_count()
        return count

    def can_be_deleted(self):
        """Check if folder can be safely deleted"""
        if self.is_system:
            return False, "System folders cannot be deleted"

        if self.get_total_file_count() > 0:
            return False, "Folder contains files. Delete files first."

        if self.subfolders.filter(is_deleted=False).exists():
            return False, "Folder contains subfolders. Delete subfolders first."

        return True, ""

    def soft_delete(self, user):
        """Soft delete folder and all contents"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()

        # Soft delete all files
        for file in self.files.all():
            file.soft_delete(user)

        # Soft delete all subfolders
        for subfolder in self.subfolders.all():
            subfolder.soft_delete(user)

    @classmethod
    def get_or_create_system_folders(cls, member_state, user=None):
        """
        Ensure all system folders exist for a member state.
        Called during member state creation or media setup.
        """
        # Create root folder
        root, created = cls.objects.get_or_create(
            member_state=member_state,
            folder_type="root",
            defaults={
                "name": f"{member_state.country_name} Media",
                "is_system": True,
                "created_by": user,
            },
        )

        # Create system folders
        system_folders = [
            ("Documents", "documents"),
            ("Images", "images"),
            ("Videos", "videos"),
            ("Others", "others"),
        ]

        created_folders = []
        for name, folder_type in system_folders:
            folder, created = cls.objects.get_or_create(
                member_state=member_state,
                parent=root,
                folder_type=folder_type,
                defaults={
                    "name": name,
                    "is_system": True,
                    "created_by": user,
                },
            )
            if created:
                created_folders.append(folder)

        return root, created_folders


class MediaFile(models.Model):
    """
    Individual media files stored in Cloudinary.

    Supports images, documents, videos, audio with metadata,
    optimizations, and full-text search.
    """

    FILE_TYPES = [
        ("image", "Image"),
        ("document", "Document"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("other", "Other"),
    ]

    # Core Fields
    member_state = models.ForeignKey(
        MemberStateIPA,
        on_delete=models.CASCADE,
        related_name="media_files",
        db_index=True,
        help_text="Denormalized for performance",
    )

    folder = models.ForeignKey(
        MediaFolder, on_delete=models.CASCADE, related_name="files", db_index=True
    )

    # File Information
    name = models.CharField(max_length=255, help_text="Display name for the file")

    original_filename = models.CharField(max_length=255, help_text="Original uploaded filename")

    file_type = models.CharField(max_length=20, choices=FILE_TYPES, db_index=True)

    mime_type = models.CharField(max_length=100)

    size_bytes = models.BigIntegerField(validators=[MinValueValidator(0)])

    # Cloudinary Data
    cloudinary_public_id = models.CharField(
        max_length=500, unique=True, db_index=True, help_text="Unique identifier in Cloudinary"
    )

    cloudinary_resource_type = models.CharField(
        max_length=20, help_text="Cloudinary resource type (image, video, raw)"
    )

    cloudinary_url = models.URLField(max_length=1000, help_text="Primary Cloudinary URL")

    cloudinary_secure_url = models.URLField(max_length=1000, help_text="HTTPS Cloudinary URL")

    # Image-Specific Fields
    thumbnail_url = models.URLField(
        max_length=1000, blank=True, help_text="200px width thumbnail (images only)"
    )

    medium_url = models.URLField(
        max_length=1000, blank=True, help_text="800px width medium size (images only)"
    )

    width = models.IntegerField(null=True, blank=True, help_text="Width in pixels (images/videos)")

    height = models.IntegerField(
        null=True, blank=True, help_text="Height in pixels (images/videos)"
    )

    # Video/Audio Fields
    duration = models.IntegerField(
        null=True, blank=True, help_text="Duration in seconds (videos/audio)"
    )

    # Processing Status
    is_optimized = models.BooleanField(
        default=False, help_text="Whether optimized versions have been generated"
    )

    optimization_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )

    # Flexible Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional file metadata")

    # SEO & Search
    alt_text = models.CharField(max_length=255, blank=True, help_text="Alt text for images (SEO)")

    caption = models.TextField(blank=True, help_text="File caption or description")

    tags = models.JSONField(default=list, blank=True, help_text="Search tags")

    search_vector = SearchVectorField(null=True, editable=False)

    # Access Control
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="uploaded_files", db_index=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft Delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deleted_files"
    )

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Media File"
        verbose_name_plural = "Media Files"
        indexes = [
            models.Index(fields=["member_state", "folder"]),
            models.Index(fields=["member_state", "file_type"]),
            models.Index(fields=["file_type", "member_state"]),
            models.Index(fields=["-uploaded_at"]),
            models.Index(fields=["uploaded_by", "-uploaded_at"]),
            models.Index(fields=["member_state", "is_deleted", "-uploaded_at"]),
            models.Index(fields=["cloudinary_public_id"]),
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.member_state.country_name})"

    def save(self, *args, **kwargs):
        """Auto-populate member_state from folder"""
        if not self.member_state_id and self.folder:
            self.member_state = self.folder.member_state
        super().save(*args, **kwargs)

    def clean(self):
        """Validation"""
        if self.folder and self.folder.member_state != self.member_state:
            raise ValidationError("File's member state must match folder's member state.")

    def get_display_size(self):
        """Human-readable file size"""
        size = self.size_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_file_icon(self):
        """Font Awesome icon class based on file type"""
        icon_map = {
            "image": "fa-file-image",
            "document": "fa-file-pdf",
            "video": "fa-file-video",
            "audio": "fa-file-audio",
            "other": "fa-file",
        }
        return icon_map.get(self.file_type, "fa-file")

    def is_image(self):
        """Check if file is an image"""
        return self.file_type == "image"

    def is_video(self):
        """Check if file is a video"""
        return self.file_type == "video"

    def is_document(self):
        """Check if file is a document"""
        return self.file_type == "document"

    def get_thumbnail(self):
        """Get thumbnail URL (returns medium_url or original if not available)"""
        if self.thumbnail_url:
            return self.thumbnail_url
        if self.medium_url:
            return self.medium_url
        return self.cloudinary_secure_url

    def get_download_url(self):
        """Get URL for downloading file"""
        # Cloudinary download URL with fl_attachment flag
        base_url = self.cloudinary_secure_url
        if "upload/" in base_url:
            return base_url.replace("upload/", "upload/fl_attachment/")
        return base_url

    def soft_delete(self, user):
        """Soft delete file"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()

    def restore(self):
        """Restore soft-deleted file"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    @classmethod
    def detect_file_type(cls, mime_type):
        """Detect file type from MIME type"""
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ]:
            return "document"
        else:
            return "other"
