"""
Inquiry URL Patterns
apps/dashboard/urls/inquiries.py

Handles routing for investor inquiries in the dashboard.
Works for both HQ admin and Member State dashboards.
"""

from django.urls import path

from dashboard.views import inquiries as views

app_name = "inquiries"

urlpatterns = [
    # List all inquiries
    # HQ: /dashboard/hq/inquiries/
    # Member: /dashboard/<member-state-slug>/inquiries/
    path("", views.InquiryListView.as_view(), name="list"),
    # View inquiry details
    path("<int:pk>/", views.InquiryDetailView.as_view(), name="detail"),
    # Update inquiry status
    path("<int:pk>/update-status/", views.InquiryUpdateStatusView.as_view(), name="update_status"),
    # Assign inquiry
    path("<int:pk>/assign/", views.InquiryAssignView.as_view(), name="assign"),
    # Add internal note
    path("<int:pk>/add-note/", views.InquiryAddNoteView.as_view(), name="add_note"),
    # Send email reply to investor
    path("<int:pk>/reply/", views.InquiryReplyView.as_view(), name="reply"),
]
