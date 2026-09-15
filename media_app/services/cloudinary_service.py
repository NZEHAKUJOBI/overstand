"""
Cloudinary Service - IPAWAS Media Management
=============================================

Handles all Cloudinary API interactions:
- File uploads with proper folder structure
- Image optimization (thumbnail, medium sizes)
- File deletion
- URL transformations
"""

from django.conf import settings

import cloudinary
import cloudinary.api
import cloudinary.uploader


class CloudinaryService:
    """
    Abstraction layer for Cloudinary operations.

    Analogy: Like a specialized courier service that knows exactly
    where to store each package and how to optimize its contents.
    """

    @staticmethod
    def initialize():
        """Initialize Cloudinary configuration"""
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )

    @staticmethod
    def upload_file(file, folder_path, resource_type="auto", **options):
        """
        Upload file to Cloudinary.

        Args:
            file: File object or path
            folder_path: Cloudinary folder path (e.g., 'ipawas/nigeria/documents')
            resource_type: 'image', 'video', 'raw', or 'auto'
            **options: Additional Cloudinary options

        Returns:
            dict: Cloudinary response with public_id, url, etc.
        """
        CloudinaryService.initialize()

        upload_options = {
            "folder": folder_path,
            "resource_type": resource_type,
            "use_filename": True,
            "unique_filename": True,
            "overwrite": False,
        }
        upload_options.update(options)

        try:
            result = cloudinary.uploader.upload(file, **upload_options)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def generate_image_transformations(public_id):
        """
        Generate optimized versions of an image.

        Creates:
        - Thumbnail: 200px width, auto quality, WebP format
        - Medium: 800px width, auto quality, WebP format

        Args:
            public_id: Cloudinary public_id of the image

        Returns:
            dict: URLs for thumbnail and medium versions
        """
        CloudinaryService.initialize()

        # Thumbnail transformation
        thumbnail_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=200,
            height=200,
            crop="fill",
            gravity="auto",
            quality="auto",
            fetch_format="auto",
            secure=True,
        )

        # Medium transformation
        medium_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=800, crop="limit", quality="auto:good", fetch_format="auto", secure=True
        )

        return {"thumbnail_url": thumbnail_url, "medium_url": medium_url}

    @staticmethod
    def delete_file(public_id, resource_type="image"):
        """
        Delete file from Cloudinary.

        Args:
            public_id: Cloudinary public_id
            resource_type: 'image', 'video', or 'raw'

        Returns:
            dict: Success status
        """
        CloudinaryService.initialize()

        try:
            result = cloudinary.uploader.destroy(
                public_id, resource_type=resource_type, invalidate=True
            )
            return {"success": result.get("result") == "ok", "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_folder(folder_path):
        """
        Delete entire folder from Cloudinary (and all contents).

        Args:
            folder_path: Cloudinary folder path

        Returns:
            dict: Success status
        """
        CloudinaryService.initialize()

        try:
            # Delete all resources in folder
            result = cloudinary.api.delete_resources_by_prefix(folder_path, resource_type="image")

            # Also delete raw files (documents, etc.)
            cloudinary.api.delete_resources_by_prefix(folder_path, resource_type="raw")

            # Delete videos
            cloudinary.api.delete_resources_by_prefix(folder_path, resource_type="video")

            # Delete the folder itself
            cloudinary.api.delete_folder(folder_path)

            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_video_thumbnail(public_id):
        """
        Generate thumbnail from video.

        Args:
            public_id: Cloudinary public_id of video

        Returns:
            str: Thumbnail URL
        """
        CloudinaryService.initialize()

        return cloudinary.CloudinaryVideo(public_id).build_url(
            resource_type="video",
            format="jpg",
            transformation=[
                {"start_offset": "0"},
                {"width": 400, "crop": "fill", "gravity": "auto"},
            ],
            secure=True,
        )

    @staticmethod
    def optimize_pdf(public_id):
        """
        Get optimized PDF URL.

        Args:
            public_id: Cloudinary public_id of PDF

        Returns:
            str: Optimized PDF URL
        """
        CloudinaryService.initialize()

        return cloudinary.CloudinaryImage(public_id).build_url(
            resource_type="raw", format="pdf", flags="attachment", secure=True
        )
