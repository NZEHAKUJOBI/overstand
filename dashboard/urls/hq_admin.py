"""
HQ Admin URLs - apps/dashboard/urls/hq_admin.py

System-wide administration for IPAWAS Headquarters staff.
Only accessible to users with user_type='ipawas_admin'
"""

from django.urls import include, path

from dashboard.views import hq_admin as views
from dashboard.views.hq.onboarding import (
    OnboardingApproveView,
    OnboardingIndexView,
    OnboardingRejectView,
    OnboardingRequestDetailView,
    OnboardingRequestListView,
    OnboardingSessionCreateView,
    OnboardingSessionQRImageView,
    OnboardingSessionQRView,
    OnboardingSessionToggleView,
)
from dashboard.views.hq.training import (
    TrainingIndexView,
    TrainingResponsesView,
    TrainingSessionDetailView,
)

app_name = "hq"

urlpatterns = [
    # HQ Dashboard Overview
    path("", views.HQDashboardView.as_view(), name="overview"),
    # Member States Management
    path(
        "members/",
        include(
            [
                path("", views.MemberStateListView.as_view(), name="member_states"),
                path(
                    "<slug:slug>/",
                    views.MemberStateDetailView.as_view(),
                    name="member_state_detail",
                ),
                path(
                    "<slug:slug>/invite/",
                    views.MemberStateInviteView.as_view(),
                    name="member_state_invite",
                ),
                path(
                    "<slug:slug>/users/",
                    views.MemberStateUsersView.as_view(),
                    name="member_state_users",
                ),
                path(
                    "<slug:slug>/activities/",
                    views.MemberStateActivitiesView.as_view(),
                    name="member_state_activities",
                ),
                path(
                    "<slug:slug>/analytics/",
                    views.MemberStateAnalyticsView.as_view(),
                    name="member_state_analytics",
                ),
            ]
        ),
    ),
    # System-wide User Management
    path(
        "users/",
        include(
            [
                path("", views.SystemUsersView.as_view(), name="users"),
                path("<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
                path("<int:pk>/edit/", views.UserEditView.as_view(), name="user_edit"),
                path(
                    "<int:pk>/deactivate/",
                    views.UserDeactivateView.as_view(),
                    name="user_deactivate",
                ),
                path(
                    "<int:pk>/permissions/",
                    views.UserPermissionsView.as_view(),
                    name="user_permissions",
                ),
            ]
        ),
    ),
    # System Configuration
    path(
        "system/",
        include(
            [
                path("", views.SystemConfigView.as_view(), name="config"),
                path("logs/", views.SystemLogsView.as_view(), name="logs"),
                path("email/", views.EmailSettingsView.as_view(), name="email"),
                path("security/", views.SecuritySettingsView.as_view(), name="security"),
                path("maintenance/", views.MaintenanceModeView.as_view(), name="maintenance"),
            ]
        ),
    ),
    # Platform Reports
    path(
        "reports/",
        include(
            [
                path("", views.ReportsOverviewView.as_view(), name="reports"),
                path("platform-stats/", views.PlatformStatsView.as_view(), name="platform_stats"),
                path(
                    "member-state-comparison/",
                    views.MemberStateComparisonView.as_view(),
                    name="comparison",
                ),
                path(
                    "activity-summary/",
                    views.ActivitySummaryView.as_view(),
                    name="activity_summary",
                ),
                path("export/", views.ReportsExportView.as_view(), name="export"),
            ]
        ),
    ),
    # Platform Analytics
    path(
        "analytics/",
        include(
            [
                path("", views.PlatformAnalyticsView.as_view(), name="analytics"),
                path(
                    "opportunities/",
                    views.AllOpportunitiesAnalyticsView.as_view(),
                    name="opportunities",
                ),
                path("inquiries/", views.AllInquiriesAnalyticsView.as_view(), name="inquiries"),
                path("traffic/", views.PlatformTrafficView.as_view(), name="traffic"),
            ]
        ),
    ),
    # Settings (HQ Admin personal settings)
    path(
        "settings/",
        include(
            [
                path("", views.HQAdminSettingsView.as_view(), name="settings"),
                path("password/", views.HQPasswordChangeView.as_view(), name="password"),
                path("2fa/", views.HQ2FASetupView.as_view(), name="2fa"),
                path(
                    "notifications/",
                    views.HQNotificationPreferencesView.as_view(),
                    name="notifications",
                ),
            ]
        ),
    ),
    path(
        "media/",
        include(
            [
                path("", include("media_app.urls", namespace="media")),
            ]
        ),
    ),
    path(
        "training/",
        include(
            ([
                path("", TrainingIndexView.as_view(), name="index"),
                path("<int:pk>/", TrainingSessionDetailView.as_view(), name="detail"),
                path("<int:pk>/responses/", TrainingResponsesView.as_view(), name="responses"),
            ], "training"),
        ),
    ),
    # Feedback
    path(
        "feedback/",
        include(
            [
                path("", views.HQFeedbackListView.as_view(), name="feedback_list"),
                path("<int:pk>/", views.HQFeedbackDetailView.as_view(), name="feedback_detail"),
            ]
        ),
    ),
    path("invitations/", include("dashboard.urls.invitations", namespace="invitations")),
    path("inquiries/", include("dashboard.urls.inquiries", namespace="inquiries")),
    path("news/", include("dashboard.urls.news", namespace="news")),
    path("media-center/", include("dashboard.urls.hq_media_center", namespace="media_center")),
    path(
        "onboarding/",
        include(
            (
                [
                    path("", OnboardingIndexView.as_view(), name="index"),
                    path("sessions/new/", OnboardingSessionCreateView.as_view(), name="session_create"),
                    path("sessions/<int:pk>/qr/", OnboardingSessionQRView.as_view(), name="session_qr"),
                    path("sessions/<int:pk>/qr/image/", OnboardingSessionQRImageView.as_view(), name="session_qr_image"),
                    path("sessions/<int:pk>/toggle/", OnboardingSessionToggleView.as_view(), name="session_toggle"),
                    path("requests/", OnboardingRequestListView.as_view(), name="requests"),
                    path("requests/<int:pk>/", OnboardingRequestDetailView.as_view(), name="request_detail"),
                    path("requests/<int:pk>/approve/", OnboardingApproveView.as_view(), name="approve"),
                    path("requests/<int:pk>/reject/", OnboardingRejectView.as_view(), name="reject"),
                ],
                "onboarding",
            )
        ),
    ),
]
