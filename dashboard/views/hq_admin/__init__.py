"""
HQ Admin Views Package
apps/dashboard/views/hq_admin/__init__.py

Exports all HQ Admin views for easy importing.
All views require user_type='ipawas_admin'
"""

from .analytics import (
    AllInquiriesAnalyticsView,
    AllOpportunitiesAnalyticsView,
    PlatformAnalyticsView,
    PlatformTrafficView,
)
from .dashboard import HQDashboardView
from .knowledge_hub import (
    HQNewsAutoSaveView,
    HQNewsCreateView,
    HQNewsDeleteView,
    HQNewsListView,
    HQNewsPreviewView,
    HQNewsUpdateView,
)
from .members import (
    MemberStateActivitiesView,
    MemberStateAnalyticsView,
    MemberStateDetailView,
    MemberStateInviteView,
    MemberStateListView,
    MemberStateUsersView,
)
from .reports import (
    ActivitySummaryView,
    MemberStateComparisonView,
    PlatformStatsView,
    ReportsExportView,
    ReportsOverviewView,
)
from .settings import (
    HQ2FASetupView,
    HQAdminSettingsView,
    HQNotificationPreferencesView,
    HQPasswordChangeView,
)
from .system import (
    EmailSettingsView,
    MaintenanceModeView,
    SecuritySettingsView,
    SystemConfigView,
    SystemLogsView,
)
from .users import (
    SystemUsersView,
    UserDeactivateView,
    UserDetailView,
    UserEditView,
    UserPermissionsView,
)
from feedback.views import HQFeedbackDetailView, HQFeedbackListView

__all__ = [
    # Dashboard
    "HQDashboardView",
    # Member States
    "MemberStateListView",
    "MemberStateDetailView",
    "MemberStateInviteView",
    "MemberStateUsersView",
    "MemberStateActivitiesView",
    "MemberStateAnalyticsView",
    # Users
    "SystemUsersView",
    "UserDetailView",
    "UserEditView",
    "UserDeactivateView",
    "UserPermissionsView",
    # System
    "SystemConfigView",
    "SystemLogsView",
    "EmailSettingsView",
    "SecuritySettingsView",
    "MaintenanceModeView",
    # Reports
    "ReportsOverviewView",
    "PlatformStatsView",
    "MemberStateComparisonView",
    "ActivitySummaryView",
    "ReportsExportView",
    # Analytics
    "PlatformAnalyticsView",
    "AllOpportunitiesAnalyticsView",
    "AllInquiriesAnalyticsView",
    "PlatformTrafficView",
    # Settings
    "HQAdminSettingsView",
    "HQPasswordChangeView",
    "HQ2FASetupView",
    "HQNotificationPreferencesView",
    # Knowledge Hub News
    "HQNewsListView",
    "HQNewsCreateView",
    "HQNewsUpdateView",
    "HQNewsDeleteView",
    "HQNewsAutoSaveView",
    "HQNewsPreviewView",
]
