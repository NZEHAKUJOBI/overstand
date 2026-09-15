"""
Folder Service - IPAWAS Media Management
=========================================

Business logic for folder operations:
- Creating/deleting folders
- Hierarchy validation
- System folder management
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from media_app.models import MediaFolder
from media_app.services.cloudinary_service import CloudinaryService


class FolderService:
    """
    Service for managing media folders.

    Enforces:
    - Maximum depth of 4 levels
    - System folder protection
    - Member state isolation
    """

    @staticmethod
    @transaction.atomic
    def ensure_system_folders(member_state, user=None):
        """
        Create all required system folders for a member state.

        Called during:
        - Member state creation
        - First-time media access

        Args:
            member_state: MemberStateIPA instance
            user: User creating folders

        Returns:
            tuple: (root_folder, list of created system folders)
        """
        return MediaFolder.get_or_create_system_folders(member_state, user)

    @staticmethod
    def create_custom_folder(member_state, parent, name, description, user):
        """
        Create a custom folder.

        Validates:
        - Maximum depth not exceeded
        - Parent belongs to same member state
        - Name uniqueness within parent

        Args:
            member_state: MemberStateIPA instance
            parent: Parent MediaFolder instance
            name: Folder name
            description: Folder description
            user: User creating folder

        Returns:
            MediaFolder instance

        Raises:
            ValidationError: If validation fails
        """
        # Depth check
        if parent and parent.level >= 3:
            raise ValidationError("Cannot create folders beyond level 3. Maximum depth reached.")

        # Member state match check
        if parent and parent.member_state != member_state:
            raise ValidationError("Parent folder must belong to the same member state.")

        # Check for existing folder with same name
        existing = MediaFolder.objects.filter(
            member_state=member_state, parent=parent, name__iexact=name, is_deleted=False
        ).exists()

        if existing:
            raise ValidationError(f"A folder named '{name}' already exists in this location.")

        # Create folder
        folder = MediaFolder(
            member_state=member_state,
            parent=parent,
            name=name,
            description=description,
            folder_type="custom",
            is_system=False,
            created_by=user,
        )

        folder.full_clean()
        folder.save()

        return folder

    @staticmethod
    def rename_folder(folder, new_name, user):
        """
        Rename a folder.

        Args:
            folder: MediaFolder instance
            new_name: New folder name
            user: User performing rename

        Raises:
            ValidationError: If folder is system folder or name exists
        """
        if folder.is_system:
            raise ValidationError("System folders cannot be renamed.")

        # Check for duplicate name
        existing = (
            MediaFolder.objects.filter(
                member_state=folder.member_state,
                parent=folder.parent,
                name__iexact=new_name,
                is_deleted=False,
            )
            .exclude(pk=folder.pk)
            .exists()
        )

        if existing:
            raise ValidationError(f"A folder named '{new_name}' already exists in this location.")

        folder.name = new_name
        folder.save()

    @staticmethod
    @transaction.atomic
    def delete_folder(folder, user, force=False):
        """
        Delete a folder.

        By default, performs soft delete. If force=True, deletes from
        Cloudinary and database.

        Args:
            folder: MediaFolder instance
            user: User performing deletion
            force: If True, hard delete

        Raises:
            ValidationError: If folder cannot be deleted
        """
        # Check if deletion is allowed
        can_delete, reason = folder.can_be_deleted()
        if not can_delete:
            raise ValidationError(reason)

        if force:
            # Hard delete from Cloudinary
            CloudinaryService.delete_folder(folder.cloudinary_folder)
            folder.delete()
        else:
            # Soft delete
            folder.soft_delete(user)

    @staticmethod
    def move_folder(folder, new_parent, user):
        """
        Move folder to a different parent.

        Args:
            folder: MediaFolder instance
            new_parent: New parent MediaFolder instance (or None for root)
            user: User performing move

        Raises:
            ValidationError: If move is invalid
        """
        if folder.is_system:
            raise ValidationError("System folders cannot be moved.")

        # Check depth after move
        if new_parent:
            if new_parent.level >= 3:
                raise ValidationError(
                    "Cannot move folder. Target location would exceed maximum depth."
                )

            # Check circular reference
            current = new_parent
            while current:
                if current.pk == folder.pk:
                    raise ValidationError("Cannot move folder into itself.")
                current = current.parent

        # Check member state match
        if new_parent and new_parent.member_state != folder.member_state:
            raise ValidationError("Cannot move folder to a different member state.")

        folder.parent = new_parent
        folder.save()

    @staticmethod
    def get_folder_tree(member_state, include_deleted=False):
        """
        Get hierarchical folder structure for a member state.

        Args:
            member_state: MemberStateIPA instance
            include_deleted: Include soft-deleted folders

        Returns:
            dict: Nested folder structure
        """
        queryset = MediaFolder.objects.filter(member_state=member_state)

        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)

        folders = queryset.select_related("parent", "created_by").order_by("level", "name")

        # Build tree structure
        folder_dict = {f.id: {"folder": f, "children": []} for f in folders}

        root_folders = []
        for folder in folders:
            if folder.parent_id:
                if folder.parent_id in folder_dict:
                    folder_dict[folder.parent_id]["children"].append(folder_dict[folder.id])
            else:
                root_folders.append(folder_dict[folder.id])

        return root_folders

    @staticmethod
    def get_breadcrumbs(folder):
        """
        Get breadcrumb trail for a folder.

        Args:
            folder: MediaFolder instance

        Returns:
            list: List of (folder, url) tuples from root to current
        """
        breadcrumbs = []
        current = folder

        while current:
            breadcrumbs.insert(0, current)
            current = current.parent

        return breadcrumbs

    @staticmethod
    def search_folders(member_state, query):
        """
        Search folders by name.

        Args:
            member_state: MemberStateIPA instance
            query: Search query string

        Returns:
            QuerySet: Matching folders
        """
        return MediaFolder.objects.filter(
            member_state=member_state, name__icontains=query, is_deleted=False
        ).select_related("parent")
