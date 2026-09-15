"""
Media Center URLs - IPAWAS Frontend
====================================

URLs for public-facing Media Center integrated with existing MediaFile system.
"""

from django.urls import path

from core.views import media_center as views

app_name = "media_center"

urlpatterns = [
    # Main Media Center Hub
    path("", views.MediaCenterView.as_view(), name="hub"),
    # Press Releases
    path("press/", views.PressReleaseListView.as_view(), name="press_releases"),
    path("press/<slug:slug>/", views.PressReleaseDetailView.as_view(), name="press_release_detail"),
    path("press/<int:pk>/download/", views.download_press_release, name="press_release_download"),
    # Photo Gallery
    path("photos/", views.PhotoGalleryView.as_view(), name="photo_gallery"),
    path("photos/<int:pk>/", views.PhotoDetailView.as_view(), name="photo_detail"),
    path("photos/<int:pk>/download/", views.download_photo, name="photo_download"),
    # Video Library
    path("videos/", views.VideoLibraryView.as_view(), name="video_library"),
    path("videos/<int:pk>/", views.VideoDetailView.as_view(), name="video_detail"),
    # Media Kit
    path("media-kit/", views.MediaKitView.as_view(), name="media_kit"),
    path("media-kit/<int:pk>/download/", views.download_media_kit_item, name="media_kit_download"),
    # AJAX Endpoints
    path("ajax/stats/", views.MediaStatsAjaxView.as_view(), name="ajax_stats"),
    path("ajax/search/", views.MediaSearchAjaxView.as_view(), name="ajax_search"),
]
