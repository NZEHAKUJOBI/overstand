from django.urls import path
from dashboard.views.hq_admin import media_center as views

app_name = "media_center"

urlpatterns = [
    path("", views.HQMediaCenterOverviewView.as_view(), name="overview"),
    path("press-releases/", views.HQPressReleaseListView.as_view(), name="pr_list"),
    path("press-releases/create/", views.HQPressReleaseCreateView.as_view(), name="pr_create"),
    path("press-releases/<int:pk>/edit/", views.HQPressReleaseUpdateView.as_view(), name="pr_edit"),
    path("press-releases/<int:pk>/delete/", views.HQPressReleaseDeleteView.as_view(), name="pr_delete"),
    path("press-releases/<int:pk>/approve/", views.HQPressReleaseApproveView.as_view(), name="pr_approve"),
    path("press-releases/<int:pk>/reject/", views.HQPressReleaseRejectView.as_view(), name="pr_reject"),
    path("media/", views.HQMediaSubmissionListView.as_view(), name="media_list"),
    path("media/<int:pk>/approve/", views.HQMediaApproveView.as_view(), name="media_approve"),
    path("media/<int:pk>/reject/", views.HQMediaRejectView.as_view(), name="media_reject"),
    path("media-kit/", views.HQMediaKitListView.as_view(), name="media_kit"),
]
