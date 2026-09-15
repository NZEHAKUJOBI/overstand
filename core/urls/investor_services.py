from django.urls import path

from core.views import investor_service as investor_views

app_name = "investor_services"

urlpatterns = [
    # Main hub
    path("", investor_views.InvestorServicesHubView.as_view(), name="hub"),
    # Investment advisory
    path("advisory/", investor_views.InvestmentAdvisoryView.as_view(), name="advisory"),
    # IPA Connection Hub
    path("ipa-connection/", investor_views.IPAConnectionHubView.as_view(), name="ipa_connection"),
    # Investor Toolkit
    path("toolkit/", investor_views.InvestorToolkitView.as_view(), name="toolkit"),
    # Resources & Guides
    path("resources/", investor_views.ResourcesGuidesView.as_view(), name="resources"),
    # Site Visit Coordination
    path("site-visits/", investor_views.SiteVisitCoordinationView.as_view(), name="site_visits"),
    # AJAX endpoints for toolkit
    path(
        "ajax/incentive-calculator/",
        investor_views.incentive_calculator_ajax,
        name="incentive_calculator_ajax",
    ),
    path("ajax/cost-comparison/", investor_views.cost_comparison_ajax, name="cost_comparison_ajax"),
    path("ajax/roi-estimator/", investor_views.roi_estimator_ajax, name="roi_estimator_ajax"),
]
