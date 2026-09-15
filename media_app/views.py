"""
Media Management Views - IPAWAS Platform
=========================================

Thin views that delegate business logic to services.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from media_app.forms import (
    BulkFileUploadForm,
    FileEditForm,
    FileMoveForm,
    FileSearchForm,
    FileUploadForm,
    FolderCreateForm,
    FolderRenameForm,
)
from media_app.models import MediaFile, MediaFolder
from media_app.permissions import (
    CanDeleteMediaMixin,
    CanManageMediaMixin,
    CanUploadMediaMixin,
    FileAccessMixin,
    FolderAccessMixin,
    MediaAccessMixin,
)
from media_app.services import FileService, FolderService


class MediaLibraryView(MediaAccessMixin, TemplateView):
    """
    Main media library view showing folder tree and files.
    """

    template_name = "media_app/library.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.request.member_state
        context["member_state"] = member_state

        # Ensure system folders exist
        FolderService.ensure_system_folders(member_state, self.request.user)

        # Get folder tree
        context["folder_tree"] = FolderService.get_folder_tree(member_state)

        # Get current folder (if specified)
        folder_id = self.request.GET.get("folder")
        if folder_id:
            try:
                context["current_folder"] = MediaFolder.objects.get(
                    pk=folder_id, member_state=member_state, is_deleted=False
                )
                context["breadcrumbs"] = FolderService.get_breadcrumbs(context["current_folder"])
            except MediaFolder.DoesNotExist:
                pass

        # Get files in current folder
        if "current_folder" in context:
            context["files"] = (
                MediaFile.objects.filter(folder=context["current_folder"], is_deleted=False)
                .select_related("uploaded_by")
                .order_by("-uploaded_at")
            )
        else:
            # Show recent files if no folder selected
            context["files"] = FileService.get_recent_files(member_state, limit=20)

        # Storage stats
        context["storage_stats"] = FileService.get_storage_stats(member_state)

        # User permissions
        context["can_upload"] = self.request.user.user_type == "ipawas_admin" or (
            hasattr(self.request.user, "ipa_profile")
            and self.request.user.ipa_profile.can_edit_profile
        )

        return context


class FolderCreateView(CanManageMediaMixin, CreateView):
    """Create custom folder"""

    model = MediaFolder
    form_class = FolderCreateForm
    template_name = "media_app/folder_create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        member_state = self.request.member_state

        # Get parent folder
        parent_id = self.request.GET.get("parent")
        parent = None
        if parent_id:
            parent = get_object_or_404(
                MediaFolder, pk=parent_id, member_state=member_state, is_deleted=False
            )

        kwargs["member_state"] = member_state
        kwargs["parent"] = parent
        return kwargs

    def form_valid(self, form):
        try:
            member_state = self.request.member_state
            parent_id = self.request.GET.get("parent")
            parent = None

            if parent_id:
                parent = MediaFolder.objects.get(pk=parent_id, member_state=member_state)

            folder = FolderService.create_custom_folder(
                member_state=member_state,
                parent=parent,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
                user=self.request.user,
            )

            messages.success(self.request, f"Folder '{folder.name}' created successfully.")

            return redirect("dashboard:country:media:library", member_state_slug=member_state.slug)

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class FolderRenameView(CanManageMediaMixin, FolderAccessMixin, UpdateView):
    """Rename folder"""

    model = MediaFolder
    form_class = FolderRenameForm
    template_name = "media_app/folder_rename.html"

    def get_object(self):
        return self.get_folder()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["folder"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        folder = self.get_object()

        try:
            FolderService.rename_folder(folder, form.cleaned_data["name"], self.request.user)

            messages.success(self.request, f"Folder renamed to '{form.cleaned_data['name']}'.")

            return redirect(
                "dashboard:country:media:library", member_state_slug=self.request.member_state.slug
            )

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class FolderDeleteView(CanManageMediaMixin, FolderAccessMixin, DeleteView):
    """Delete folder"""

    model = MediaFolder
    template_name = "media_app/folder_delete.html"

    def get_object(self):
        return self.get_folder()

    def delete(self, request, *args, **kwargs):
        folder = self.get_object()

        try:
            FolderService.delete_folder(folder, request.user, force=False)  # Soft delete

            messages.success(request, f"Folder '{folder.name}' deleted successfully.")

            return redirect(
                "dashboard:country:media:library", member_state_slug=request.member_state.slug
            )

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect(
                "dashboard:country:media:library", member_state_slug=request.member_state.slug
            )


class FileUploadView(CanUploadMediaMixin, View):
    """Upload single file"""

    def get(self, request, *args, **kwargs):
        member_state = request.member_state
        folder_id = request.GET.get("folder")

        # Get folder
        if folder_id:
            folder = get_object_or_404(
                MediaFolder, pk=folder_id, member_state=member_state, is_deleted=False
            )
        else:
            # Default to Documents folder
            folder = MediaFolder.objects.filter(
                member_state=member_state, folder_type="documents", is_deleted=False
            ).first()

        form = FileUploadForm()

        return render(
            request,
            "media_app/file_upload.html",
            {"form": form, "folder": folder, "member_state": member_state},
        )

    def post(self, request, *args, **kwargs):
        member_state = request.member_state
        folder_id = request.POST.get("folder_id")

        folder = get_object_or_404(
            MediaFolder, pk=folder_id, member_state=member_state, is_deleted=False
        )

        form = FileUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                file = form.cleaned_data["file"]
                name = form.cleaned_data.get("name") or file.name

                media_file = FileService.upload_file(
                    file=file,
                    folder=folder,
                    name=name,
                    user=request.user,
                    alt_text=form.cleaned_data.get("alt_text", ""),
                    caption=form.cleaned_data.get("caption", ""),
                    tags=form.cleaned_data.get("tags", []),
                )

                messages.success(request, f"File '{media_file.name}' uploaded successfully.")

                return redirect(
                    "dashboard:country:media:library", member_state_slug=member_state.slug
                )

            except ValidationError as e:
                messages.error(request, str(e))
                return render(
                    request,
                    "media_app/file_upload.html",
                    {"form": form, "folder": folder, "member_state": member_state},
                )

        return render(
            request,
            "media_app/file_upload.html",
            {"form": form, "folder": folder, "member_state": member_state},
        )


class BulkFileUploadView(CanUploadMediaMixin, View):
    """Bulk file upload"""

    def get(self, request, *args, **kwargs):
        member_state = request.member_state
        folder_id = request.GET.get("folder")

        if folder_id:
            folder = get_object_or_404(
                MediaFolder, pk=folder_id, member_state=member_state, is_deleted=False
            )
        else:
            folder = MediaFolder.objects.filter(
                member_state=member_state, folder_type="documents", is_deleted=False
            ).first()

        form = BulkFileUploadForm()

        return render(
            request,
            "media_app/bulk_upload.html",
            {"form": form, "folder": folder, "member_state": member_state},
        )

    def post(self, request, *args, **kwargs):
        member_state = request.member_state
        folder_id = request.POST.get("folder_id")

        folder = get_object_or_404(
            MediaFolder, pk=folder_id, member_state=member_state, is_deleted=False
        )

        files = request.FILES.getlist("files")

        if not files:
            messages.error(request, "No files selected.")
            return redirect(
                "dashboard:country:media:file_bulk_upload", member_state_slug=member_state.slug
            )

        # Upload files
        result = FileService.bulk_upload(files, folder, request.user)

        # Show results
        if result["successful"]:
            messages.success(request, f"Successfully uploaded {len(result['successful'])} file(s).")

        if result["failed"]:
            for failure in result["failed"]:
                messages.error(
                    request, f"Failed to upload {failure['filename']}: {failure['error']}"
                )

        return redirect("dashboard:country:media", member_state_slug=member_state.slug)


class FileDetailView(FileAccessMixin, DetailView):
    """View file details"""

    model = MediaFile
    template_name = "media_app/file_detail.html"
    context_object_name = "file"

    def get_object(self):
        return self.get_file()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Member state is already validated and set by MemberStateAccessMixin
        member_state = self.request.member_state
        context["member_state"] = member_state
        return context


class FileEditView(CanManageMediaMixin, FileAccessMixin, UpdateView):
    """Edit file metadata"""

    model = MediaFile
    form_class = FileEditForm
    template_name = "media_app/file_edit.html"

    def get_object(self):
        return self.get_file()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Member state is already validated and set by MemberStateAccessMixin
        member_state = self.request.member_state
        context["member_state"] = member_state
        return context

    def form_valid(self, form):
        media_file = form.save()

        # Update search vector
        FileService.update_search_vector(media_file)

        messages.success(self.request, f"File '{media_file.name}' updated successfully.")

        return redirect(
            "dashboard:country:media:file_detail",
            member_state_slug=self.request.member_state.slug,
            pk=media_file.pk,
        )


class FileDeleteView(CanDeleteMediaMixin, FileAccessMixin, DeleteView):
    """Delete file"""

    model = MediaFile
    template_name = "media_app/file_delete.html"
    context_object_name = "file"

    def get_object(self):
        media_file = self.get_file()

        # Check if user can delete this specific file
        if not self.can_delete_file(self.request.user, media_file):
            raise PermissionDenied("You can only delete your own uploads.")

        return media_file

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.member_state
        return context

    def get_success_url(self):
        return reverse(
            "dashboard:country:media:library",
            kwargs={"member_state_slug": self.request.member_state.slug},
        )

    def delete(self, request, *args, **kwargs):
        media_file = self.get_object()

        try:
            FileService.delete_file(media_file, request.user, permanent=False)  # Soft delete

            messages.success(request, f"File '{media_file.name}' deleted successfully.")

            return redirect(
                "dashboard:country:media:library",
                member_state_slug=request.member_state.slug,
                pk=media_file.pk,
            )

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect(
                "dashboard:country:media:library",
                member_state_slug=request.member_state.slug,
                pk=media_file.pk,
            )


class FileSearchView(MediaAccessMixin, ListView):
    """Search files"""

    model = MediaFile
    template_name = "media_app/file_search.html"
    context_object_name = "files"
    paginate_by = 24

    def get_queryset(self):
        member_state = self.request.member_state
        form = FileSearchForm(self.request.GET, member_state=member_state)

        if form.is_valid():
            query = form.cleaned_data.get("query")
            file_type = form.cleaned_data.get("file_type")
            folder = form.cleaned_data.get("folder")

            return FileService.search_files(member_state, query, file_type, folder)

        return MediaFile.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = FileSearchForm(self.request.GET, member_state=self.request.member_state)
        return context


# AJAX Views for better UX


class FolderTreeAjaxView(MediaAccessMixin, View):
    """AJAX endpoint for folder tree"""

    def get(self, request, *args, **kwargs):
        member_state = request.member_state
        folder_tree = FolderService.get_folder_tree(member_state)

        def serialize_tree(tree_nodes):
            result = []
            for node in tree_nodes:
                folder = node["folder"]
                result.append(
                    {
                        "id": folder.id,
                        "name": folder.name,
                        "type": folder.folder_type,
                        "level": folder.level,
                        "file_count": folder.get_file_count(),
                        "is_system": folder.is_system,
                        "children": serialize_tree(node["children"]),
                    }
                )
            return result

        return JsonResponse({"folders": serialize_tree(folder_tree)})


class FileUploadAjaxView(CanUploadMediaMixin, View):
    """AJAX file upload endpoint"""

    def post(self, request, *args, **kwargs):
        member_state = request.member_state
        folder_id = request.POST.get("folder_id")

        try:
            folder = MediaFolder.objects.get(
                pk=folder_id, member_state=member_state, is_deleted=False
            )
        except MediaFolder.DoesNotExist:
            return JsonResponse({"success": False, "error": "Invalid folder"}, status=400)

        if "file" not in request.FILES:
            return JsonResponse({"success": False, "error": "No file provided"}, status=400)

        file = request.FILES["file"]

        try:
            media_file = FileService.upload_file(
                file=file, folder=folder, name=file.name, user=request.user
            )

            return JsonResponse(
                {
                    "success": True,
                    "file": {
                        "id": media_file.id,
                        "name": media_file.name,
                        "type": media_file.file_type,
                        "size": media_file.get_display_size(),
                        "url": media_file.cloudinary_secure_url,
                        "thumbnail": media_file.get_thumbnail(),
                    },
                }
            )

        except ValidationError as e:
            return JsonResponse({"success": False, "error": "; ".join(e.messages)}, status=400)


class PickerListAPIView(MediaAccessMixin, View):
    """
    JSON API for the media picker modal.
    Returns files for the current member state, optionally filtered by type.
    GET ?type=image|video|document&search=...&page=1
    """

    PAGE_SIZE = 30

    def get(self, request, *args, **kwargs):
        member_state = request.member_state
        qs = MediaFile.objects.filter(member_state=member_state, is_deleted=False)

        file_type = request.GET.get("type")
        if file_type in ("image", "video", "document", "audio"):
            qs = qs.filter(file_type=file_type)

        search = request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(name__icontains=search)

        qs = qs.order_by("-uploaded_at")

        # Simple offset pagination
        try:
            page = max(1, int(request.GET.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        offset = (page - 1) * self.PAGE_SIZE
        total = qs.count()
        files = qs[offset : offset + self.PAGE_SIZE]

        data = []
        for f in files:
            data.append(
                {
                    "id": f.id,
                    "name": f.name,
                    "file_type": f.file_type,
                    "size_display": f.get_display_size(),
                    "url": f.cloudinary_secure_url,
                    # Only return a thumbnail URL for images; other types get None so the
                    # picker card shows a file icon instead of a broken <img>.
                    "thumbnail": f.get_thumbnail() if f.file_type == "image" else None,
                    "uploaded_at": f.uploaded_at.strftime("%d %b %Y"),
                }
            )

        return JsonResponse(
            {
                "files": data,
                "total": total,
                "page": page,
                "has_next": (offset + self.PAGE_SIZE) < total,
            }
        )


class PickerUploadAPIView(CanUploadMediaMixin, View):
    """
    JSON upload endpoint for the media picker modal.
    POST with multipart/form-data: file, folder_type (images|videos|documents)
    """

    def post(self, request, *args, **kwargs):
        member_state = request.member_state

        if "file" not in request.FILES:
            return JsonResponse({"success": False, "error": "No file provided."}, status=400)

        file = request.FILES["file"]
        folder_type = request.POST.get("folder_type", "images")

        # Map folder_type to a valid system folder type
        valid_folder_types = {"images": "images", "videos": "videos", "documents": "documents"}
        resolved_folder_type = valid_folder_types.get(folder_type, "images")

        # Get or create the target system folder
        FolderService.ensure_system_folders(member_state, request.user)
        folder = MediaFolder.objects.filter(
            member_state=member_state,
            folder_type=resolved_folder_type,
            is_deleted=False,
        ).first()

        if not folder:
            return JsonResponse({"success": False, "error": "Upload folder not found."}, status=500)

        try:
            media_file = FileService.upload_file(
                file=file,
                folder=folder,
                name=file.name,
                user=request.user,
            )
            return JsonResponse(
                {
                    "success": True,
                    "file": {
                        "id": media_file.id,
                        "name": media_file.name,
                        "file_type": media_file.file_type,
                        "size_display": media_file.get_display_size(),
                        "url": media_file.cloudinary_secure_url,
                        "thumbnail": media_file.get_thumbnail(),
                        "uploaded_at": media_file.uploaded_at.strftime("%d %b %Y"),
                    },
                }
            )
        except ValidationError as e:
            return JsonResponse({"success": False, "error": "; ".join(e.messages)}, status=400)
