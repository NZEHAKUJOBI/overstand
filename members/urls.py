"""
URL Configuration for IPAWAS Members App

App Name: members (not member_states)
Namespace: 'members'
"""

from django.urls import path

from members import views

app_name = "members"

urlpatterns = [
    # Hub/Landing Page
    path("", views.MemberStatesHubView.as_view(), name="hub"),
    # Fixed-path routes MUST come before <slug> to avoid slug matching them
    path("compare/", views.CountryComparisonView.as_view(), name="comparison"),
    path("api/filter/", views.FilterMemberStatesView.as_view(), name="api_filter"),
    path("api/statistics/", views.RegionalStatisticsView.as_view(), name="api_statistics"),
    # Slug-based routes last
    path("<slug:country_slug>/contact/", views.InquiryCreateView.as_view(), name="inquiry_create"),
    path("<slug:country_slug>/", views.MemberStateDetailView.as_view(), name="detail"),
]
