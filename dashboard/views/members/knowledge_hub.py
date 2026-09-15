"""
Member State News Management Views
File: apps/dashboard/views/member_state/news.py

Views for member state staff to:
- List country-specific news
- Create news for their country
- Edit their news
- Delete their news
"""

import json

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.models import Sector
from dashboard.mixins import IPAStaffRequiredMixin, MemberStateAccessMixin
from knowledge_hub.models import NewsArticle, Tag, Topic
from media_app.models import MediaFile


class CountryNewsListView(IPAStaffRequiredMixin, MemberStateAccessMixin, ListView):
    """
    List news for specific member state.

    URL: /dashboard/<member-state-slug>/news/
    """

    model = NewsArticle
    template_name = "dashboard/members/news/news_list.html"
    context_object_name = "news_articles"
    paginate_by = 20

    def get_queryset(self):
        """Get news for this member state only"""
        member_state = self.request.member_state

        qs = (
            NewsArticle.objects.filter(member_state=member_state)
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
        member_state = self.request.member_state

        # Stats
        all_country_news = NewsArticle.objects.filter(member_state=member_state)
        context["total_count"] = all_country_news.count()
        context["published_count"] = all_country_news.filter(published=True).count()
        context["draft_count"] = all_country_news.filter(published=False).count()
        context["featured_count"] = all_country_news.filter(featured=True).count()

        # Filters
        context["categories"] = NewsArticle.CATEGORY_CHOICES
        context["current_category"] = self.request.GET.get("category", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")

        return context


class CountryNewsCreateView(IPAStaffRequiredMixin, MemberStateAccessMixin, CreateView):
    """
    Create new news article for member state.

    URL: /dashboard/<member-state-slug>/news/create/
    """

    model = NewsArticle
    template_name = "dashboard/members/news/news_editor.html"
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
        member_state = self.request.member_state

        # Available options
        context["categories"] = NewsArticle.CATEGORY_CHOICES
        context["tags"] = Tag.objects.all()
        context["topics"] = Topic.objects.all()
        context["sectors"] = Sector.objects.filter(is_active=True)

        # Media files for this member state only
        context["available_images"] = MediaFile.objects.filter(
            member_state=member_state, file_type="image", is_deleted=False
        ).order_by("-uploaded_at")[:50]

        # Editor mode
        context["is_edit"] = False
        context["is_hq"] = False
        context["member_state"] = member_state

        return context

    def form_valid(self, form):
        """Process form submission"""
        member_state = self.request.member_state

        # Set creator, member state, and scope
        form.instance.created_by = self.request.user
        form.instance.member_state = member_state
        form.instance.scope = "country"

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
                # Ensure media belongs to this member state
                form.instance.featured_media = MediaFile.objects.get(
                    id=featured_media_id, member_state=member_state
                )
            except MediaFile.DoesNotExist:
                messages.warning(
                    self.request, "Selected featured image not found or not accessible."
                )

        # Save article
        response = super().form_valid(form)

        # Handle M2M relationships

        # Supporting images (must belong to member state)
        supporting_image_ids = self.request.POST.getlist("supporting_images[]")
        if supporting_image_ids:
            supporting_images = MediaFile.objects.filter(
                id__in=supporting_image_ids,
                member_state=member_state,
                file_type="image",
                is_deleted=False,
            )
            form.instance.supporting_images.set(supporting_images)

        # Tags
        tag_names = self.request.POST.get("tags", "").split(",")
        tag_names = [name.strip() for name in tag_names if name.strip()]
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            form.instance.tags.add(tag)

        # Topics
        topic_ids = self.request.POST.getlist("topics[]")
        if topic_ids:
            form.instance.topics.set(topic_ids)

        # Related sectors
        sector_ids = self.request.POST.getlist("related_sectors[]")
        if sector_ids:
            form.instance.related_sectors.set(sector_ids)

        # Log activity
        from dashboard.utils.activity_logs_services import ActivityLogService

        ActivityLogService.log_activity(
            user=self.request.user,
            action_type="created_news",
            description=f"Created news article: {form.instance.title}",
            member_state=member_state,
        )

        messages.success(
            self.request, f'News article "{form.instance.title}" created successfully!'
        )

        return response

    def get_success_url(self):
        member_state_slug = self.request.member_state.slug
        if self.request.POST.get("action") == "save_and_continue":
            return reverse(
                "dashboard:country:news:edit",
                kwargs={"member_state_slug": member_state_slug, "pk": self.object.pk},
            )
        return reverse(
            "dashboard:country:news:list", kwargs={"member_state_slug": member_state_slug}
        )


class CountryNewsUpdateView(IPAStaffRequiredMixin, MemberStateAccessMixin, UpdateView):
    """
    Edit existing news article for member state.

    URL: /dashboard/<member-state-slug>/news/<pk>/edit/
    """

    model = NewsArticle
    template_name = "dashboard/members/news/news_editor.html"
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
        """Only news for this member state"""
        return NewsArticle.objects.filter(member_state=self.request.member_state)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object
        member_state = self.request.member_state

        # Available options
        context["categories"] = NewsArticle.CATEGORY_CHOICES
        context["tags"] = Tag.objects.all()
        context["topics"] = Topic.objects.all()
        context["sectors"] = Sector.objects.filter(is_active=True)

        # Current selections
        context["current_tags"] = list(article.tags.values_list("name", flat=True))
        context["current_topics"] = list(article.topics.values_list("id", flat=True))
        context["current_sectors"] = list(article.related_sectors.values_list("id", flat=True))
        context["current_supporting_images"] = article.get_supporting_images_list()

        # Content for editor
        context["content_html"] = article.content
        context["content_blocks"] = article.content_blocks

        # Media files for this member state only
        context["available_images"] = MediaFile.objects.filter(
            member_state=member_state, file_type="image", is_deleted=False
        ).order_by("-uploaded_at")[:50]

        # Editor mode
        context["is_edit"] = True
        context["is_hq"] = False
        context["member_state"] = member_state

        return context

    def form_valid(self, form):
        """Process form submission - similar to CreateView"""
        member_state = self.request.member_state

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
                form.instance.featured_media = MediaFile.objects.get(
                    id=featured_media_id, member_state=member_state
                )
            except MediaFile.DoesNotExist:
                pass
        elif self.request.POST.get("remove_featured_media"):
            form.instance.featured_media = None

        # Save article
        response = super().form_valid(form)

        # Handle M2M relationships

        # Supporting images
        supporting_image_ids = self.request.POST.getlist("supporting_images[]")
        if supporting_image_ids:
            supporting_images = MediaFile.objects.filter(
                id__in=supporting_image_ids,
                member_state=member_state,
                file_type="image",
                is_deleted=False,
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
        topic_ids = self.request.POST.getlist("topics[]")
        form.instance.topics.set(topic_ids if topic_ids else [])

        # Related sectors
        sector_ids = self.request.POST.getlist("related_sectors[]")
        form.instance.related_sectors.set(sector_ids if sector_ids else [])

        # Log activity
        from dashboard.utils.activity_logs_services import ActivityLogService

        ActivityLogService.log_activity(
            user=self.request.user,
            action_type="updated_news",
            description=f"Updated news article: {form.instance.title}",
            member_state=member_state,
        )

        messages.success(
            self.request, f'News article "{form.instance.title}" updated successfully!'
        )

        return response

    def get_success_url(self):
        member_state_slug = self.request.member_state.slug
        if self.request.POST.get("action") == "save_and_continue":
            return reverse(
                "dashboard:country:news:edit",
                kwargs={"member_state_slug": member_state_slug, "pk": self.object.pk},
            )
        return reverse(
            "dashboard:country:news:list", kwargs={"member_state_slug": member_state_slug}
        )


class CountryNewsDeleteView(IPAStaffRequiredMixin, MemberStateAccessMixin, DeleteView):
    """
    Delete news article for member state.

    URL: /dashboard/<member-state-slug>/news/<pk>/delete/
    """

    model = NewsArticle
    template_name = "dashboard/members/news/news_confirm_delete.html"

    def get_queryset(self):
        """Only news for this member state"""
        return NewsArticle.objects.filter(member_state=self.request.member_state)

    def delete(self, request, *args, **kwargs):
        article_title = self.get_object().title

        # Log activity
        from dashboard.utils.activity_logs_services import ActivityLogService

        ActivityLogService.log_activity(
            user=request.user,
            action_type="deleted_news",
            description=f"Deleted news article: {article_title}",
            member_state=request.member_state,
        )

        messages.success(request, f'News article "{article_title}" deleted successfully!')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "dashboard:country:news:list",
            kwargs={"member_state_slug": self.request.member_state.slug},
        )


# AJAX Views


class CountryNewsAutoSaveView(IPAStaffRequiredMixin, MemberStateAccessMixin, UpdateView):
    """
    Auto-save draft while editing.

    URL: /dashboard/<member-state-slug>/news/<pk>/autosave/
    """

    model = NewsArticle
    fields = ["title", "excerpt", "content"]

    def get_queryset(self):
        return NewsArticle.objects.filter(member_state=self.request.member_state)

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


class CountryNewsPreviewView(IPAStaffRequiredMixin, MemberStateAccessMixin, DetailView):
    """
    Preview news before publishing.

    URL: /dashboard/<member-state-slug>/news/<pk>/preview/
    """

    model = NewsArticle
    template_name = "news/news_detail.html"
    context_object_name = "article"

    def get_queryset(self):
        """Include unpublished news for preview"""
        return NewsArticle.objects.filter(member_state=self.request.member_state)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_preview"] = True
        context["preview_mode"] = True

        # Parse content blocks
        context["content_blocks"] = (
            self.object.content_blocks if isinstance(self.object.content_blocks, list) else []
        )

        context["supporting_images"] = self.object.get_supporting_images_list()

        return context


class CountryMediaPickerAPIView(IPAStaffRequiredMixin, MemberStateAccessMixin, View):
    """
    AJAX image picker for the member state news editor.
    Returns images scoped to the current member state.

    GET ?search=...&page=1
    URL: /dashboard/<member-state-slug>/news/media-picker/
    """

    PAGE_SIZE = 30

    def get(self, request, *args, **kwargs):
        member_state = request.member_state
        qs = MediaFile.objects.filter(
            file_type="image", is_deleted=False, member_state=member_state
        )

        search = request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(name__icontains=search)

        qs = qs.order_by("-uploaded_at")

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
            })

        return JsonResponse({
            "files": data,
            "total": total,
            "page": page,
            "has_next": (offset + self.PAGE_SIZE) < total,
        })
