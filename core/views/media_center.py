"""
Knowledge Hub Frontend Views for Media Center
==============================================

Integrates with existing media_app.MediaFile system.
Public-facing views that filter and display media for external users.
"""

from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView, TemplateView

from knowledge_hub.models import MediaCategory, MediaCenterSubmission, MediaKitItem, NewsArticle, PressRelease, Tag, Topic
from media_app.models import MediaFile, MediaFolder

# ============================================================================
# MEDIA CENTER - MAIN HUB
# ============================================================================


class MediaCenterView(TemplateView):
    """
    Main Media Center hub with 4 tabs:
    - Press Releases
    - Photo Gallery
    - Video Library
    - Media Kit
    """

    template_name = "knowledge_hub/media_center.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Recent Press Releases (top 5) - approved only
        context["recent_press_releases"] = (
            PressRelease.objects.filter(status="approved")
            .select_related("pdf_file", "member_state")
            .order_by("-release_date")[:5]
        )

        # Photo Gallery - approved MediaCenterSubmissions
        context["featured_photos"] = (
            MediaCenterSubmission.objects.filter(status="approved", submission_type="photo")
            .select_related("media_file", "member_state")
            .order_by("-approved_at")[:12]
        )

        # Video Library - approved MediaCenterSubmissions
        context["featured_videos"] = (
            MediaCenterSubmission.objects.filter(status="approved", submission_type="video")
            .select_related("media_file", "member_state")
            .order_by("-approved_at")[:6]
        )

        # Media Kit Items
        context["media_kit_items"] = (
            MediaKitItem.objects.filter(is_active=True)
            .select_related("primary_file")
            .order_by("display_order", "-is_featured")[:8]
        )

        # Stats
        context["stats"] = {
            "total_photos": MediaCenterSubmission.objects.filter(status="approved", submission_type="photo").count(),
            "total_videos": MediaCenterSubmission.objects.filter(status="approved", submission_type="video").count(),
            "total_press_releases": PressRelease.objects.filter(status="approved").count(),
            "total_media_kit_items": MediaKitItem.objects.filter(is_active=True).count(),
        }

        return context


# ============================================================================
# PRESS RELEASES
# ============================================================================


