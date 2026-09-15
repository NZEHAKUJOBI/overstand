from django.urls import path
from dashboard.views.help import (
    help_index,
    getting_started,
    hq_dashboard_guide,
    ipa_dashboard_guide,
    quick_reference,
    roles_permissions,
)

app_name = "help"

urlpatterns = [
    path("", help_index, name="index"),
    path("getting-started/", getting_started, name="getting_started"),
    path("hq-dashboard/", hq_dashboard_guide, name="hq_dashboard"),
    path("ipa-dashboard/", ipa_dashboard_guide, name="ipa_dashboard"),
    path("quick-reference/", quick_reference, name="quick_reference"),
    path("roles-permissions/", roles_permissions, name="roles_permissions"),
]
