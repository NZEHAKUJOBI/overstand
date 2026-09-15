"""
Country News Hub URLs - apps/dashboard/urls/country_news.py

News article management for member state IPA staff.
All URLs are nested under: /dashboard/<member-state-slug>/news/
"""

from django.urls import path

from dashboard.views import members as views

app_name = "news"

urlpatterns = [
    path("", views.CountryNewsListView.as_view(), name="list"),
    path("create/", views.CountryNewsCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.CountryNewsUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.CountryNewsDeleteView.as_view(), name="delete"),
    path("<int:pk>/preview/", views.CountryNewsPreviewView.as_view(), name="preview"),
    path("<int:pk>/autosave/", views.CountryNewsAutoSaveView.as_view(), name="autosave"),
    path("media-picker/", views.CountryMediaPickerAPIView.as_view(), name="media_picker"),
]
