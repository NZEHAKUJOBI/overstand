"""
Media Management URLs - IPAWAS Platform
========================================

URL patterns for media library, following existing dashboard patterns.
"""

from django.urls import include, path

from media_app import views

app_name = "media"

# Folder patterns
folder_patterns = [
    path("create/", views.FolderCreateView.as_view(), name="folder_create"),
    path("<int:pk>/rename/", views.FolderRenameView.as_view(), name="folder_rename"),
    path("<int:pk>/delete/", views.FolderDeleteView.as_view(), name="folder_delete"),
]

# File patterns
file_patterns = [
    path("upload/", views.FileUploadView.as_view(), name="file_upload"),
    path("upload/bulk/", views.BulkFileUploadView.as_view(), name="file_bulk_upload"),
    path("<int:pk>/", views.FileDetailView.as_view(), name="file_detail"),
    path("<int:pk>/edit/", views.FileEditView.as_view(), name="file_edit"),
    path("<int:pk>/delete/", views.FileDeleteView.as_view(), name="file_delete"),
    path("search/", views.FileSearchView.as_view(), name="file_search"),
]

# AJAX patterns
ajax_patterns = [
    path("folders/tree/", views.FolderTreeAjaxView.as_view(), name="ajax_folder_tree"),
    path("files/upload/", views.FileUploadAjaxView.as_view(), name="ajax_file_upload"),
    path("picker/", views.PickerListAPIView.as_view(), name="ajax_picker_list"),
    path("picker/upload/", views.PickerUploadAPIView.as_view(), name="ajax_picker_upload"),
]

# Main patterns
urlpatterns = [
    path("", views.MediaLibraryView.as_view(), name="library"),
    path("folders/", include(folder_patterns)),
    path("files/", include(file_patterns)),
    path("ajax/", include(ajax_patterns)),
]
