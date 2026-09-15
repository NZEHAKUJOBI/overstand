"""
Media Management Permissions - IPAWAS Platform
===============================================

Permission mixins that integrate with existing dashboard auth system.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from media_app.models import MediaFile, MediaFolder
from members.models import MemberStateIPA


class MediaAccessMixin(LoginRequiredMixin):
    """
    Base mixin for media access.
    Ensures user can only access media from their member state.

    HQ admins can access all member states.
    IPA staff can only access their own member state.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Get member state from URL or context
        member_state_slug = kwargs.get("member_state_slug")

        if member_state_slug:
            member_state = get_object_or_404(MemberStateIPA, slug=member_state_slug)

            # Check access
            if not self.can_access_member_state(request.user, member_state):
                raise PermissionDenied(
                    "You don't have permission to access this member state's media."
                )

            # Store in request for easy access
            request.member_state = member_state

        return super().dispatch(request, *args, **kwargs)

    def can_access_member_state(self, user, member_state):
        """Check if user can access member state's media"""
        # HQ admins can access all
        if user.user_type == "ipawas_admin":
            return True

        # IPA staff can only access their own
        if user.user_type == "ipa_staff":
            try:
                return user.ipa_profile.member_state == member_state
            except AttributeError:
                return False

        return False


class CanManageMediaMixin(MediaAccessMixin):
    """
    Require permission to manage media (upload, delete, organize).

    HQ admins: Always have permission
    IPA staff: Need can_edit_profile or specific can_manage_media permission
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # HQ admins always have permission
        if request.user.user_type == "ipawas_admin":
            return super().dispatch(request, *args, **kwargs)

        # IPA staff need permission
        if request.user.user_type == "ipa_staff":
            try:
                profile = request.user.ipa_profile
                # For now, use can_edit_profile as proxy for media management
                # You can add can_manage_media to IPAProfile model later
                if profile.can_edit_profile:
                    return super().dispatch(request, *args, **kwargs)
            except AttributeError:
                pass

        raise PermissionDenied("You don't have permission to manage media files.")


class CanUploadMediaMixin(MediaAccessMixin):
    """
    Permission to upload media files.

    HQ admins: Always can upload
    IPA staff: Need can_edit_profile
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # HQ admins can always upload
        if request.user.user_type == "ipawas_admin":
            return super().dispatch(request, *args, **kwargs)

        # IPA staff need can_edit_profile
        if request.user.user_type == "ipa_staff":
            try:
                if request.user.ipa_profile.can_edit_profile:
                    return super().dispatch(request, *args, **kwargs)
            except AttributeError:
                pass

        raise PermissionDenied("You don't have permission to upload files.")


class CanDeleteMediaMixin(MediaAccessMixin):
    """
    Permission to delete media files.

    HQ admins: Can delete any file
    IPA staff: Can delete own uploads if they have can_edit_profile
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # HQ admins can always delete
        if request.user.user_type == "ipawas_admin":
            return super().dispatch(request, *args, **kwargs)

        # IPA staff with can_edit_profile can delete own files
        if request.user.user_type == "ipa_staff":
            try:
                if request.user.ipa_profile.can_edit_profile:
                    return super().dispatch(request, *args, **kwargs)
            except AttributeError:
                pass

        raise PermissionDenied("You don't have permission to delete files.")

    def can_delete_file(self, user, media_file):
        """Check if user can delete specific file"""
        # HQ admins can delete any file
        if user.user_type == "ipawas_admin":
            return True

        # IPA staff can only delete their own uploads
        if user.user_type == "ipa_staff":
            try:
                if user.ipa_profile.can_edit_profile:
                    return media_file.uploaded_by == user
            except AttributeError:
                pass

        return False


class FolderAccessMixin(MediaAccessMixin):
    """
    Mixin for views that work with folders.
    Validates folder belongs to accessible member state.
    """

    def get_folder(self):
        """Get and validate folder access"""
        folder_id = self.kwargs.get("folder_id") or self.kwargs.get("pk")

        if not folder_id:
            return None

        folder = get_object_or_404(MediaFolder, pk=folder_id, is_deleted=False)

        # Check access
        if not self.can_access_member_state(self.request.user, folder.member_state):
            raise PermissionDenied("You don't have permission to access this folder.")

        return folder


class FileAccessMixin(MediaAccessMixin):
    """
    Mixin for views that work with files.
    Validates file belongs to accessible member state.
    """

    def get_file(self):
        """Get and validate file access"""
        file_id = self.kwargs.get("file_id") or self.kwargs.get("pk")

        if not file_id:
            return None

        media_file = get_object_or_404(MediaFile, pk=file_id, is_deleted=False)

        # Check access
        if not self.can_access_member_state(self.request.user, media_file.member_state):
            raise PermissionDenied("You don't have permission to access this file.")

        return media_file
