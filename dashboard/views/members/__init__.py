"""
Member State Views Package - apps/dashboard/views/member_state/__init__.py
"""

from .analytics import AnalyticsExportView, AnalyticsView
from .dashboard import DashboardOverviewView
from .knowledge_hub import (
    CountryMediaPickerAPIView,
    CountryNewsAutoSaveView,
    CountryNewsCreateView,
    CountryNewsDeleteView,
    CountryNewsListView,
    CountryNewsPreviewView,
    CountryNewsUpdateView,
)

from .incentives import (
    IncentiveCreateView,
    IncentiveDeleteView,
    IncentiveEditView,
    IncentiveListView,
)
# from .inquiries import (
#     InquiryAssignView,
#     InquiryCloseView,
#     InquiryDetailView,
#     InquiryInboxView,
#     InquiryRespondView,
# )
# from .notifications import (
#     NotificationListView,
#     NotificationMarkAllReadView,
#     NotificationMarkReadView,
# )
from .opportunities import (
    OpportunityCreateView,
    OpportunityDeleteView,
    OpportunityDetailView,
    OpportunityEditView,
    OpportunityListView,
    OpportunityPublishView,
    OpportunityToggleFeaturedView,
    OpportunityUnpublishView,
)
from .profile import (
    BasicInfoUpdateView,
    EconomicDataUpdateView,
    IncentivesView,
    MediaGalleryView,
    ProfileOverviewView,
    ResourceDeleteDocumentView,
    ResourceSaveDocumentUrlView,
    ResourceUploadSignatureView,
    ResourcesUpdateView,
    SEOSettingsView,
)
from .team import TeamMemberActivateView, TeamMemberDeactivateView, TeamMemberUpdateRoleView, TeamView
from .sectors import (
    SectorAddView,
    SectorDeleteView,
    SectorEditView,
    SectorListView,
    SectorReorderView,
)

# from .settings import (
#     NotificationPreferencesView,
#     PasswordChangeView,
#     TwoFactorSetupView,
#     UserSettingsView,
# )
from .success_stories import (
    SuccessStoryCreateView,
    SuccessStoryDeleteView,
    SuccessStoryEditView,
    SuccessStoryListView,
)
from .leadership import LeadershipEditView
from feedback.views import FeedbackDetailView, FeedbackListView, FeedbackSubmitView
from .fdi_data import (
    FDIDataCreateView,
    FDIDataDeleteView,
    FDIDataEditView,
    FDIDataListView,
)
# from .team import (
#     TeamInviteView,
#     TeamMemberDeactivateView,
#     TeamMemberDetailView,
#     TeamMemberEditView,
#     TeamMemberPermissionsView,
#     TeamMembersView,
# )
