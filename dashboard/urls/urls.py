"""
Main Dashboard URLs - apps/dashboard/urls.py

Improved routing with:
- Member state context in URLs
- Smart redirects based on user type
- Clear separation of HQ vs country dashboards
"""

from django.urls import include, path
from django.views.generic import RedirectView

from dashboard.views.routing import DashboardRoutingView

app_name = "dashboard"

urlpatterns = [
    # Smart router - redirects users to their appropriate dashboard
    path("", DashboardRoutingView.as_view(), name="index"),
    # HQ Admin Dashboard (system-wide)
    path("hq/", include("dashboard.urls.hq_admin", namespace="hq")),
    # Fixed-path routes MUST come before <slug> to avoid slug matching them
    path("invitations/", include("dashboard.urls.invitations", namespace="invitations")),
    path("inquiries/", include("dashboard.urls.inquiries", namespace="inquiries")),
    path("help/", include("dashboard.urls.help", namespace="help")),
    # Member State Dashboard (country-specific with slug) — must be last
    path("<slug:member_state_slug>/", include("dashboard.urls.members", namespace="country")),
]
