"""
Invitations URLs - apps/dashboard/urls/invitations.py

Invitation management URLs.
- HQ Admins can manage invitations for any member state
- IPA Admins can manage invitations only for their member state
- Public registration URLs are accessible without authentication
"""

from django.urls import path

from dashboard.views import invitation as views

app_name = "invitations"

urlpatterns = [
    # List & manage invitations (for admins)
    # Permission checked: can_manage_users
    path("", views.InvitationListView.as_view(), name="list"),
    path("<int:pk>/", views.InvitationDetailView.as_view(), name="detail"),
    path("create/", views.InvitationCreateView.as_view(), name="create"),
    path("<int:pk>/resend/", views.InvitationResendView.as_view(), name="resend"),
    path("<int:pk>/revoke/", views.InvitationRevokeView.as_view(), name="revoke"),
    path("bulk/", views.BulkInvitationView.as_view(), name="bulk"),
    # QR code views
    path("<int:pk>/qr/", views.InvitationQRView.as_view(), name="qr"),
    path("qr-cards/", views.InvitationBulkQRView.as_view(), name="qr_bulk"),
    # Public registration from invitation
    # No authentication required - token-based access
    path("register/<uuid:token>/", views.InvitationRegistrationView.as_view(), name="register"),
]
