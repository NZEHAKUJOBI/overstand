from django.urls import path

from core.views import knowledge_hub as views

app_name = "knowledge_hub"

urlpatterns = [
    # Landing Page
    path("", views.KnowledgeHubLandingView.as_view(), name="hub"),
    # Publications
    path("publications/", views.PublicationsLibraryView.as_view(), name="publications"),
    path(
        "publications/<slug:slug>/",
        views.PublicationDetailView.as_view(),
        name="publication_detail",
    ),
    path(
        "publications/<int:pk>/download/", views.download_publication, name="publication_download"
    ),
    # News & Articles
    path("news/", views.NewsListView.as_view(), name="news"),
    path("news/<slug:slug>/", views.NewsDetailView.as_view(), name="news_detail"),
    # Resources
    path("resources/", views.ResourcesLibraryView.as_view(), name="resources"),
    path("resources/<int:pk>/download/", views.download_resource, name="resource_download"),
    # Newsletter & Search
    path("newsletter/subscribe/", views.subscribe_newsletter, name="newsletter_subscribe"),
    path("search/", views.search_content, name="search"),
]
