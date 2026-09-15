"""
Main Dashboard URLs - apps/dashboard/urls.py

Routes users to appropriate dashboard based on their type:
- IPAWAS HQ Admin → HQ Dashboard (system-wide access)
- Member State IPA Admin → Country Dashboard (member state specific)
"""

from django.urls import include, path

app_name = "dashboard"

urlpatterns = [
    # HQ Admin Dashboard (system-wide)
    # Accessible only to users with user_type='ipawas_admin'
    path("hq/", include("dashboard.urls.hq_admin", namespace="hq")),
    # Member State Dashboard (country-specific)
    # Accessible to users with user_type='ipa_staff'
    # This is the default dashboard for IPA staff
    path("", include("dashboard.urls.members", namespace="country")),
    # Invitations (shared between HQ and Member States with different permissions)
    path("invitations/", include("dashboard.urls.invitations", namespace="invitations")),
]
