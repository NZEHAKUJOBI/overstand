"""Member State Opportunities Views"""

import logging

from django import forms as django_forms
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from core.models import Sector
from dashboard.mixins import CanCreateOpportunitiesMixin, IPAStaffRequiredMixin
from dashboard.utils.activity_logs_services import ActivityLogService
from media_app.models import MediaFile
from media_app.services.cloudinary_service import CloudinaryService
from opportunities.models import InvestmentOpportunity

logger = logging.getLogger(__name__)


def _resolve_media_file_id(raw_id, member_state):
    """Return validated MediaFile PK only if it belongs to this member state."""
    try:
        pk = int(raw_id)
    except (ValueError, TypeError):
        return None
    if MediaFile.objects.filter(pk=pk, member_state=member_state, is_deleted=False).exists():
        return pk
    return None


def _handle_file_uploads(view, opportunity, member_state, *, append_gallery=False):
    """
    Upload images for an opportunity.

    append_gallery=False (create): new gallery images replace any existing list.
    append_gallery=True  (edit):   new gallery images are appended to the existing list.
    """
    CloudinaryService.initialize()
    allowed = getattr(
        settings, "ALLOWED_IMAGE_TYPES", ["image/jpeg", "image/png", "image/gif", "image/webp"]
    )
    folder = f"ipawas/{member_state.country_code.lower()}/opportunities/{opportunity.pk}"
    updated = []

    # Thumbnail — picker FK takes priority over direct upload
    thumb_fk = _resolve_media_file_id(view.request.POST.get("thumbnail_image_file_id"), member_state)
    if thumb_fk:
        opportunity.thumbnail_image_file_id = thumb_fk
        updated.append("thumbnail_image_file")
    else:
        f = view.request.FILES.get("thumbnail_image")
        if f:
            if f.content_type not in allowed:
                messages.error(view.request, "Thumbnail: invalid file type. Allowed: JPEG, PNG, GIF, WebP.")
            else:
                result = CloudinaryService.upload_file(f, folder, resource_type="image")
                if result["success"]:
                    opportunity.thumbnail_image = result["data"]["secure_url"]
                    updated.append("thumbnail_image")

    # Hero image
    hero_fk = _resolve_media_file_id(view.request.POST.get("hero_image_file_id"), member_state)
    if hero_fk:
        opportunity.hero_image_file_id = hero_fk
        updated.append("hero_image_file")
    else:
        f = view.request.FILES.get("hero_image")
        if f:
            if f.content_type not in allowed:
                messages.error(view.request, "Hero image: invalid file type. Allowed: JPEG, PNG, GIF, WebP.")
            else:
                result = CloudinaryService.upload_file(f, folder, resource_type="image")
                if result["success"]:
                    opportunity.hero_image = result["data"]["secure_url"]
                    updated.append("hero_image")

    # Gallery images
    gallery_files = view.request.FILES.getlist("gallery_images")
    if gallery_files:
        urls = list(opportunity.gallery_images or []) if append_gallery else []
        for f in gallery_files:
            if f.content_type not in allowed:
                messages.error(view.request, f"Gallery '{f.name}': invalid file type.")
                continue
            result = CloudinaryService.upload_file(f, f"{folder}/gallery", resource_type="image")
            if result["success"]:
                urls.append(result["data"]["secure_url"])
        opportunity.gallery_images = urls
        updated.append("gallery_images")

    if updated:
        opportunity.save(update_fields=updated)


def _parse_coordinates(request):
    """
    Parse geo_lat / geo_lng from POST data.

    Returns:
      {"lat": float, "lng": float}  — both present and valid
      None                          — both empty (clear coordinates)
      "keep"                        — only one provided (sentinel: leave coordinates unchanged)
    """
    lat = request.POST.get("geo_lat", "").strip()
    lng = request.POST.get("geo_lng", "").strip()

    if lat and lng:
        try:
            return {"lat": float(lat), "lng": float(lng)}
        except ValueError:
            return "keep"
    elif not lat and not lng:
        return None
    else:
        return "keep"


