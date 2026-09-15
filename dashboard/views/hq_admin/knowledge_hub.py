import json

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from core.models import Sector
from dashboard.mixins import IPAWASAdminRequiredMixin
from knowledge_hub.models import NewsArticle, Tag, Topic
from media_app.models import MediaFile
from members.models import MemberStateIPA


class HQNewsListView(IPAWASAdminRequiredMixin, ListView):
    """
    List all HQ/platform-wide news articles.

    URL: /dashboard/hq/news/
    """

    model = NewsArticle
    template_name = "dashboard/hq_admin/news/news_list.html"
    context_object_name = "news_articles"
    paginate_by = 20

    def get_queryset(self):
        """Get HQ news only (member_state is NULL)"""
        qs = (
            NewsArticle.objects.filter(member_state__isnull=True)
            .select_related("created_by", "featured_media")
            .prefetch_related("tags")
        )

        # Search
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(excerpt__icontains=query))

        # Status filter
        status = self.request.GET.get("status")
        if status == "published":
            qs = qs.filter(published=True)
        elif status == "draft":
            qs = qs.filter(published=False)

        # Category filter
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Stats
        all_hq_news = NewsArticle.objects.filter(member_state__isnull=True)
        context["total_count"] = all_hq_news.count()
        context["published_count"] = all_hq_news.filter(published=True).count()
        context["draft_count"] = all_hq_news.filter(published=False).count()
        context["featured_count"] = all_hq_news.filter(featured=True).count()

        # Filters
        context["categories"] = NewsArticle.CATEGORY_CHOICES
        context["current_category"] = self.request.GET.get("category", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")

        return context


class HQNewsCreateView(IPAWASAdminRequiredMixin, CreateView):
    """
    Create new HQ/platform-wide news article.

    URL: /dashboard/hq/news/create/
    """

    model = NewsArticle
    template_name = "dashboard/hq_admin/news/news_editor.html"
    fields = [
        "title",
        "excerpt",
        "category",
        "publication_date",
        "author",
        "author_title",
        "published",
        "featured",
    ]

    def get_initial(self):
        """Set default values"""
        return {
            "author": self.request.user.get_full_name() or self.request.user.username,
            "publication_date": timezone.now(),
            "published": False,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Available options
        context["categories"] = NewsArticle.CATEGORY_CHOICES
        context["tags"] = Tag.objects.all()
        context["topics"] = Topic.objects.all()
        context["member_states"] = MemberStateIPA.objects.filter(is_active=True)
        context["sectors"] = Sector.objects.filter(is_active=True)

        # Media files for selection
        context["available_images"] = MediaFile.objects.filter(
            file_type="image", is_deleted=False
        ).order_by("-uploaded_at")[:50]

        # Current selections (empty on create)
        context["current_tags"] = []
        context["current_topics"] = []
        context["current_countries"] = []
        context["current_sectors"] = []
        context["current_supporting_images"] = []

        # Editor mode
        context["is_edit"] = False
        context["is_hq"] = True

        return context

    def form_valid(self, form):
        """Process form submission"""
        # Set creator and scope
        form.instance.created_by = self.request.user
        form.instance.member_state = None  # HQ news
        form.instance.scope = "hq"

        # Parse content from editor
        content_html = self.request.POST.get("content_html", "")
        if content_html:
            from knowledge_hub.models import parse_html_to_blocks

            form.instance.content_blocks = parse_html_to_blocks(content_html)
            form.instance.content = content_html  # Keep legacy field populated

        # Handle featured media
        featured_media_id = self.request.POST.get("featured_media_id")
        if featured_media_id:
            try:
                form.instance.featured_media = MediaFile.objects.get(id=featured_media_id)
            except MediaFile.DoesNotExist:
                pass

        # Save article
        response = super().form_valid(form)

        # Handle M2M relationships

        # Supporting images — template sends a single JSON-encoded array
        raw_supporting = self.request.POST.get("supporting_images", "")
        try:
            supporting_image_ids = json.loads(raw_supporting) if raw_supporting else []
        except (ValueError, TypeError):
            supporting_image_ids = []
        if supporting_image_ids:
            supporting_images = MediaFile.objects.filter(
                id__in=supporting_image_ids, file_type="image", is_deleted=False
            )
            form.instance.supporting_images.set(supporting_images)

        # Tags
        tag_names = self.request.POST.get("tags", "").split(",")
        tag_names = [name.strip() for name in tag_names if name.strip()]
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            form.instance.tags.add(tag)

        # Topics
        topic_ids = self.request.POST.getlist("topics")
        if topic_ids:
            form.instance.topics.set(topic_ids)

        # Related countries
        country_ids = self.request.POST.getlist("related_countries")
        if country_ids:
            form.instance.related_countries.set(country_ids)

        # Related sectors
        sector_ids = self.request.POST.getlist("related_sectors")
        if sector_ids:
            form.instance.related_sectors.set(sector_ids)

        messages.success(
            self.request, f'News article "{form.instance.title}" created successfully!'
        )

        return response

    def get_success_url(self):
        if self.request.POST.get("action") == "save_and_continue":
            return reverse("dashboard:hq:news:edit", kwargs={"pk": self.object.pk})
        return reverse("dashboard:hq:news:list")


class HQNewsUpdateView(IPAWASAdminRequiredMixin, UpdateView):
    """
    Edit existing HQ news article.

    URL: /dashboard/hq/news/<pk>/edit/
    """

    model = NewsArticle
    template_name = "dashboard/hq_admin/news/news_editor.html"
    fields = [
        "title",
        "excerpt",
        "category",
        "publication_date",
        "author",
        "author_title",
        "published",
        "featured",
    ]

    def get_queryset(self):
        """Only HQ news"""
        return NewsArticle.objects.filter(member_state__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        # Available options
        context["categories"] = NewsArticle.CATEGORY_CHOICES
        context["tags"] = Tag.objects.all()
        context["topics"] = Topic.objects.all()
        context["member_states"] = MemberStateIPA.objects.filter(is_active=True)
        context["sectors"] = Sector.objects.filter(is_active=True)

        # Current selections
        context["current_tags"] = list(article.tags.values_list("name", flat=True))
        context["current_topics"] = list(article.topics.values_list("id", flat=True))
        context["current_countries"] = list(article.related_countries.values_list("id", flat=True))
        context["current_sectors"] = list(article.related_sectors.values_list("id", flat=True))
        context["current_supporting_images"] = article.get_supporting_images_list()

        # Content for editor
        context["content_html"] = article.content
        context["content_blocks"] = article.content_blocks

        # Media files
        context["available_images"] = MediaFile.objects.filter(
            file_type="image", is_deleted=False
        ).order_by("-uploaded_at")[:50]

        # Editor mode
        context["is_edit"] = True
        context["is_hq"] = True

        return context

    def form_valid(self, form):
        """Process form submission - similar to CreateView"""
        # Parse content from editor
        content_html = self.request.POST.get("content_html", "")
        if content_html:
            from knowledge_hub.models import parse_html_to_blocks

            form.instance.content_blocks = parse_html_to_blocks(content_html)
            form.instance.content = content_html

        # Handle featured media
        featured_media_id = self.request.POST.get("featured_media_id")
        if featured_media_id:
            try:
                form.instance.featured_media = MediaFile.objects.get(id=featured_media_id)
            except MediaFile.DoesNotExist:
                pass
        elif self.request.POST.get("remove_featured_media"):
            form.instance.featured_media = None

        # Save article
        response = super().form_valid(form)

        # Handle M2M relationships (same as CreateView)

        # Supporting images — template sends a single JSON-encoded array
        raw_supporting = self.request.POST.get("supporting_images", "")
        try:
            supporting_image_ids = json.loads(raw_supporting) if raw_supporting else []
        except (ValueError, TypeError):
            supporting_image_ids = []
        if supporting_image_ids:
            supporting_images = MediaFile.objects.filter(
                id__in=supporting_image_ids, file_type="image", is_deleted=False
            )
            form.instance.supporting_images.set(supporting_images)
        else:
            form.instance.supporting_images.clear()

        # Tags
        form.instance.tags.clear()
        tag_names = self.request.POST.get("tags", "").split(",")
        tag_names = [name.strip() for name in tag_names if name.strip()]
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            form.instance.tags.add(tag)

        # Topics
        topic_ids = self.request.POST.getlist("topics")
        form.instance.topics.set(topic_ids if topic_ids else [])

        # Related countries
        country_ids = self.request.POST.getlist("related_countries")
        form.instance.related_countries.set(country_ids if country_ids else [])

        # Related sectors
        sector_ids = self.request.POST.getlist("related_sectors")
        form.instance.related_sectors.set(sector_ids if sector_ids else [])

        messages.success(
            self.request, f'News article "{form.instance.title}" updated successfully!'
        )

        return response

    def get_success_url(self):
        if self.request.POST.get("action") == "save_and_continue":
            return reverse("dashboard:hq:news:edit", kwargs={"pk": self.object.pk})
        return reverse("dashboard:hq:news:list")


class HQNewsDeleteView(IPAWASAdminRequiredMixin, DeleteView):
    """
    Delete HQ news article.

    URL: /dashboard/hq/news/<pk>/delete/
    """

    model = NewsArticle
    template_name = "dashboard/hq_admin/news/news_confirm_delete.html"
    success_url = reverse_lazy("dashboard:hq:news:list")

    def get_queryset(self):
        """Only HQ news"""
        return NewsArticle.objects.filter(member_state__isnull=True)

    def form_valid(self, form):
        messages.success(self.request, "News article deleted successfully!")
        return super().form_valid(form)


# AJAX Views for Editor


class HQNewsAutoSaveView(IPAWASAdminRequiredMixin, UpdateView):
    """
    Auto-save draft while editing.
    Returns JSON response.

    URL: /dashboard/hq/news/<pk>/autosave/
    """

    model = NewsArticle
    fields = ["title", "excerpt", "content"]

    def get_queryset(self):
        return NewsArticle.objects.filter(member_state__isnull=True)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            data = json.loads(request.body)

            # Update fields
            if "title" in data:
                self.object.title = data["title"]
            if "excerpt" in data:
                self.object.excerpt = data["excerpt"]
            if "content_html" in data:
                self.object.content = data["content_html"]

            self.object.save()

            return JsonResponse(
                {"success": True, "saved_at": timezone.now().isoformat(), "message": "Draft saved"}
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class HQNewsPreviewView(IPAWASAdminRequiredMixin, DetailView):
    """
    Preview news before publishing.

    URL: /dashboard/hq/news/<pk>/preview/
    """

    model = NewsArticle
    template_name = "knowledge_hub/news_detail.html"
    context_object_name = "article"

    def get_queryset(self):
        """Include unpublished news for preview"""
        return NewsArticle.objects.filter(member_state__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        context["is_preview"] = True
        context["preview_mode"] = True

        # Parse content blocks
        context["content_blocks"] = (
            article.content_blocks if isinstance(article.content_blocks, list) else []
        )

        context["supporting_images"] = article.get_supporting_images_list()

        # Social share data (real URL not available in preview — use placeholder)
        context["share_url"] = self.request.build_absolute_uri()
        context["share_title"] = article.title
        context["share_excerpt"] = article.excerpt

        # Recent news sidebar (same category, exclude this one)
        context["recent_news"] = (
            NewsArticle.objects.filter(
                published=True,
                category=article.category,
                publication_date__lte=timezone.now(),
            )
            .exclude(pk=article.pk)
            .select_related("featured_media")
            .order_by("-publication_date")[:5]
        )

        # Previous / next navigation
        context["previous_article"] = (
            NewsArticle.objects.filter(
                published=True,
                publication_date__lt=article.publication_date,
            )
            .order_by("-publication_date")
            .first()
        )
        context["next_article"] = (
            NewsArticle.objects.filter(
                published=True,
                publication_date__gt=article.publication_date,
            )
            .order_by("publication_date")
            .first()
        )

        return context


class HQMediaPickerAPIView(IPAWASAdminRequiredMixin, View):
    """
    AJAX image picker for the HQ news editor.
    Returns images from all member states (HQ has global access).

    GET ?search=...&page=1&type=image
    URL: /dashboard/hq/news/media-picker/
    """

    PAGE_SIZE = 30

    def get(self, request, *args, **kwargs):
        qs = MediaFile.objects.filter(file_type="image", is_deleted=False)

        search = request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(name__icontains=search)

        qs = qs.select_related("member_state").order_by("-uploaded_at")

        try:
            page = max(1, int(request.GET.get("page", 1)))
        except (ValueError, TypeError):
            page = 1

        offset = (page - 1) * self.PAGE_SIZE
        total = qs.count()
        files = qs[offset: offset + self.PAGE_SIZE]

        data = []
        for f in files:
            data.append({
                "id": f.id,
                "name": f.name,
                "url": f.cloudinary_secure_url,
                "thumbnail": f.get_thumbnail(),
                "alt_text": f.alt_text or "",
                "caption": f.caption if hasattr(f, "caption") else "",
                "member_state": f.member_state.country_name if f.member_state else "HQ",
            })

        return JsonResponse({
            "files": data,
            "total": total,
            "page": page,
            "has_next": (offset + self.PAGE_SIZE) < total,
        })
