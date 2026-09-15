"""
Knowledge Hub Views - IPAWAS Frontend
======================================

Views for public-facing Knowledge Hub integrated with media_app.MediaFile.
"""

from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView, TemplateView

from core.models import Publication
from knowledge_hub.models import MediaCategory, NewsArticle, PressRelease, Resource, Tag, Topic
from media_app.models import MediaFile
from members.models import MemberStateIPA

# ============================================================================
# KNOWLEDGE HUB LANDING PAGE
# ============================================================================


class KnowledgeHubLandingView(TemplateView):
    """
    Main Knowledge Hub landing page with featured content and category cards.
    """

    template_name = "knowledge_hub/knowledge_hub_landing_2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Featured Publication
        context["featured_publication"] = (
            Publication.objects.filter(published=True, featured=True)
            .select_related("cover_media")
            .first()
        )

        # Recent Publications (for Publications tab)
        context["recent_publications"] = (
            Publication.objects.filter(published=True)
            .select_related("cover_media")
            .order_by("-publication_date")[:6]
        )

        # Recent News (for News tab)
        context["recent_news"] = (
            NewsArticle.objects.filter(published=True, category="investment_news")
            .select_related("featured_media")
            .order_by("-publication_date")[:6]
        )

        # Recent Blog Posts (for Blog tab)
        context["recent_blog"] = (
            NewsArticle.objects.filter(published=True, category="blog")
            .select_related("featured_media")
            .order_by("-publication_date")[:6]
        )

        # Recent Press Releases (for Press tab)
        context["recent_press"] = (
            PressRelease.objects.filter(published=True)
            .select_related("pdf_file")
            .order_by("-release_date")[:6]
        )

        # Latest Content (mixed - for All Content tab)
        context["latest_content"] = self.get_latest_mixed_content()

        # Statistics for category cards
        context["stats"] = {
            "publications_count": Publication.objects.filter(published=True).count(),
            "news_count": NewsArticle.objects.filter(published=True).count(),
            "press_releases_count": PressRelease.objects.filter(published=True).count(),
            "resources_count": Resource.objects.filter(published=True).count(),
            "contributors_count": (
                NewsArticle.objects.filter(published=True, created_by__isnull=False)
                .values("created_by")
                .distinct()
                .count()
            ),
            "photos_count": MediaFile.objects.filter(
                file_type="image", is_deleted=False, public_categories__is_public=True
            )
            .distinct()
            .count(),
            "videos_count": MediaFile.objects.filter(
                file_type="video", is_deleted=False, public_categories__is_public=True
            )
            .distinct()
            .count(),
        }

        # Trending topics
        context["trending_topics"] = Topic.objects.filter(content_count__gt=0).order_by(
            "-content_count"
        )[:15]

        return context

    def get_latest_mixed_content(self):
        """
        Get mixed latest content from Publications, News, and Press Releases.
        Returns a unified list sorted by date.

        Handles both date/datetime differences AND timezone-aware/naive differences.
        """
        from datetime import date, datetime

        from django.utils import timezone

        def normalize_date(date_obj):
            """
            Convert any date/datetime to timezone-aware datetime for consistent sorting.

            Handles:
            - datetime.date objects -> convert to datetime at midnight
            - timezone-naive datetime -> make timezone-aware
            - timezone-aware datetime -> return as-is
            - None values -> return very old date
            """
            if date_obj is None:
                return timezone.make_aware(datetime.min)

            # Convert date to datetime if needed
            if isinstance(date_obj, date) and not isinstance(date_obj, datetime):
                date_obj = datetime.combine(date_obj, datetime.min.time())

            # Ensure datetime is timezone-aware
            if isinstance(date_obj, datetime):
                if timezone.is_naive(date_obj):
                    return timezone.make_aware(date_obj)
                return date_obj

            # Fallback for unexpected types
            return timezone.make_aware(datetime.min)

        # Get recent items from each type
        publications = list(
            Publication.objects.filter(published=True)
            .select_related("cover_media")
            .order_by("-publication_date")[:3]
        )

        news_articles = list(
            NewsArticle.objects.filter(published=True)
            .select_related("featured_media")
            .order_by("-publication_date")[:3]
        )

        press_releases = list(
            PressRelease.objects.filter(published=True)
            .select_related("pdf_file")
            .order_by("-release_date")[:3]
        )

        # Normalize data structure for template
        items = []

        for pub in publications:
            items.append(
                {
                    "title": pub.title,
                    "excerpt": pub.description,
                    "date": pub.publication_date,
                    "date_normalized": normalize_date(pub.publication_date),
                    "url": f"/knowledge-hub/publications/{pub.slug}/",
                    "type_display": pub.get_publication_type_display(),
                    "featured_media": pub.cover_media,
                    "icon": "fas fa-file-pdf",
                    "gradient": "linear-gradient(135deg, #1B7A4C, #10B981)",
                    "stat_type": "downloads",
                    "stat_value": pub.download_count,
                }
            )

        for article in news_articles:
            items.append(
                {
                    "title": article.title,
                    "excerpt": article.excerpt,
                    "date": article.publication_date,
                    "date_normalized": normalize_date(article.publication_date),
                    "url": f"/knowledge-hub/news/{article.slug}/",
                    "type_display": article.get_category_display(),
                    "featured_media": article.featured_media,
                    "icon": "fas fa-newspaper",
                    "gradient": "linear-gradient(135deg, #059669, #34D399)",
                    "stat_type": "views",
                    "stat_value": article.view_count,
                }
            )

        for press in press_releases:
            items.append(
                {
                    "title": press.title,
                    "excerpt": press.summary,
                    "date": press.release_date,
                    "date_normalized": normalize_date(press.release_date),
                    "url": f"/media-center/press/{press.slug}/",
                    "type_display": "Press Release",
                    "featured_media": None,
                    "icon": "fas fa-bullhorn",
                    "gradient": "linear-gradient(135deg, #064E3B, #1B7A4C)",
                    "stat_type": "downloads",
                    "stat_value": press.download_count,
                }
            )

        # Sort by normalized date (most recent first)
        items.sort(key=lambda x: x["date_normalized"], reverse=True)

        return items[:9]  # Return top 9 items


