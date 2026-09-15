"""
Member State Dashboard URLs - Improved
apps/dashboard/urls/members.py

Now includes member_state_slug in context for all views.
All URLs are prefixed with: /dashboard/<member-state-slug>/
"""

from django.urls import include, path

from dashboard.views import members as views

app_name = "country"

urlpatterns = [
    # Dashboard Overview
    # URL: /dashboard/<member-state-slug>/
    path("", views.DashboardOverviewView.as_view(), name="overview"),
    # Analytics
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    path("analytics/export/", views.AnalyticsExportView.as_view(), name="analytics_export"),
    # Country Profile Management
    # URLs: /dashboard/<member-state-slug>/profile/...
    path(
        "profile/",
        include(
            [
                path("", views.ProfileOverviewView.as_view(), name="profile"),
                path("basic/", views.BasicInfoUpdateView.as_view(), name="profile_basic"),
                path("economic/", views.EconomicDataUpdateView.as_view(), name="profile_economic"),
                path("incentives/", views.IncentivesView.as_view(), name="profile_incentives"),
                path("incentives/add/", views.IncentiveCreateView.as_view(), name="incentives_add"),
                path("incentives/<int:pk>/edit/", views.IncentiveEditView.as_view(), name="incentives_edit"),
                path("incentives/<int:pk>/delete/", views.IncentiveDeleteView.as_view(), name="incentives_delete"),
                path("media/", views.MediaGalleryView.as_view(), name="profile_media"),
                path("seo/", views.SEOSettingsView.as_view(), name="profile_seo"),
                path("resources/", views.ResourcesUpdateView.as_view(), name="profile_resources"),
                path("resources/upload-signature/", views.ResourceUploadSignatureView.as_view(), name="profile_resources_signature"),
                path("resources/save-document-url/", views.ResourceSaveDocumentUrlView.as_view(), name="profile_resources_save_url"),
                path("resources/delete-document/", views.ResourceDeleteDocumentView.as_view(), name="profile_resources_delete"),
            ]
        ),
    ),
    # Priority Sectors
    # URLs: /dashboard/<member-state-slug>/sectors/...
    path(
        "sectors/",
        include(
            [
                path("", views.SectorListView.as_view(), name="sectors"),
                path("add/", views.SectorAddView.as_view(), name="sectors_add"),
                path("<int:pk>/edit/", views.SectorEditView.as_view(), name="sectors_edit"),
                path("<int:pk>/delete/", views.SectorDeleteView.as_view(), name="sectors_delete"),
                path("reorder/", views.SectorReorderView.as_view(), name="sectors_reorder"),
            ]
        ),
    ),
    # Investment Opportunities
    # URLs: /dashboard/<member-state-slug>/opportunities/...
    path(
        "opportunities/",
        include(
            [
                path("", views.OpportunityListView.as_view(), name="opportunities"),
                path("create/", views.OpportunityCreateView.as_view(), name="opportunities_create"),
                path(
                    "<int:pk>/", views.OpportunityDetailView.as_view(), name="opportunities_detail"
                ),
                path(
                    "<int:pk>/edit/", views.OpportunityEditView.as_view(), name="opportunities_edit"
                ),
                path(
                    "<int:pk>/publish/",
                    views.OpportunityPublishView.as_view(),
                    name="opportunities_publish",
                ),
                # Unpublish opportunity
                path(
                    "<int:pk>/unpublish/",
                    views.OpportunityUnpublishView.as_view(),
                    name="opportunities_unpublish",
                ),
                path(
                    "<int:pk>/delete/",
                    views.OpportunityDeleteView.as_view(),
                    name="opportunities_delete",
                ),
                # Toggle featured status
                path(
                    "<int:pk>/toggle-featured/",
                    views.OpportunityToggleFeaturedView.as_view(),
                    name="opportunities_toggle_featured",
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
    # Investment Incentives
    path(
        "incentives/",
        include(
            [
                path("", views.IncentiveListView.as_view(), name="incentives"),
                path("add/", views.IncentiveCreateView.as_view(), name="incentives_add"),
                path("<int:pk>/edit/", views.IncentiveEditView.as_view(), name="incentives_edit"),
                path("<int:pk>/delete/", views.IncentiveDeleteView.as_view(), name="incentives_delete"),
            ]
        ),
    ),
    # Success Stories
    path(
        "success-stories/",
        include(
            [
                path("", views.SuccessStoryListView.as_view(), name="success_stories"),
                path("add/", views.SuccessStoryCreateView.as_view(), name="success_stories_add"),
                path("<int:pk>/edit/", views.SuccessStoryEditView.as_view(), name="success_stories_edit"),
                path("<int:pk>/delete/", views.SuccessStoryDeleteView.as_view(), name="success_stories_delete"),
            ]
        ),
    ),
    # IPA Leadership
    path("leadership/", views.LeadershipEditView.as_view(), name="leadership"),
    # Economic / FDI Data
    path(
        "economic-data/",
        include(
            [
                path("", views.FDIDataListView.as_view(), name="fdi_data"),
                path("add/", views.FDIDataCreateView.as_view(), name="fdi_data_add"),
                path("<int:pk>/edit/", views.FDIDataEditView.as_view(), name="fdi_data_edit"),
                path("<int:pk>/delete/", views.FDIDataDeleteView.as_view(), name="fdi_data_delete"),
            ]
        ),
    ),
    # Team Management
    path("team/", views.TeamView.as_view(), name="team"),
    path("team/<int:pk>/deactivate/", views.TeamMemberDeactivateView.as_view(), name="team_deactivate"),
    path("team/<int:pk>/activate/", views.TeamMemberActivateView.as_view(), name="team_activate"),
    path("team/<int:pk>/update-role/", views.TeamMemberUpdateRoleView.as_view(), name="team_update_role"),
    # Feedback
    path(
        "feedback/",
        include(
            [
                path("", views.FeedbackListView.as_view(), name="feedback_list"),
                path("submit/", views.FeedbackSubmitView.as_view(), name="feedback_submit"),
                path("<int:pk>/", views.FeedbackDetailView.as_view(), name="feedback_detail"),
            ]
        ),
    ),
    path("news/", include("dashboard.urls.country_news", namespace="news")),
    path("invitations/", include("dashboard.urls.invitations", namespace="invitations")),
    path("inquiries/", include("dashboard.urls.inquiries", namespace="inquiries")),
    path("media-center/", include("dashboard.urls.country_media_center", namespace="media_center")),
]
