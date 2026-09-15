# programs/urls.py
"""
IPAWAS Programs Section - URL Configuration
"""

from django.urls import path

from core.views import programs as views

app_name = "programs"

urlpatterns = [
    # Main Programs Hub
    path("", views.programs_hub, name="hub"),
    # Specific Program Pages
    path("ipa-leadership-academy/", views.ipa_leadership_academy, name="ipa-leadership"),
    path("investment-promotion-training/", views.investment_promotion_training, name="training"),
    path("regional-investment-missions/", views.regional_investment_missions, name="missions"),
    path("ipa-performance-benchmarking/", views.ipa_performance_benchmarking, name="benchmarking"),
    path("research-publications/", views.research_publications_program, name="research"),
    # Program Actions
    path("submit-proposal/", views.submit_program_proposal, name="submit_proposal"),
    path("<slug:program_slug>/apply/", views.submit_application, name="submit_application"),
    path("<slug:program_slug>/brochure/", views.download_program_brochure, name="download_brochure"),
    # Generic Program Detail (catch-all - should be last)
    path("<slug:slug>/", views.program_detail, name="detail"),
]