# ============================================================================
# PUBLICATIONS
# ============================================================================


class PublicationsLibraryView(ListView):
    """Publications library with filtering."""

    model = Publication
    template_name = "knowledge_hub/publications_library.html"
    context_object_name = "publications"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Publication.objects.filter(published=True)
            .select_related("cover_media")
            .prefetch_related("topics", "tags", "related_sectors", "related_countries")
        )

        # Filter by type
        pub_type = self.request.GET.get("type")
        if pub_type:
            qs = qs.filter(publication_type=pub_type)

        # Filter by topic
        topic_slug = self.request.GET.get("topic")
        if topic_slug:
            qs = qs.filter(topics__slug=topic_slug)

        # Filter by country
        country_id = self.request.GET.get("country")
        if country_id:
            qs = qs.filter(related_countries__id=country_id)

        # Filter by year
        year = self.request.GET.get("year")
        if year:
            qs = qs.filter(year=year)

        # Search
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

        # Sort
        sort = self.request.GET.get("sort", "-publication_date")
        valid_sorts = ["-publication_date", "publication_date", "-download_count", "title"]
        if sort in valid_sorts:
            qs = qs.order_by(sort)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filter options
        context["publication_types"] = Publication.PUBLICATION_TYPES
        context["topics"] = Topic.objects.filter(publications__published=True).distinct()
        context["countries"] = MemberStateIPA.objects.filter(
            publications__published=True
        ).distinct()
        context["available_years"] = (
            Publication.objects.filter(published=True)
            .values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )

        # Current filters
        context["current_filters"] = {
            "type": self.request.GET.get("type", ""),
            "topic": self.request.GET.get("topic", ""),
            "country": self.request.GET.get("country", ""),
            "year": self.request.GET.get("year", ""),
            "sort": self.request.GET.get("sort", "-publication_date"),
        }

        return context


