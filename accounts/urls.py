"""
URL Configuration for Authentication
apps/accounts/urls.py

URL patterns for authentication and user management.
"""

from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("login/verify-2fa/", views.VerifyTOTPView.as_view(), name="verify_totp"),
    path("profile/setup-2fa/", views.Setup2FAView.as_view(), name="setup_2fa"),
    path("profile/disable-2fa/", views.Disable2FAView.as_view(), name="disable_2fa"),
    # Invitation
    path(
        "accept-invitation/<str:token>/",
        views.AcceptInvitationView.as_view(),
        name="accept_invitation",
    ),
    path("onboarding/", views.OnboardingView.as_view(), name="onboarding"),
    path("send-invitation/", views.SendInvitationView.as_view(), name="send_invitation"),
    path(
        "pending-invitations/", views.PendingInvitationsView.as_view(), name="pending_invitations"
    ),
    path("resend-invitation/<str:token>/", views.resend_invitation, name="resend_invitation"),
    path("revoke-invitation/<str:token>/", views.revoke_invitation, name="revoke_invitation"),
    # Password Reset
    path("password-reset/", views.PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset/done/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "password-reset/<str:token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("password-change/", views.PasswordChangeView.as_view(), name="password_change"),
    # Profile
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("profile/ipa-edit/", views.IPAProfileUpdateView.as_view(), name="ipa_profile_edit"),
    path("profile/avatar/", views.AvatarUploadView.as_view(), name="avatar_upload"),
    # User Management
    path("team/", views.TeamMembersView.as_view(), name="team_members"),
    path(
        "team/<int:user_id>/permissions/",
        views.ManageUserPermissionsView.as_view(),
        name="manage_permissions",
    ),
    path("team/<int:user_id>/deactivate/", views.deactivate_user, name="deactivate_user"),
    path("team/<int:user_id>/reactivate/", views.reactivate_user, name="reactivate_user"),
    # Email Verification
    path("verify-email/<str:token>/", views.VerifyEmailView.as_view(), name="verify_email"),
]