class PressReleaseListView(ListView):
    """List all press releases with filtering."""

    model = PressRelease
    template_name = "knowledge_hub/press_releases.html"
    context_object_name = "press_releases"
    paginate_by = 15

    def get_queryset(self):
        qs = (
            PressRelease.objects.filter(published=True)
            .select_related("pdf_file")
            .prefetch_related("topics", "tags")
        )

        # Filter by year
        year = self.request.GET.get("year")
        if year:
            qs = qs.filter(release_date__year=year)

        # Filter by topic
        topic_slug = self.request.GET.get("topic")
        if topic_slug:
            qs = qs.filter(topics__slug=topic_slug)

        # Search
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(content__icontains=query))

        return qs.order_by("-release_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Available years
        context["available_years"] = PressRelease.objects.filter(published=True).dates(
            "release_date", "year", order="DESC"
        )

        # Topics
        context["topics"] = Topic.objects.filter(press_releases__published=True).distinct()

        return context


class PressReleaseDetailView(DetailView):
    """Individual press release detail."""

    model = PressRelease
    template_name = "knowledge_hub/press_release_detail.html"
    context_object_name = "press_release"

    def get_queryset(self):
        return (
            PressRelease.objects.filter(published=True)
            .select_related("pdf_file")
            .prefetch_related("media_assets", "topics", "tags")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Increment view count
        press_release = self.object
        press_release.view_count += 1
        press_release.save(update_fields=["view_count"])

        # Related press releases
        context["related_press_releases"] = (
            PressRelease.objects.filter(published=True, topics__in=press_release.topics.all())
            .exclude(pk=press_release.pk)
            .distinct()[:3]
        )

        return context


# ============================================================================
# PHOTO GALLERY
# ============================================================================


class PhotoGalleryView(ListView):
    """
    Photo gallery from MediaFile system.
    Displays public photos organized by MediaCategory.
    """

    template_name = "knowledge_hub/photo_gallery.html"
    context_object_name = "photos"
    paginate_by = 24

    def get_queryset(self):
        qs = MediaFile.objects.filter(
            file_type="image",
            is_deleted=False,
            # Add criteria for public display
            # Option 1: Use MediaCategory
            # public_categories__is_public=True
            # Option 2: Use specific folders
            # folder__folder_type='images'
        ).select_related("folder", "member_state")

        # Filter by category
        category_slug = self.request.GET.get("category")
        if category_slug:
            qs = qs.filter(public_categories__slug=category_slug)

        # Filter by member state
        country_slug = self.request.GET.get("country")
        if country_slug:
            qs = qs.filter(member_state__slug=country_slug)

        # Filter by year
        year = self.request.GET.get("year")
        if year:
            qs = qs.filter(uploaded_at__year=year)

        # Search
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(name__icontains=query)
                | Q(caption__icontains=query)
                | Q(alt_text__icontains=query)
            )

        return qs.order_by("-uploaded_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Photo categories
        context["categories"] = MediaCategory.objects.filter(
            is_public=True, category_type__in=["press_event", "leadership", "projects", "meetings"]
        ).annotate(photo_count=Count("media_files", filter=Q(media_files__file_type="image")))

        # Countries with photos
        context["countries"] = MemberStateIPA.objects.filter(
            media_files__file_type="image", media_files__is_deleted=False
        ).distinct()

        return context


class PhotoDetailView(DetailView):
    """Individual photo detail with metadata."""

    template_name = "knowledge_hub/photo_detail.html"
    context_object_name = "photo"

    def get_queryset(self):
        return MediaFile.objects.filter(file_type="image", is_deleted=False).select_related(
            "folder", "member_state", "uploaded_by"
        )

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])


# ============================================================================
# VIDEO LIBRARY
# ============================================================================


class VideoLibraryView(ListView):
    """Video library from MediaFile system."""

    template_name = "knowledge_hub/video_library.html"
    context_object_name = "videos"
    paginate_by = 12

    def get_queryset(self):
        qs = MediaFile.objects.filter(
            file_type="video",
            is_deleted=False,
        ).select_related("folder", "member_state")

        # Filter by category
        category_slug = self.request.GET.get("category")
        if category_slug:
            qs = qs.filter(public_categories__slug=category_slug)

        # Filter by year
        year = self.request.GET.get("year")
        if year:
            qs = qs.filter(uploaded_at__year=year)

        # Search
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(caption__icontains=query))

        return qs.order_by("-uploaded_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Video categories
        context["categories"] = MediaCategory.objects.filter(
            is_public=True, category_type__in=["promotional", "documentary", "press_event"]
        ).annotate(video_count=Count("media_files", filter=Q(media_files__file_type="video")))

        return context


class VideoDetailView(DetailView):
    """Individual video detail with player."""

    template_name = "knowledge_hub/video_detail.html"
    context_object_name = "video"

    def get_queryset(self):
        return MediaFile.objects.filter(file_type="video", is_deleted=False).select_related(
            "folder", "member_state"
        )

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])


# ============================================================================
# MEDIA KIT
# ============================================================================


