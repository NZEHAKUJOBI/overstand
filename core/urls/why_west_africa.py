from django.urls import path

from core.views import why_west_africa as views

app_name = "why_west_africa"

urlpatterns = [
    # ========================================================================
    # MAIN WHY WEST AFRICA PAGES (4 pages)
    # ========================================================================
    # Hub/Landing Page
    path("", views.WhyWestAfricaHubView.as_view(), name="hub"),
    # Investment Case
    path("investment-case/", views.InvestmentCaseView.as_view(), name="investment-case"),
    # Investment Incentives
    path("incentives/", views.InvestmentIncentivesView.as_view(), name="incentives"),
    # Success Stories
    path("success-stories/", views.SuccessStoriesView.as_view(), name="success-stories"),
    # ========================================================================
    # SECTOR PAGES (8 pages)
    # ========================================================================
    # Agriculture & Agribusiness
    path("sectors/agriculture/", views.AgricultureSectorView.as_view(), name="agriculture-sector"),
    # Energy & Renewable Energy
    path("sectors/energy/", views.EnergySectorView.as_view(), name="energy-sector"),
    # Manufacturing & Industrial Parks
    path(
        "sectors/manufacturing/",
        views.ManufacturingSectorView.as_view(),
        name="manufacturing-sector",
    ),
    # ICT & Digital Economy
    path("sectors/technology/", views.TechnologySectorView.as_view(), name="ict-sector"),
    # Infrastructure & Logistics
    path(
        "sectors/infrastructure/",
        views.InfrastructureSectorView.as_view(),
        name="infrastructure-sector",
    ),
    # Mining & Natural Resources
    path("sectors/mining/", views.MiningSectorView.as_view(), name="mining-sector"),
    # Tourism & Hospitality
    path("sectors/tourism/", views.TourismSectorView.as_view(), name="tourism-sector"),
    # Financial Services
    path(
        "sectors/financial-services/",
        views.FinancialServicesSectorView.as_view(),
        name="financial-services-sector",
    ),
    # ========================================================================
    # ALTERNATIVE: Generic sector detail view (optional)
    # Use this if you want dynamic sector pages based on slug
    # ========================================================================
    # path(
    #     'sectors/<slug:sector_slug>/',
    #     views.SectorDetailView.as_view(),
    #     name='sector-detail'
    # ),
]
