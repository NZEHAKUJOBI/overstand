"""
Invitations URLs - apps/dashboard/urls/invitations.py

Invitation management URLs.
- HQ Admins can manage invitations for any member state
- IPA Admins can manage invitations only for their member state
- Public registration URLs are accessible without authentication
"""

from django.urls import path

from dashboard.views.hq_admin.knowledge_hub import (
    HQMediaPickerAPIView,
    HQNewsAutoSaveView,
    HQNewsCreateView,
    HQNewsDeleteView,
    HQNewsListView,
    HQNewsPreviewView,
    HQNewsUpdateView,
)

app_name = "news"

urlpatterns = [
    # News listing
    path("", HQNewsListView.as_view(), name="list"),
    # Create news
    path("create/", HQNewsCreateView.as_view(), name="create"),
    # Edit news
    path("<int:pk>/edit/", HQNewsUpdateView.as_view(), name="edit"),
    # Delete news
    path("<int:pk>/delete/", HQNewsDeleteView.as_view(), name="delete"),
    # Preview news (before publishing)
    path(
        "<int:pk>/preview/",
        HQNewsPreviewView.as_view(),
        name="preview",
    ),
    # Auto-save (AJAX)
    path(
        "<int:pk>/autosave/",
        HQNewsAutoSaveView.as_view(),
        name="autosave",
    ),
    # HQ media picker (AJAX)
    path("media-picker/", HQMediaPickerAPIView.as_view(), name="media_picker"),
]
