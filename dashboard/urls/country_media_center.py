from django.urls import path
from dashboard.views.members import media_center as views

app_name = "media_center"

urlpatterns = [
    path("", views.IPAMediaCenterOverviewView.as_view(), name="overview"),
    path("press-releases/", views.IPAPressReleaseListView.as_view(), name="pr_list"),
    path("press-releases/create/", views.IPAPressReleaseCreateView.as_view(), name="pr_create"),
    path("press-releases/<int:pk>/edit/", views.IPAPressReleaseUpdateView.as_view(), name="pr_edit"),
    path("press-releases/<int:pk>/delete/", views.IPAPressReleaseDeleteView.as_view(), name="pr_delete"),
    path("media/", views.IPAMediaSubmissionListView.as_view(), name="media_list"),
    path("media/submit/", views.IPAMediaSubmitView.as_view(), name="media_submit"),
    path("media/<int:pk>/withdraw/", views.IPAMediaWithdrawView.as_view(), name="media_withdraw"),
]
