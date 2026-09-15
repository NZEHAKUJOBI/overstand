import json
import logging
import time

import cloudinary.utils

logger = logging.getLogger(__name__)
"""
Member State Profile Views - Updated with File Upload Support
===============================================================

Handles profile editing with integrated Cloudinary file uploads.
"""

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView, UpdateView, View

from dashboard.forms import BasicInfoForm, EconomicDataForm, InvestmentIncentiveForm, SEOSettingsForm
from dashboard.mixins import CanEditProfileMixin, IPAStaffRequiredMixin
from media_app.models import MediaFile
from media_app.services.cloudinary_service import CloudinaryService
from media_app.services.file_service import FileService
from members.models import InvestmentIncentive, MemberStateIPA


def _resolve_media_file_id(raw_id, member_state):
    """Return validated MediaFile PK only if it belongs to this member state."""
    try:
        pk = int(raw_id)
    except (ValueError, TypeError):
        return None
    if MediaFile.objects.filter(pk=pk, member_state=member_state, is_deleted=False).exists():
        return pk
    return None


class ProfileOverviewView(IPAStaffRequiredMixin, TemplateView):
    """Profile overview with completion tracking and statistics"""

    template_name = "dashboard/members/profile/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.request.user.ipa_profile.member_state
        context["member_state"] = member_state

        # Calculate counts for header stats
        context["opportunities_count"] = member_state.opportunities.count()
        context["sectors_count"] = member_state.sectors.count()
        context["team_members_count"] = member_state.ipa_users.filter(is_active=True).count()

        # Profile completion — canonical source is MemberStateIPA.get_profile_completion()
        completion = member_state.get_profile_completion()
        context["profile_completion"] = completion

        # Checklist flags derived from the canonical completion items
        completed_names = {item["name"] for item in completion["items"] if item["completed"]}
        context["has_basic_info"] = "Basic Information" in completed_names
        context["has_sectors"] = "Priority Sectors" in completed_names
        context["has_published_opportunities"] = "Published Opportunities" in completed_names
        context["has_hero_image"] = "Hero Image" in completed_names
        context["has_logo"] = "IPA Logo" in completed_names

        return context


