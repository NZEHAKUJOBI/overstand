"""
File Service - IPAWAS Media Management
=======================================

Business logic for file operations:
- File uploads with Cloudinary integration
- Image optimization
- File deletion
- Bulk operations
"""

import mimetypes

from django.contrib.postgres.search import SearchVector
from django.core.exceptions import ValidationError
from django.db import models, transaction

from media_app.models import MediaFile
from media_app.services.cloudinary_service import CloudinaryService


class FileService:
    """
    Service for managing media files.

    Handles uploads, optimization, and CRUD operations.
    """

    # File size limits (in bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

    @staticmethod
    def validate_file_upload(file, file_type):
        """
        Validate file before upload.

        Args:
            file: Django UploadedFile
            file_type: Detected file type

        Raises:
            ValidationError: If file is invalid
        """
        # Size validation
        size_limits = {
            "image": FileService.MAX_IMAGE_SIZE,
            "document": FileService.MAX_DOCUMENT_SIZE,
            "video": FileService.MAX_VIDEO_SIZE,
            "audio": FileService.MAX_DOCUMENT_SIZE,
            "other": FileService.MAX_DOCUMENT_SIZE,
        }

        max_size = size_limits.get(file_type, FileService.MAX_DOCUMENT_SIZE)

        if file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise ValidationError(
                f"File size exceeds maximum allowed size of {max_mb}MB for {file_type} files."
            )

        # MIME type validation (basic check)
        if not file.content_type:
            raise ValidationError("Could not determine file type.")

    @staticmethod
    @transaction.atomic
    def upload_file(file, folder, name, user, alt_text="", caption="", tags=None):
        """
        Upload file to Cloudinary and create database record.

        Process:
        1. Validate file
        2. Upload to Cloudinary
        3. For images: generate optimized versions
        4. Create MediaFile record

        Args:
            file: Django UploadedFile
            folder: MediaFolder instance
            name: Display name for file
            user: User uploading file
            alt_text: Alt text (for images)
            caption: File caption
            tags: List of tags

        Returns:
            MediaFile instance

        Raises:
            ValidationError: If upload fails
        """
        # Detect file type
        mime_type = file.content_type
        file_type = MediaFile.detect_file_type(mime_type)

        # Validate
        FileService.validate_file_upload(file, file_type)

        # Quota check
        FileService.check_quota(folder.member_state, file.size)

        # Determine Cloudinary resource type
        resource_type_map = {
            "image": "image",
            "video": "video",
            "audio": "video",  # Cloudinary stores audio as video
            "document": "raw",
            "other": "raw",
        }
        cloudinary_resource_type = resource_type_map.get(file_type, "raw")

        # Upload to Cloudinary
        upload_result = CloudinaryService.upload_file(
            file, folder.cloudinary_folder, resource_type=cloudinary_resource_type
        )

        if not upload_result["success"]:
            raise ValidationError(f"Upload failed: {upload_result.get('error', 'Unknown error')}")

        cloudinary_data = upload_result["data"]

        # Create MediaFile record
        media_file = MediaFile(
            member_state=folder.member_state,
            folder=folder,
            name=name or file.name,
            original_filename=file.name,
            file_type=file_type,
            mime_type=mime_type,
            size_bytes=file.size,
            cloudinary_public_id=cloudinary_data["public_id"],
            cloudinary_resource_type=cloudinary_data["resource_type"],
            cloudinary_url=cloudinary_data["url"],
            cloudinary_secure_url=cloudinary_data["secure_url"],
            alt_text=alt_text,
            caption=caption,
            tags=tags or [],
            uploaded_by=user,
            metadata={
                "format": cloudinary_data.get("format"),
                "version": cloudinary_data.get("version"),
            },
        )

        # Extract dimensions for images/videos
        if "width" in cloudinary_data:
            media_file.width = cloudinary_data["width"]
        if "height" in cloudinary_data:
            media_file.height = cloudinary_data["height"]
        if "duration" in cloudinary_data:
            media_file.duration = cloudinary_data["duration"]

        media_file.save()

        # Optimize if image
        if file_type == "image":
            FileService.optimize_image(media_file)

        # Generate video thumbnail
        if file_type == "video":
            FileService.generate_video_thumbnail(media_file)

        # Update search vector
        FileService.update_search_vector(media_file)

        return media_file

    @staticmethod
    def check_quota(member_state, additional_bytes):
        """
        Raise ValidationError if uploading additional_bytes would exceed the member state quota.
        """
        from django.db.models import Sum

        used = (
            MediaFile.objects.filter(member_state=member_state, is_deleted=False).aggregate(
                total=Sum("size_bytes")
            )["total"]
            or 0
        )
        quota = member_state.storage_quota_bytes
        if used + additional_bytes > quota:
            remaining_mb = max(0, (quota - used)) / (1024 * 1024)
            raise ValidationError(
                f"Storage quota exceeded. You have {remaining_mb:.1f} MB remaining "
                f"out of your {quota // (1024**3)} GB allowance."
            )

    @staticmethod
    def optimize_image(media_file):
        """
        Generate optimized versions of an image.

        Args:
            media_file: MediaFile instance
        """
        if not media_file.is_image():
            return

        media_file.optimization_status = "processing"
        media_file.save()

        try:
            # Generate transformations
            urls = CloudinaryService.generate_image_transformations(media_file.cloudinary_public_id)

            media_file.thumbnail_url = urls["thumbnail_url"]
            media_file.medium_url = urls["medium_url"]
            media_file.is_optimized = True
            media_file.optimization_status = "completed"
            media_file.save()
        except Exception as e:
            media_file.optimization_status = "failed"
            media_file.metadata["optimization_error"] = str(e)
            media_file.save()

    @staticmethod
    def generate_video_thumbnail(media_file):
        """
        Generate thumbnail for video.

        Args:
            media_file: MediaFile instance
        """
        if not media_file.is_video():
            return

        try:
            thumbnail_url = CloudinaryService.get_video_thumbnail(media_file.cloudinary_public_id)
            media_file.thumbnail_url = thumbnail_url
            media_file.save()
        except Exception:
            pass  # Non-critical, fail silently

    @staticmethod
    @transaction.atomic
    def delete_file(media_file, user, permanent=False):
        """
        Delete a file.

        Args:
            media_file: MediaFile instance
            user: User performing deletion
            permanent: If True, delete from Cloudinary and DB

        Raises:
            ValidationError: If deletion fails
        """
        if permanent:
            # Delete from Cloudinary
            delete_result = CloudinaryService.delete_file(
                media_file.cloudinary_public_id, media_file.cloudinary_resource_type
            )

            if not delete_result["success"]:
                raise ValidationError(
                    f"Failed to delete from Cloudinary: {delete_result.get('error')}"
                )

            media_file.delete()
        else:
            # Soft delete
            media_file.soft_delete(user)

    @staticmethod
    def move_file(media_file, target_folder, user):
        """
        Move file to different folder.

        Args:
            media_file: MediaFile instance
            target_folder: Target MediaFolder instance
            user: User performing move

        Raises:
            ValidationError: If move is invalid
        """
        # Validate member state match
        if target_folder.member_state != media_file.member_state:
            raise ValidationError("Cannot move file to a folder in a different member state.")

        media_file.folder = target_folder
        media_file.save()

    @staticmethod
    def update_file_metadata(media_file, name=None, alt_text=None, caption=None, tags=None):
        """
        Update file metadata.

        Args:
            media_file: MediaFile instance
            name: New name (optional)
            alt_text: New alt text (optional)
            caption: New caption (optional)
            tags: New tags list (optional)
        """
        if name is not None:
            media_file.name = name
        if alt_text is not None:
            media_file.alt_text = alt_text
        if caption is not None:
            media_file.caption = caption
        if tags is not None:
            media_file.tags = tags

        media_file.save()
        FileService.update_search_vector(media_file)

    @staticmethod
    def update_search_vector(media_file):
        """
        Update full-text search vector.

        Args:
            media_file: MediaFile instance
        """
        MediaFile.objects.filter(pk=media_file.pk).update(
            search_vector=(
                SearchVector("name", weight="A")
                + SearchVector("caption", weight="B")
                + SearchVector("alt_text", weight="C")
            )
        )

    @staticmethod
    def bulk_upload(files, folder, user):
        """
        Upload multiple files at once.

        Args:
            files: List of Django UploadedFile objects
            folder: MediaFolder instance
            user: User uploading files

        Returns:
            dict: {
                'successful': [list of MediaFile instances],
                'failed': [list of {'filename': str, 'error': str}]
            }
        """
        successful = []
        failed = []

        for file in files:
            try:
                media_file = FileService.upload_file(file, folder, name=file.name, user=user)
                successful.append(media_file)
            except Exception as e:
                failed.append({"filename": file.name, "error": str(e)})

        return {"successful": successful, "failed": failed}

    @staticmethod
    def search_files(member_state, query, file_type=None, folder=None):
        """
        Search files by name, caption, alt text.

        Args:
            member_state: MemberStateIPA instance
            query: Search query
            file_type: Filter by file type (optional)
            folder: Filter by folder (optional)

        Returns:
            QuerySet: Matching files
        """
        from django.contrib.postgres.search import SearchQuery, SearchRank

        queryset = MediaFile.objects.filter(member_state=member_state, is_deleted=False)

        if file_type:
            queryset = queryset.filter(file_type=file_type)

        if folder:
            queryset = queryset.filter(folder=folder)

        if query:
            search_query = SearchQuery(query)
            queryset = (
                queryset.annotate(rank=SearchRank("search_vector", search_query))
                .filter(search_vector=search_query)
                .order_by("-rank")
            )

        return queryset.select_related("folder", "uploaded_by")

    @staticmethod
    def get_recent_files(member_state, limit=20, file_type=None):
        """
        Get recently uploaded files.

        Args:
            member_state: MemberStateIPA instance
            limit: Number of files to return
            file_type: Filter by file type (optional)

        Returns:
            QuerySet: Recent files
        """
        queryset = MediaFile.objects.filter(member_state=member_state, is_deleted=False)

        if file_type:
            queryset = queryset.filter(file_type=file_type)

        return queryset.select_related("folder", "uploaded_by").order_by("-uploaded_at")[:limit]

    @staticmethod
    def get_storage_stats(member_state):
        """
        Calculate storage statistics for a member state.

        Args:
            member_state: MemberStateIPA instance

        Returns:
            dict: Storage statistics
        """
        from django.db.models import Count, Sum

        files = MediaFile.objects.filter(member_state=member_state, is_deleted=False)

        stats = files.aggregate(
            total_files=Count("id"),
            total_size=Sum("size_bytes"),
            images_count=Count("id", filter=models.Q(file_type="image")),
            documents_count=Count("id", filter=models.Q(file_type="document")),
            videos_count=Count("id", filter=models.Q(file_type="video")),
        )

        # Format total size
        total_bytes = stats["total_size"] or 0
        for unit in ["B", "KB", "MB", "GB"]:
            if total_bytes < 1024.0:
                stats["total_size_display"] = f"{total_bytes:.1f} {unit}"
                break
            total_bytes /= 1024.0
        else:
            stats["total_size_display"] = f"{total_bytes:.1f} TB"

        return stats