class OpportunityListView(IPAStaffRequiredMixin, ListView):
    model = InvestmentOpportunity
    template_name = "dashboard/members/opportunities.html"
    context_object_name = "opportunities"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.request.user.ipa_profile.member_state
        context["member_state"] = member_state

        # Stats
        context["opportunities_count"] = member_state.opportunities.count()
        context["published_count"] = member_state.opportunities.filter(published=True).count()
        context["draft_count"] = member_state.opportunities.filter(published=False).count()
        context["featured_count"] = member_state.opportunities.filter(featured=True).count()

        # Sectors for filtering
        context["sectors"] = Sector.objects.all()

        return context

    def get_queryset(self):
        qs = (
            InvestmentOpportunity.objects.filter(
                primary_country=self.request.user.ipa_profile.member_state
            )
            .select_related("primary_sector")
            .order_by("-created_at")
        )

        # Apply filters
        search = self.request.GET.get("search")
        if search:
            qs = qs.filter(title__icontains=search)

        status = self.request.GET.get("status")
        valid_statuses = {"draft", "under_review", "active", "negotiation", "funded", "suspended", "cancelled"}
        if status == "published":
            qs = qs.filter(published=True)
        elif status == "draft":
            qs = qs.filter(published=False)
        elif status in valid_statuses:
            qs = qs.filter(status=status)

        sector = self.request.GET.get("sector")
        if sector:
            qs = qs.filter(primary_sector_id=sector)

        return qs


class OpportunityDetailView(IPAStaffRequiredMixin, DetailView):
    model = InvestmentOpportunity
    template_name = "dashboard/members/opportunities_detail.html"
    context_object_name = "opportunity"

    def get_queryset(self):
        return InvestmentOpportunity.objects.filter(
            primary_country=self.request.user.ipa_profile.member_state
        ).select_related("primary_sector")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context