class MediaKitView(ListView):
    """Downloadable media kit with logos, photos, guidelines."""

    model = MediaKitItem
    template_name = "knowledge_hub/media_kit.html"
    context_object_name = "media_kit_items"

    def get_queryset(self):
        return (
            MediaKitItem.objects.filter(is_active=True)
            .select_related("primary_file")
            .prefetch_related("additional_files")
            .order_by("display_order", "-is_featured")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Group by item type
        items = context["media_kit_items"]
        context["grouped_items"] = {}
        for item in items:
            item_type = item.get_item_type_display()
            if item_type not in context["grouped_items"]:
                context["grouped_items"][item_type] = []
            context["grouped_items"][item_type].append(item)

        return context


# ============================================================================
# DOWNLOAD HANDLERS
# ============================================================================


@require_http_methods(["POST"])
def download_press_release(request, pk):
    """Handle press release PDF download."""
    press_release = get_object_or_404(PressRelease, pk=pk, published=True)

    if press_release.pdf_file:
        # Increment counters
        press_release.download_count += 1
        press_release.save(update_fields=["download_count"])

        # Redirect to MediaFile download URL
        return JsonResponse(
            {"success": True, "download_url": press_release.pdf_file.get_download_url()}
        )

    return JsonResponse({"success": False, "error": "PDF not available"}, status=404)


@require_http_methods(["POST"])
def download_media_kit_item(request, pk):
    """Handle media kit item download."""
    item = get_object_or_404(MediaKitItem, pk=pk, is_active=True)

    # Increment counter
    item.download_count += 1
    item.save(update_fields=["download_count"])

    # Get all file URLs
    files = item.get_all_files()
    file_urls = [f.get_download_url() for f in files]

    return JsonResponse(
        {"success": True, "files": file_urls, "primary_file": item.primary_file.get_download_url()}
    )


@require_http_methods(["GET"])
def download_photo(request, pk):
    """Handle individual photo download."""
    photo = get_object_or_404(MediaFile, pk=pk, file_type="image", is_deleted=False)

    # Track download (optional)
    # You might want to add a download_count to MediaFile

    # Redirect to download URL
    return redirect(photo.get_download_url())


# ============================================================================
# AJAX ENDPOINTS
# ============================================================================


@method_decorator(cache_page(60 * 15), name="dispatch")  # Cache 15 minutes
class MediaStatsAjaxView(View):
    """Get media center statistics."""

    def get(self, request):
        stats = {
            "photos": {
                "total": MediaFile.objects.filter(file_type="image", is_deleted=False).count(),
                "by_category": {},
            },
            "videos": {
                "total": MediaFile.objects.filter(file_type="video", is_deleted=False).count(),
            },
            "press_releases": {
                "total": PressRelease.objects.filter(published=True).count(),
                "this_year": PressRelease.objects.filter(
                    published=True, release_date__year=timezone.now().year
                ).count(),
            },
        }

        return JsonResponse(stats)


class MediaSearchAjaxView(View):
    """Unified search across all media types."""

    def get(self, request):
        query = request.GET.get("q", "")
        media_type = request.GET.get("type", "all")  # all, photo, video, press

        results = {"photos": [], "videos": [], "press_releases": []}

        if not query:
            return JsonResponse(results)

        # Search photos
        if media_type in ["all", "photo"]:
            photos = MediaFile.objects.filter(
                Q(name__icontains=query)
                | Q(caption__icontains=query)
                | Q(alt_text__icontains=query),
                file_type="image",
                is_deleted=False,
            )[:10]

            results["photos"] = [
                {
                    "id": p.pk,
                    "name": p.name,
                    "thumbnail": p.get_thumbnail(),
                    "uploaded_at": p.uploaded_at.isoformat(),
                }
                for p in photos
            ]

        # Search videos
        if media_type in ["all", "video"]:
            videos = MediaFile.objects.filter(
                Q(name__icontains=query) | Q(caption__icontains=query),
                file_type="video",
                is_deleted=False,
            )[:10]

            results["videos"] = [
                {"id": v.pk, "name": v.name, "thumbnail": v.get_thumbnail(), "duration": v.duration}
                for v in videos
            ]

        # Search press releases
        if media_type in ["all", "press"]:
            press_releases = PressRelease.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query), published=True
            )[:10]

            results["press_releases"] = [
                {
                    "id": pr.pk,
                    "title": pr.title,
                    "release_date": pr.release_date.isoformat(),
                    "summary": pr.summary[:200],
                }
                for pr in press_releases
            ]

        return JsonResponse(results)