class PublicationDetailView(DetailView):
    """Individual publication detail page."""

    model = Publication
    template_name = "knowledge_hub/publication_detail.html"
    context_object_name = "publication"

    def get_queryset(self):
        return (
            Publication.objects.filter(published=True)
            .select_related("cover_media")
            .prefetch_related("topics", "tags", "related_sectors", "related_countries")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Increment view count
        publication = self.get_object()
        publication.view_count += 1
        publication.save(update_fields=["view_count"])

        # Related publications
        context["related_publications"] = (
            Publication.objects.filter(published=True, topics__in=publication.topics.all())
            .exclude(pk=publication.pk)
            .distinct()[:3]
        )

        return context


# ============================================================================
# NEWS & ARTICLES
# ============================================================================


class NewsListView(ListView):
    """
    News listing page with filters and search.

    URL: /news/ or /media-center/news/
    Features:
    - Category filtering
    - Country filtering
    - Search
    - Pagination
    - Featured news at top
    """

    model = NewsArticle
    template_name = "knowledge_hub/news_hub.html"
    context_object_name = "news_articles"
    paginate_by = 12

    def get_queryset(self):
        """Get filtered and published news"""
        qs = (
            NewsArticle.objects.filter(published=True, publication_date__lte=timezone.now())
            .select_related("featured_media", "member_state", "created_by")
            .prefetch_related("tags", "topics")
        )

        # Category filter
        category = self.request.GET.get("category")
        if category and category in dict(NewsArticle.CATEGORY_CHOICES):
            qs = qs.filter(category=category)

        # Country filter
        country_slug = self.request.GET.get("country")
        if country_slug:
            if country_slug == "hq":
                qs = qs.filter(member_state__isnull=True)
            else:
                qs = qs.filter(member_state__slug=country_slug)

        # Search query
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(excerpt__icontains=query)
                | Q(content__icontains=query)
                | Q(tags__name__icontains=query)
            ).distinct()

        # Scope filter
        scope = self.request.GET.get("scope")
        if scope in ["hq", "country"]:
            qs = qs.filter(scope=scope)

        return qs.order_by("-featured", "-publication_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Categories for filter tabs
        context["categories"] = NewsArticle.CATEGORY_CHOICES
        context["current_category"] = self.request.GET.get("category", "")

        # Member states for country filter
        context["member_states"] = (
            MemberStateIPA.objects.filter(is_active=True)
            .annotate(news_count=Count("news_articles", filter=Q(news_articles__published=True)))
            .filter(news_count__gt=0)
        )
        context["current_country"] = self.request.GET.get("country", "")

        # Search query
        context["search_query"] = self.request.GET.get("q", "")

        # Featured news (top 3, shown separately)
        if not any(
            [
                self.request.GET.get("category"),
                self.request.GET.get("country"),
                self.request.GET.get("q"),
                self.request.GET.get("page", 1) != 1,
            ]
        ):
            # Only show featured on first page without filters
            context["featured_news"] = NewsArticle.get_featured_news(limit=3)

        # Stats
        context["total_news_count"] = NewsArticle.get_published_news().count()
        context["hq_news_count"] = NewsArticle.get_hq_news().count()
        context["country_news_count"] = (
            NewsArticle.get_published_news().filter(member_state__isnull=False).count()
        )

        return context


class NewsDetailView(DetailView):
    """
    News detail page with full content.

    URL: /news/<slug>/
    Features:
    - Full article content
    - Featured image hero
    - Supporting images carousel
    - Social share buttons
    - Related news sidebar
    - Previous/Next navigation
    """

    model = NewsArticle
    template_name = "knowledge_hub/news_detail.html"
    context_object_name = "article"
    slug_field = "slug"

    def get_queryset(self):
        """Only published news"""
        return (
            NewsArticle.objects.filter(published=True, publication_date__lte=timezone.now())
            .select_related("featured_media", "member_state", "created_by")
            .prefetch_related(
                "supporting_images", "tags", "topics", "related_countries", "related_sectors"
            )
        )

    def get_object(self):
        """Get article and increment view count"""
        obj = super().get_object()

        # Increment view count (consider using async/celery for production)
        obj.increment_view_count()

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        # Parse content blocks
        context["content_blocks"] = (
            article.content_blocks if isinstance(article.content_blocks, list) else []
        )

        # Supporting images for carousel
        context["supporting_images"] = article.get_supporting_images_list()

        # Recent news in same category (sidebar)
        context["recent_news"] = (
            NewsArticle.objects.filter(
                published=True, category=article.category, publication_date__lte=timezone.now()
            )
            .exclude(pk=article.pk)
            .select_related("featured_media")
            .order_by("-publication_date")[:5]
        )

        # Related news (same tags or topics)
        context["related_news"] = article.get_related_news(limit=3)

        # Previous article (older)
        context["previous_article"] = (
            NewsArticle.objects.filter(
                published=True, publication_date__lt=article.publication_date
            )
            .order_by("-publication_date")
            .first()
        )

        # Next article (newer)
        context["next_article"] = (
            NewsArticle.objects.filter(
                published=True, publication_date__gt=article.publication_date
            )
            .order_by("publication_date")
            .first()
        )

        # Social share data
        context["share_url"] = self.request.build_absolute_uri()
        context["share_title"] = article.title
        context["share_excerpt"] = article.excerpt

        # Breadcrumbs
        context["breadcrumbs"] = [
            {"title": "Home", "url": "/"},
            {"title": "News", "url": "/news/"},
            {"title": article.get_category_display(), "url": f"/news/?category={article.category}"},
            {"title": article.title, "url": ""},
        ]

        return context


class NewsByCategoryView(NewsListView):
    """News filtered by specific category"""

    def get_queryset(self):
        self.category = self.kwargs.get("category")
        qs = super().get_queryset()
        return qs.filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = dict(NewsArticle.CATEGORY_CHOICES).get(self.category, "News")
        context["current_category"] = self.category
        return context


class NewsByCountryView(NewsListView):
    """News filtered by specific country"""

    def get_queryset(self):
        self.member_state = get_object_or_404(MemberStateIPA, slug=self.kwargs.get("country_slug"))
        qs = super().get_queryset()
        return qs.filter(member_state=self.member_state)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"{self.member_state.country_name} News"
        context["member_state"] = self.member_state
        return context


# ============================================================================
# RESOURCES
# ============================================================================


class ResourcesLibraryView(ListView):
    """Resources library with tabbed interface."""

    model = Resource
    template_name = "knowledge_hub/resources_library.html"
    context_object_name = "resources"
    paginate_by = 15

    def get_queryset(self):
        qs = Resource.objects.filter(published=True).select_related("resource_file")

        # Filter by resource type
        resource_type = self.request.GET.get("type")
        if resource_type:
            qs = qs.filter(resource_type=resource_type)

        # Search
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

        return qs.order_by("-last_updated", "-featured")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Group by resource type for tabs
        context["resource_types"] = Resource.RESOURCE_TYPES

        # Get counts per type
        context["type_counts"] = {}
        for type_code, type_name in Resource.RESOURCE_TYPES:
            context["type_counts"][type_code] = Resource.objects.filter(
                published=True, resource_type=type_code
            ).count()

        return context


# ============================================================================
# DOWNLOAD HANDLERS
# ============================================================================


@require_http_methods(["POST", "GET"])
def download_publication(request, pk):
    """Handle publication download."""
    publication = get_object_or_404(Publication, pk=pk, published=True)

    # Increment download count
    publication.download_count += 1
    publication.save(update_fields=["download_count"])

    # Redirect to file URL
    from django.shortcuts import redirect

    return redirect(publication.file)


@require_http_methods(["POST", "GET"])
def download_resource(request, pk):
    """Handle resource download via MediaFile."""
    resource = get_object_or_404(Resource, pk=pk, published=True)

    # Increment download counts
    resource.download_count += 1
    resource.save(update_fields=["download_count"])

    # Get download URL from MediaFile
    if resource.resource_file:
        download_url = resource.resource_file.get_download_url()
        from django.shortcuts import redirect

        return redirect(download_url)

    return JsonResponse({"error": "File not available"}, status=404)


# ============================================================================
# NEWSLETTER SUBSCRIPTION
# ============================================================================


@require_http_methods(["POST"])
def subscribe_newsletter(request):
    """Handle newsletter subscription."""
    email = request.POST.get("email")

    if not email:
        return JsonResponse({"success": False, "error": "Email required"}, status=400)

    # Get preferences
    preferences = {
        "publications": request.POST.get("publications") == "on",
        "news": request.POST.get("news") == "on",
        "events": request.POST.get("events") == "on",
        "data_reports": request.POST.get("data_reports") == "on",
    }

    # TODO: Save to your newsletter system
    # NewsletterSubscription.objects.create(
    #     email=email,
    #     preferences=preferences
    # )

    return JsonResponse({"success": True, "message": "Successfully subscribed to newsletter!"})


# ============================================================================
# SEARCH
# ============================================================================


@require_http_methods(["GET"])
def search_content(request):
    """Unified search across all Knowledge Hub content."""
    query = request.GET.get("q", "")
    content_type = request.GET.get("type", "all")  # all, publication, news, resource

    if not query:
        return JsonResponse({"results": []})

    results = []

    # Search publications
    if content_type in ["all", "publication"]:
        publications = Publication.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query), published=True
        ).select_related("cover_media")[:10]

        for pub in publications:
            results.append(
                {
                    "type": "publication",
                    "title": pub.title,
                    "excerpt": pub.description[:200],
                    "url": f"/knowledge-hub/publications/{pub.slug}/",
                    "date": pub.publication_date.isoformat(),
                    "thumbnail": pub.cover_media.get_thumbnail() if pub.cover_media else None,
                }
            )

    # Search news articles
    if content_type in ["all", "news"]:
        articles = NewsArticle.objects.filter(
            Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query),
            published=True,
        ).select_related("featured_media")[:10]

        for article in articles:
            results.append(
                {
                    "type": "news",
                    "title": article.title,
                    "excerpt": article.excerpt[:200],
                    "url": f"/knowledge-hub/news/{article.slug}/",
                    "date": article.publication_date.isoformat(),
                    "thumbnail": (
                        article.featured_media.get_thumbnail() if article.featured_media else None
                    ),
                }
            )

    # Search resources
    if content_type in ["all", "resource"]:
        resources = Resource.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query), published=True
        )[:10]

        for resource in resources:
            results.append(
                {
                    "type": "resource",
                    "title": resource.title,
                    "excerpt": resource.description[:200],
                    "url": f"/knowledge-hub/resources/{resource.pk}/",
                    "date": resource.last_updated.isoformat(),
                }
            )

    return JsonResponse({"results": results})