class OpportunityCreateView(CanCreateOpportunitiesMixin, CreateView):
    model = InvestmentOpportunity
    template_name = "dashboard/members/opportunities_form.html"
    fields = [
        "title",
        "summary",
        "description",
        "opportunity_type",
        "project_stage",
        "priority_level",
        "primary_sector",
        "secondary_sectors",
        "sub_sector",
        "specific_location",
        "is_regional",
        "participating_countries",
        "start_date_target",
        "implementing_agency",
        "implementing_agency_contact",
        "investment_required_min",
        "investment_required_max",
        "expected_roi",
        "payback_period",
        "minimum_equity",
        "implementation_timeline",
        "revenue_projections",
        "investor_profile",
        "technical_requirements",
        "local_content_requirements",
        "market_analysis",
        "target_market",
        "financial_incentives_available",
        "regulatory_framework",
        "approval_process",
        "licenses_required",
        "land_availability",
        "risk_factors",
        "mitigation_measures",
        "video_url",
        "factsheet_url",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["start_date_target"].widget = django_forms.DateInput(attrs={"type": "date"})
        return form

    def get_success_url(self):
        return reverse(
            "dashboard:country:opportunities",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        context["sectors"] = Sector.objects.all()
        context["is_create"] = True
        context["geo_lat"] = ""
        context["geo_lng"] = ""
        return context

    def form_valid(self, form):
        member_state = self.request.user.ipa_profile.member_state
        form.instance.primary_country = member_state
        form.instance.created_by = self.request.user

        # Handle publish/draft/feature
        action = self.request.POST.get("action", "draft")
        if action == "publish":
            form.instance.status = "active"
            form.instance.published = True
            form.instance.published_date = timezone.now()
            form.instance.approved_by = self.request.user
            form.instance.approved_date = timezone.now()
        else:
            form.instance.status = "draft"
            form.instance.published = False

        # Handle featured checkbox
        form.instance.featured = "featured" in self.request.POST

        # Build geographic_coordinates JSON from lat/lng inputs
        coords = _parse_coordinates(self.request)
        if isinstance(coords, dict):
            form.instance.geographic_coordinates = coords
        # "keep" and None both leave coordinates unset on a new instance

        # Save the instance first to get the ID
        response = super().form_valid(form)

        # NOW handle file uploads to Cloudinary
        _handle_file_uploads(self, form.instance, member_state)

        # Activity log
        action_type = "published_opportunity" if form.instance.published else "created_opportunity"
        ActivityLogService.log_activity(
            user=self.request.user,
            action_type=action_type,
            description=f"Created opportunity: {form.instance.title}",
            member_state=member_state,
        )

        if form.instance.published:
            messages.success(
                self.request, f"✓ Opportunity '{form.instance.title}' created and published!"
            )
        else:
            messages.success(self.request, f"✓ Opportunity '{form.instance.title}' saved as draft.")

        return response


class OpportunityEditView(CanCreateOpportunitiesMixin, UpdateView):
    model = InvestmentOpportunity
    template_name = "dashboard/members/opportunities_form.html"
    fields = [
        "title",
        "summary",
        "description",
        "opportunity_type",
        "project_stage",
        "priority_level",
        "primary_sector",
        "secondary_sectors",
        "sub_sector",
        "specific_location",
        "is_regional",
        "participating_countries",
        "start_date_target",
        "implementing_agency",
        "implementing_agency_contact",
        "investment_required_min",
        "investment_required_max",
        "expected_roi",
        "payback_period",
        "minimum_equity",
        "implementation_timeline",
        "revenue_projections",
        "investor_profile",
        "technical_requirements",
        "local_content_requirements",
        "market_analysis",
        "target_market",
        "financial_incentives_available",
        "regulatory_framework",
        "approval_process",
        "licenses_required",
        "land_availability",
        "risk_factors",
        "mitigation_measures",
        "video_url",
        "factsheet_url",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["start_date_target"].widget = django_forms.DateInput(attrs={"type": "date"})
        return form

    def get_queryset(self):
        return InvestmentOpportunity.objects.filter(
            primary_country=self.request.user.ipa_profile.member_state
        )

    def get_success_url(self):
        return reverse(
            "dashboard:country:opportunities",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        context["sectors"] = Sector.objects.all()
        context["is_create"] = False
        coords = self.object.geographic_coordinates or {}
        context["geo_lat"] = coords.get("lat", "")
        context["geo_lng"] = coords.get("lng", "")
        return context

    def form_valid(self, form):
        # Handle publish/draft
        action = self.request.POST.get("action", "save")
        if action == "publish" and not form.instance.published:
            form.instance.status = "active"
            form.instance.published = True
            form.instance.published_date = timezone.now()
            form.instance.approved_by = self.request.user
            form.instance.approved_date = timezone.now()
        elif action == "draft":
            form.instance.status = "draft"
            form.instance.published = False

        # Handle featured checkbox
        form.instance.featured = "featured" in self.request.POST

        # Build geographic_coordinates JSON from lat/lng inputs
        coords = _parse_coordinates(self.request)
        if coords != "keep":
            form.instance.geographic_coordinates = coords

        # Save first
        response = super().form_valid(form)

        # Handle file uploads
        member_state = self.request.user.ipa_profile.member_state
        _handle_file_uploads(self, form.instance, member_state, append_gallery=True)

        messages.success(
            self.request, f"✓ Opportunity '{form.instance.title}' updated successfully!"
        )

        return response


class OpportunityPublishView(CanCreateOpportunitiesMixin, View):
    """Publish an opportunity"""

    def post(self, request, pk, member_state_slug):
        opportunity = get_object_or_404(
            InvestmentOpportunity, pk=pk, primary_country=request.user.ipa_profile.member_state
        )

        if not opportunity.published:
            opportunity.status = "active"
            opportunity.published = True
            opportunity.published_date = timezone.now()
            opportunity.approved_by = request.user
            opportunity.approved_date = timezone.now()
            opportunity.save()

            ActivityLogService.log_activity(
                user=request.user,
                action_type="published_opportunity",
                description=f"Published opportunity: {opportunity.title}",
                member_state=request.user.ipa_profile.member_state,
            )

            messages.success(request, f"✓ '{opportunity.title}' published successfully!")
        else:
            messages.info(request, "This opportunity is already published.")

        # Return JSON for AJAX or redirect for form
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "published": opportunity.published})

        return redirect("dashboard:country:opportunities", member_state_slug=member_state_slug)


class OpportunityUnpublishView(CanCreateOpportunitiesMixin, View):
    """Unpublish an opportunity"""

    def post(self, request, pk, member_state_slug):
        opportunity = get_object_or_404(
            InvestmentOpportunity, pk=pk, primary_country=request.user.ipa_profile.member_state
        )

        if opportunity.published:
            opportunity.status = "draft"
            opportunity.published = False
            opportunity.save()

            ActivityLogService.log_activity(
                user=request.user,
                action_type="unpublished_opportunity",
                description=f"Unpublished opportunity: {opportunity.title}",
                member_state=request.user.ipa_profile.member_state,
            )

            messages.success(request, f"✓ '{opportunity.title}' unpublished.")
        else:
            messages.info(request, "This opportunity is already unpublished.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "published": opportunity.published})

        return redirect("dashboard:country:opportunities", member_state_slug=member_state_slug)


class OpportunityToggleFeaturedView(CanCreateOpportunitiesMixin, View):
    """Toggle featured status"""

    def post(self, request, pk, member_state_slug):
        opportunity = get_object_or_404(
            InvestmentOpportunity, pk=pk, primary_country=request.user.ipa_profile.member_state
        )

        opportunity.featured = not opportunity.featured
        opportunity.save()

        action = "featured" if opportunity.featured else "unfeatured"
        ActivityLogService.log_activity(
            user=request.user,
            action_type=f"{action}_opportunity",
            description=f"{action.capitalize()} opportunity: {opportunity.title}",
            member_state=request.user.ipa_profile.member_state,
        )

        if opportunity.featured:
            messages.success(request, f"✓ '{opportunity.title}' is now featured!")
        else:
            messages.success(request, f"✓ '{opportunity.title}' removed from featured.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "featured": opportunity.featured})

        return redirect("dashboard:country:opportunities", member_state_slug=member_state_slug)


class OpportunityDeleteView(CanCreateOpportunitiesMixin, View):
    """Delete an opportunity (AJAX-enabled, no separate template needed)"""

    def post(self, request, pk, member_state_slug):
        opportunity = get_object_or_404(
            InvestmentOpportunity, pk=pk, primary_country=request.user.ipa_profile.member_state
        )

        title = opportunity.title

        # Optional: Delete images from Cloudinary
        self._cleanup_cloudinary_files(opportunity)

        opportunity.delete()

        ActivityLogService.log_activity(
            user=request.user,
            action_type="deleted_opportunity",
            description=f"Deleted opportunity: {title}",
            member_state=request.user.ipa_profile.member_state,
        )

        messages.success(request, f"✓ Opportunity '{title}' deleted successfully.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect("dashboard:country:opportunities", member_state_slug=member_state_slug)

    def _cleanup_cloudinary_files(self, opportunity):
        """Delete associated Cloudinary files (optional)"""
        try:
            CloudinaryService.initialize()

            # Delete thumbnail
            if opportunity.thumbnail_image:
                # Extract public_id from URL if needed
                pass

            # Delete hero image
            if opportunity.hero_image:
                pass

            # Delete gallery images
            if opportunity.gallery_images:
                pass

            # Or delete entire folder
            member_state = opportunity.primary_country
            folder_path = (
                f"ipawas/{member_state.country_code.lower()}/opportunities/{opportunity.pk}"
            )
            CloudinaryService.delete_folder(folder_path)

        except Exception as e:
            # Log error but don't fail deletion
            logger.exception("Error cleaning up Cloudinary files: %s", e)