class BasicInfoUpdateView(CanEditProfileMixin, UpdateView):
    """Edit basic profile information with file upload support"""

    model = MemberStateIPA
    form_class = BasicInfoForm
    template_name = "dashboard/members/profile/basic.html"
    # success_url = reverse_lazy("dashboard:country:profile")

    def get_object(self):
        return self.request.user.ipa_profile.member_state

    def get_success_url(self):
        """Redirect to member state dashboard"""
        return reverse(
            "dashboard:country:profile",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_completion"] = self.get_object().get_profile_completion()
        member_state = self.request.user.ipa_profile.member_state
        context["member_state"] = member_state
        return context

    def form_valid(self, form):
        """Handle form submission with file uploads"""
        member_state = form.save(commit=False)

        folder_path = f"ipawas/{member_state.slug}"
        allowed_image_mimes = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"]
        allowed_pdf_mimes = ["application/pdf", "application/x-pdf"]

        # Media library picker FKs (take priority over direct file uploads)
        for post_key in ("ipa_logo_file_id", "hero_image_file_id", "card_image_file_id"):
            fk = _resolve_media_file_id(self.request.POST.get(post_key), member_state)
            if fk:
                setattr(member_state, post_key, fk)

        # Direct file uploads (only when no picker FK supplied for that field)
        direct_uploads = {
            "logo": ("ipa_logo", "image", "ipa_logo_file_id"),
            "hero_image": ("hero_image", "image", "hero_image_file_id"),
            "card_image": ("card_image", "image", "card_image_file_id"),
            "investment_guide_pdf": ("investment_guide_pdf", "raw", None),
            "doing_business_pdf": ("doing_business_pdf", "raw", None),
        }

        for form_field, (model_field, resource_type, picker_key) in direct_uploads.items():
            # Skip direct upload when picker was used for this field
            if picker_key and self.request.POST.get(picker_key):
                continue
            file = self.request.FILES.get(form_field)
            if not file:
                continue
            if resource_type == "image" and file.content_type not in allowed_image_mimes:
                messages.error(
                    self.request,
                    f"{form_field.replace('_', ' ').title()}: Invalid file type. Allowed: JPEG, PNG, GIF, WebP",
                )
                continue
            if resource_type == "raw" and file.content_type not in allowed_pdf_mimes:
                messages.error(
                    self.request,
                    f"{form_field.replace('_', ' ').title()}: Only PDF files are allowed",
                )
                continue
            result = CloudinaryService.upload_file(
                file, f"{folder_path}/profile", resource_type=resource_type
            )
            if result["success"]:
                setattr(member_state, model_field, result["data"]["secure_url"])
                messages.success(
                    self.request,
                    f"{form_field.replace('_', ' ').title()} uploaded successfully",
                )
            else:
                messages.error(
                    self.request,
                    f"Failed to upload {form_field.replace('_', ' ')}: {result.get('error')}",
                )

        member_state.save()
        cache.delete_many([
            f"member_state_{member_state.slug}",
            f"country_profile_{member_state.slug}",
            "home_page_data",
            "all_active_member_states",
        ])
        messages.success(self.request, "Profile information updated successfully!")
        return redirect(self.get_success_url())


class EconomicDataUpdateView(CanEditProfileMixin, UpdateView):
    """Edit economic indicators and demographic data"""

    model = MemberStateIPA
    form_class = EconomicDataForm
    template_name = "dashboard/members/profile/economic.html"

    def get_object(self):
        return self.request.user.ipa_profile.member_state

    def get_success_url(self):
        return reverse(
            "dashboard:country:profile",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.request.user.ipa_profile.member_state
        context["member_state"] = member_state
        return context

    def form_valid(self, form):
        member_state = form.save()
        cache.delete_many([
            f"member_state_{member_state.slug}",
            f"country_profile_{member_state.slug}",
            "home_page_data",
            "all_active_member_states",
        ])
        messages.success(self.request, "Economic data updated successfully!")
        return redirect(self.get_success_url())


# class MediaGalleryView(CanEditProfileMixin, TemplateView):
#     """Manage media gallery (images and videos)"""

#     template_name = "dashboard/members/profile/media.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         member_state = self.request.user.ipa_profile.member_state

#         # Get images and videos from media app
#         from media_app.models import MediaFile
#         from media_app.services.file_service import FileService

#         context["images"] = MediaFile.objects.filter(
#             member_state=member_state, file_type="image", is_deleted=False
#         ).order_by("-uploaded_at")[:20]

#         context["videos"] = MediaFile.objects.filter(
#             member_state=member_state, file_type="video", is_deleted=False
#         ).order_by("-uploaded_at")[:10]

#         # Get storage statistics
#         storage_stats = FileService.get_storage_stats(member_state)
#         context["total_files"] = storage_stats.get("total_files", 0)
#         context["images_count"] = storage_stats.get("images_count", 0)
#         context["videos_count"] = storage_stats.get("videos_count", 0)
#         context["storage_used"] = storage_stats.get("total_size_display", "0 MB")

#         context["member_state"] = member_state

#         return context


class MediaGalleryView(CanEditProfileMixin, TemplateView):
    """Manage media gallery with upload support"""

    template_name = "dashboard/members/profile/media.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.request.user.ipa_profile.member_state

        # Get recent images and videos
        context["images"] = MediaFile.objects.filter(
            member_state=member_state, file_type="image", is_deleted=False
        ).order_by("-uploaded_at")[:12]

        context["videos"] = MediaFile.objects.filter(
            member_state=member_state, file_type="video", is_deleted=False
        ).order_by("-uploaded_at")[:6]

        # Get storage statistics
        try:
            storage_stats = FileService.get_storage_stats(member_state)
            context["total_files"] = storage_stats.get("total_files", 0)
            context["images_count"] = storage_stats.get("images_count", 0)
            context["videos_count"] = storage_stats.get("videos_count", 0)
            context["storage_used"] = storage_stats.get("total_size_display", "0 MB")
        except Exception:
            # Fallback if FileService not available
            context["total_files"] = context["images"].count() + context["videos"].count()
            context["images_count"] = context["images"].count()
            context["videos_count"] = context["videos"].count()
            context["storage_used"] = "0 MB"

        context["member_state"] = member_state
        return context

    def post(self, request, *args, **kwargs):
        """Handle file upload"""
        member_state = request.user.ipa_profile.member_state
        files = request.FILES.getlist("files")

        if not files:
            messages.error(request, "No files selected")
            return redirect(request.path)

        # Get or create media folder
        try:
            from media_app.models import MediaFolder

            folder = MediaFolder.objects.filter(
                member_state=member_state, folder_type="images", is_deleted=False
            ).first()

            if not folder:
                # Create default folder
                folder = MediaFolder.objects.create(
                    member_state=member_state,
                    name="Profile Media",
                    folder_type="custom",
                    cloudinary_folder=f"ipawas/{member_state.slug}/profile-media",
                    created_by=request.user,
                )
        except Exception:
            # Simple fallback without folder
            folder = None

        # Upload files
        successful = 0
        failed = 0

        for file in files:
            try:
                # Use FileService if available
                if folder:
                    FileService.upload_file(
                        file=file, folder=folder, name=file.name, user=request.user
                    )
                else:
                    # Simple direct upload to Cloudinary
                    result = CloudinaryService.upload_file(
                        file, f"ipawas/{member_state.slug}/media", resource_type="auto"
                    )

                    if result["success"]:
                        # Create MediaFile record manually
                        file_type = "image" if file.content_type.startswith("image") else "video"
                        MediaFile.objects.create(
                            member_state=member_state,
                            name=file.name,
                            original_filename=file.name,
                            file_type=file_type,
                            mime_type=file.content_type,
                            size_bytes=file.size,
                            cloudinary_public_id=result["data"]["public_id"],
                            cloudinary_resource_type=result["data"]["resource_type"],
                            cloudinary_url=result["data"]["url"],
                            cloudinary_secure_url=result["data"]["secure_url"],
                            uploaded_by=request.user,
                        )

                successful += 1
            except Exception as e:
                failed += 1
                logger.exception("File upload error: %s", e)

        # Show results
        if successful > 0:
            messages.success(
                request,
                f"{successful} file(s) uploaded successfully"
                + (f" ({failed} failed)" if failed > 0 else ""),
            )
        elif failed > 0:
            messages.error(request, f"Failed to upload {failed} file(s)")

        return redirect(request.path)


class SEOSettingsView(CanEditProfileMixin, UpdateView):
    """Configure SEO settings and meta tags"""

    model = MemberStateIPA
    form_class = SEOSettingsForm
    template_name = "dashboard/members/profile/seo.html"

    def get_object(self):
        return self.request.user.ipa_profile.member_state

    def get_success_url(self):
        return reverse(
            "dashboard:country:profile",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def form_valid(self, form):
        member_state = form.save(commit=False)

        # Handle OG image upload if provided
        og_image = self.request.FILES.get("og_image")
        if og_image:
            folder_path = f"ipawas/{member_state.slug}/seo"
            result = CloudinaryService.upload_file(og_image, folder_path, resource_type="image")
            if result["success"]:
                member_state.og_image_url = result["data"]["secure_url"]
                messages.success(self.request, "OG image uploaded successfully")
            else:
                messages.error(self.request, f"Failed to upload OG image: {result.get('error')}")

        member_state.save()
        cache.delete_many([
            f"member_state_{member_state.slug}",
            f"country_profile_{member_state.slug}",
            "home_page_data",
            "all_active_member_states",
        ])
        messages.success(self.request, "SEO settings updated successfully!")
        return redirect(self.get_success_url())


class ResourcesUpdateView(CanEditProfileMixin, TemplateView):
    """Upload and manage investment resource documents"""

    template_name = "dashboard/members/profile/resources.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def post(self, request, *args, **kwargs):
        """Handle document uploads"""
        member_state = request.user.ipa_profile.member_state

        # Define document fields and their configs
        documents = {
            "investment_guide_pdf": {
                "field": "investment_guide_pdf",
                "name": "Investment Guide",
                "folder": f"ipawas/{member_state.slug}/resources",
            },
            "doing_business_pdf": {
                "field": "doing_business_pdf",
                "name": "Doing Business Guide",
                "folder": f"ipawas/{member_state.slug}/resources",
            },
            "sector_profiles_pdf": {
                "field": "sector_profiles_pdf",
                "name": "Sector Profiles",
                "folder": f"ipawas/{member_state.slug}/resources",
            },
            "incentives_brochure_pdf": {
                "field": "incentives_brochure_pdf",
                "name": "Incentives Brochure",
                "folder": f"ipawas/{member_state.slug}/resources",
            },
            # "legal_framework_pdf": {
            #     "field": "legal_framework_pdf",
            #     "name": "Legal Framework",
            #     "folder": f"ipawas/{member_state.slug}/resources",
            # },
            # "infrastructure_report_pdf": {
            #     "field": "infrastructure_report_pdf",
            #     "name": "Infrastructure Report",
            #     "folder": f"ipawas/{member_state.slug}/resources",
            # },
        }

        uploaded_count = 0

        # Process each uploaded file
        for field_name, config in documents.items():
            file = request.FILES.get(field_name)

            if file:
                try:
                    # Validate file type by extension and MIME type
                    allowed_pdf_mimes = ["application/pdf", "application/x-pdf"]
                    if not file.name.lower().endswith(".pdf") or file.content_type not in allowed_pdf_mimes:
                        messages.warning(request, f'{config["name"]}: Only PDF files are allowed')
                        continue

                    # Validate file size (50MB max)
                    max_size = 50 * 1024 * 1024  # 50MB in bytes
                    if file.size > max_size:
                        messages.warning(request, f'{config["name"]}: File too large (max 50MB)')
                        continue

                    # Upload to Cloudinary
                    result = CloudinaryService.upload_file(
                        file, config["folder"], resource_type="raw"  # For PDFs
                    )

                    if result["success"]:
                        # Update member_state with secure URL
                        setattr(member_state, config["field"], result["data"]["secure_url"])
                        uploaded_count += 1

                        messages.success(request, f'{config["name"]} uploaded successfully')
                    else:
                        messages.error(
                            request,
                            f'{config["name"]}: Upload failed - {result.get("error", "Unknown error")}',
                        )

                except Exception as e:
                    messages.error(request, f'{config["name"]}: Upload error - {str(e)}')

        # Save member_state if any files were uploaded
        if uploaded_count > 0:
            member_state.save()
            messages.success(request, f"Successfully uploaded {uploaded_count} document(s)")
        elif not request.FILES:
            messages.info(request, "No files selected for upload")

        return redirect(request.path)


class ResourceUploadSignatureView(CanEditProfileMixin, View):
    """
    Return a Cloudinary signed-upload payload so the browser can upload
    PDFs directly to Cloudinary — bypassing the Django server entirely.
    This avoids Heroku's 30-second request timeout for large files.
    """

    VALID_FIELDS = frozenset({
        "investment_guide_pdf",
        "doing_business_pdf",
        "sector_profiles_pdf",
        "incentives_brochure_pdf",
    })

    def get(self, request, *args, **kwargs):
        field_name = request.GET.get("field", "").strip()
        if field_name not in self.VALID_FIELDS:
            return JsonResponse({"error": "Invalid field name"}, status=400)

        member_state = request.user.ipa_profile.member_state
        folder = f"ipawas/{member_state.slug}/resources"

        CloudinaryService.initialize()
        timestamp = int(time.time())
        # resource_type must NOT be included in the signature — Cloudinary excludes it
        # (along with file, cloud_name, api_key) when computing the expected signature.
        # Including it here causes a signature mismatch and Cloudinary rejects the upload.
        params_to_sign = {
            "folder": folder,
            "timestamp": timestamp,
        }
        signature = cloudinary.utils.api_sign_request(
            params_to_sign, settings.CLOUDINARY_API_SECRET
        )

        return JsonResponse(
            {
                "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
                "api_key": settings.CLOUDINARY_API_KEY,
                "timestamp": timestamp,
                "signature": signature,
                "folder": folder,
                "resource_type": "raw",
            }
        )


class ResourceSaveDocumentUrlView(CanEditProfileMixin, View):
    """
    Save the Cloudinary secure URL that the browser sends back after a
    successful direct upload. Only stores validated cloudinary.com URLs.
    """

    VALID_FIELDS = frozenset({
        "investment_guide_pdf",
        "doing_business_pdf",
        "sector_profiles_pdf",
        "incentives_brochure_pdf",
    })

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid request body"}, status=400)

        field_name = data.get("field", "").strip()
        secure_url = data.get("url", "").strip()

        if field_name not in self.VALID_FIELDS:
            return JsonResponse({"error": "Invalid field name"}, status=400)

        if not secure_url.startswith("https://res.cloudinary.com/"):
            return JsonResponse({"error": "Invalid Cloudinary URL"}, status=400)

        member_state = request.user.ipa_profile.member_state
        setattr(member_state, field_name, secure_url)
        member_state.save(update_fields=[field_name])

        logger.info(
            "Resource document saved: field=%s member_state=%s user=%s",
            field_name,
            member_state.slug,
            request.user.email,
        )
        return JsonResponse({"success": True, "url": secure_url})


class ResourceDeleteDocumentView(CanEditProfileMixin, View):
    """
    Clear a previously-uploaded resource document, leaving the field empty.
    Only clears the stored URL — does not attempt to remove the underlying
    Cloudinary asset (consistent with how a replacement upload already
    leaves the old asset in place, unreferenced).
    """

    VALID_FIELDS = frozenset({
        "investment_guide_pdf",
        "doing_business_pdf",
        "sector_profiles_pdf",
        "incentives_brochure_pdf",
    })

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid request body"}, status=400)

        field_name = data.get("field", "").strip()

        if field_name not in self.VALID_FIELDS:
            return JsonResponse({"error": "Invalid field name"}, status=400)

        member_state = request.user.ipa_profile.member_state
        setattr(member_state, field_name, "")
        member_state.save(update_fields=[field_name])

        logger.info(
            "Resource document removed: field=%s member_state=%s user=%s",
            field_name,
            member_state.slug,
            request.user.email,
        )
        return JsonResponse({"success": True})


class IncentivesView(CanEditProfileMixin, TemplateView):
    """List and manage investment incentives for this member state"""

    template_name = "dashboard/members/profile/incentives.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.request.user.ipa_profile.member_state
        context["member_state"] = member_state
        context["incentives"] = InvestmentIncentive.objects.filter(
            member_state=member_state
        ).prefetch_related("applicable_sectors").order_by("display_order", "title")
        context["form"] = InvestmentIncentiveForm()
        context["incentive_types"] = InvestmentIncentive.INCENTIVE_TYPES
        return context


class IncentiveCreateView(CanEditProfileMixin, View):
    """Create a new investment incentive via POST"""

    def post(self, request, *args, **kwargs):
        member_state = request.user.ipa_profile.member_state
        form = InvestmentIncentiveForm(request.POST)
        if form.is_valid():
            incentive = form.save(commit=False)
            incentive.member_state = member_state
            incentive.save()
            form.save_m2m()
            messages.success(request, f"Incentive '{incentive.title}' added successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        return redirect(
            reverse("dashboard:country:profile_incentives",
                    kwargs={"member_state_slug": member_state.slug})
        )


class IncentiveEditView(CanEditProfileMixin, View):
    """Edit an existing incentive via POST"""

    def post(self, request, pk, *args, **kwargs):
        member_state = request.user.ipa_profile.member_state
        incentive = get_object_or_404(InvestmentIncentive, pk=pk, member_state=member_state)
        form = InvestmentIncentiveForm(request.POST, instance=incentive)
        if form.is_valid():
            form.save()
            messages.success(request, f"Incentive '{incentive.title}' updated successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        return redirect(
            reverse("dashboard:country:profile_incentives",
                    kwargs={"member_state_slug": member_state.slug})
        )


class IncentiveDeleteView(CanEditProfileMixin, View):
    """Delete an incentive via POST"""

    def post(self, request, pk, *args, **kwargs):
        member_state = request.user.ipa_profile.member_state
        incentive = get_object_or_404(InvestmentIncentive, pk=pk, member_state=member_state)
        title = incentive.title
        incentive.delete()
        messages.success(request, f"Incentive '{title}' deleted.")
        return redirect(
            reverse("dashboard:country:profile_incentives",
                    kwargs={"member_state_slug": member_state.slug})
        )
