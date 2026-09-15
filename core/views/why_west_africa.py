"""
Views for Why West Africa Section
Handles all pages: hub, investment case, incentives, success stories, and 8 sector pages
"""

from decimal import Decimal

from django.db import models
from django.db.models import Avg, Count, F, Q, Sum
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView, TemplateView

from core.models import Sector
from members.models import (
    FDIDataPoint,
    InvestmentIncentive,
    MemberStateIPA,
    MemberStateSector,
    SuccessStory,
)
from opportunities.models import InvestmentOpportunity

# ============================================================================
# WHY WEST AFRICA HUB - Landing Page
# ============================================================================


class WhyWestAfricaHubView(TemplateView):
    """
    Main landing page for Why West Africa section
    Shows: 10 reasons, regional map, sector highlights, stats, comparison
    """

    template_name = "core/why_west_africa/why_west_africa_hub.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Regional statistics
        regional_stats = MemberStateIPA.objects.aggregate(
            total_population=Sum("population"), total_gdp=Sum("gdp"), country_count=Count("id")
        )

        context["regional_stats"] = {
            "population": regional_stats["total_population"],
            "gdp": regional_stats["total_gdp"],
            "countries": regional_stats["country_count"],
            "afcfta_access": 1_300_000_000,  # 1.3 billion
            "avg_growth": 5.2,
        }

        # Featured sectors with opportunity counts
        context["featured_sectors"] = (
            Sector.objects.filter(featured=True)
            .annotate(
                opportunity_count=Count(
                    "primary_opportunities", filter=Q(primary_opportunities__status="active")
                ),
                country_count=Count("primary_opportunities__primary_country", distinct=True),
            )
            .order_by("display_order")[:8]
        )

        # Active opportunities count
        context["total_opportunities"] = InvestmentOpportunity.objects.filter(
            status="active"
        ).count()

        # FDI inflows (latest year)
        latest_year = FDIDataPoint.objects.aggregate(max_year=models.Max("year"))["max_year"]

        if latest_year:
            context["fdi_inflows"] = FDIDataPoint.objects.filter(year=latest_year).aggregate(
                total=Sum("value")
            )["total"]

        # Top performing countries (by GDP)
        context["top_countries"] = MemberStateIPA.objects.order_by("-gdp")[:5]

        # Investment incentives summary
        context["incentive_count"] = InvestmentIncentive.objects.filter(is_active=True).count()

        return context


# ============================================================================
# INVESTMENT CASE
# ============================================================================


class InvestmentCaseView(TemplateView):
    """
    Comprehensive investment case with data, market fundamentals, resources
    """

    template_name = "core/why_west_africa/investment_case.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Market fundamentals
        all_states = MemberStateIPA.objects.all()
        total_pop = all_states.aggregate(Sum("population"))["population__sum"] or 0
        total_gdp = all_states.aggregate(Sum("gdp"))["gdp__sum"] or 0

        # Format population: e.g. 423500000 → "420M+"
        if total_pop >= 1_000_000:
            pop_display = f"{round(total_pop / 1_000_000)}M+"
        elif total_pop > 0:
            pop_display = f"{total_pop:,}"
        else:
            pop_display = "400M+"  # fallback if DB has no data yet

        # Format GDP: gdp field stores raw USD (e.g. 477_000_000_000 for $477B)
        if total_gdp >= 1_000_000_000:
            gdp_billions = total_gdp / 1_000_000_000
            gdp_display = f"${round(gdp_billions)}B+"
        elif total_gdp >= 1_000_000:
            gdp_millions = total_gdp / 1_000_000
            gdp_display = f"${round(gdp_millions)}M+"
        elif total_gdp > 0:
            gdp_display = f"${total_gdp:,.0f}"
        else:
            gdp_display = "$700B+"  # fallback if DB has no data yet

        context["market_fundamentals"] = {
            "total_population": total_pop,
            "total_population_display": pop_display,
            "total_gdp": total_gdp,
            "total_gdp_display": gdp_display,
            "arable_land_hectares": 248_000_000,
            "urbanization_rate": 55,
            "youth_population_pct": 60,
        }

        # GDP growth by country — pulled from MemberStateIPA (gdp field is raw USD)
        context["gdp_growth_data"] = [
            {
                "country": state.country_name,
                "growth": float(state.gdp_growth_rate),
                "gdp": round(float(state.gdp) / 1_000_000_000, 1),
            }
            for state in MemberStateIPA.objects.filter(
                is_active=True,
                gdp__isnull=False,
                gdp_growth_rate__isnull=False,
            ).order_by("-gdp_growth_rate")[:10]
        ]

        # FDI by sector (latest year)
        latest_year = FDIDataPoint.objects.aggregate(max_year=models.Max("year"))["max_year"]

        if latest_year:
            context["fdi_by_sector"] = (
                FDIDataPoint.objects.filter(year=latest_year, data_type="fdi_inflow")
                .values("member_state__country_name")
                .annotate(total_fdi=Sum("value"))
                .order_by("-total_fdi")[:5]
            )

            # context["fdi_by_sector"] = (
            #     FDIDataPoint.objects.filter(year=latest_year, member_state__sectors__isnull=False)
            #     .values("sector__name")
            #     .annotate(total_fdi=Sum("fdi_inflow"))
            #     .order_by("-total_fdi")[:5]
            # )

        # Resource endowment data
        context["resource_data"] = {
            "oil_reserves_billion_barrels": 37,
            "gas_reserves_tcf": 287,
            "solar_potential_gwh": 60_000,
            "arable_land_hectares": 248_000_000,
            "africa_ag_potential_pct": 40,
            "coastline_km": 7_400,
        }

        # Infrastructure investments
        context["infrastructure_pipeline"] = {
            "total_value_billion": 100,
            "major_ports": 45,
            "fiber_optic_km": 85_000,
            "airports": 120,
        }

        # Economic diversification timeline
        context["diversification_timeline"] = [
            {
                "period": "2015-2018",
                "title": "Foundation Phase",
                "description": "Heavy commodity dependence, limited manufacturing",
            },
            {
                "period": "2019-2021",
                "title": "Transition Phase",
                "description": "Push towards manufacturing, services, digital economy",
            },
            {
                "period": "2022-2024",
                "title": "Acceleration Phase",
                "description": "Non-oil sectors contribute 65%+ to GDP",
            },
            {
                "period": "2025+",
                "title": "Maturation Phase",
                "description": "AfCFTA deepening, export manufacturing growing",
            },
        ]

        return context


# ============================================================================
# INVESTMENT INCENTIVES
# ============================================================================


class InvestmentIncentivesView(TemplateView):
    """
    Overview of fiscal, non-fiscal incentives, and guarantees
    """

    template_name = "core/why_west_africa/investment_incentives.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get incentives by type
        context["fiscal_incentives"] = InvestmentIncentive.objects.filter(
            is_active=True,
            incentive_type__in=["tax_holiday", "tax_reduction", "duty_exemption", "vat_exemption"],
        ).select_related("member_state")

        context["non_fiscal_incentives"] = InvestmentIncentive.objects.filter(
            is_active=True, incentive_type__in=["land_incentive", "infrastructure", "training"]
        ).select_related("member_state")

        context["guarantees"] = InvestmentIncentive.objects.filter(
            is_active=True, incentive_type="repatriation"
        ).select_related("member_state")

        # Country-specific incentive packages
        context["countries_with_incentives"] = (
            MemberStateIPA.objects.filter(incentives__is_active=True)
            .distinct()
            .prefetch_related("incentives")[:4]
        )  # Top 4 for initial display

        # Sector-specific incentives
        context["sectors_with_incentives"] = (
            Sector.objects.filter(incentives__is_active=True)
            .distinct()
            .prefetch_related("incentives")
        )

        # Incentive statistics
        context["incentive_stats"] = {
            "total_active": InvestmentIncentive.objects.filter(is_active=True).count(),
            "countries_offering": MemberStateIPA.objects.filter(incentives__is_active=True)
            .distinct()
            .count(),
            "sectors_covered": Sector.objects.filter(incentives__is_active=True).distinct().count(),
        }

        # Example calculation data
        context["example_calculation"] = {
            "investment_amount": 10_000_000,
            "country": "Ghana",
            "sector": "Manufacturing",
            "tax_savings": 2_800_000,
            "duty_exemptions": 950_000,
            "other_incentives": 500_000,
            "total_savings": 4_250_000,
            "savings_percentage": 42.5,
        }

        return context


# ============================================================================
# SUCCESS STORIES
# ============================================================================


class SuccessStoriesView(TemplateView):
    """
    Display all published success stories with filtering
    """

    template_name = "core/why_west_africa/success_stories.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all published success stories — member_state is the correct FK (not "country")
        base_qs = SuccessStory.objects.filter(published=True).select_related(
            "sector", "member_state"
        )

        context["success_stories"] = base_qs

        # Get featured stories
        context["featured_stories"] = base_qs.filter(featured=True)[:3]

        # Statistics from actual data
        stats = SuccessStory.objects.filter(published=True).aggregate(
            total_fdi=Sum("investment_amount"),
            total_jobs=Sum("jobs_created"),
            country_count=Count("member_state", distinct=True),
            sector_count=Count("sector", distinct=True),
        )

        total_fdi = stats["total_fdi"] or 0
        # Format FDI for display
        if total_fdi >= 1_000_000_000:
            fdi_display = f"${total_fdi / 1_000_000_000:.1f}B+"
        elif total_fdi >= 1_000_000:
            fdi_display = f"${total_fdi / 1_000_000:.0f}M+"
        else:
            fdi_display = f"${total_fdi:,.0f}"

        total_jobs = stats["total_jobs"] or 0
        jobs_display = f"{total_jobs:,}+" if total_jobs else "0"

        context["success_stats"] = {
            "total_fdi": total_fdi,
            "total_fdi_display": fdi_display,
            "total_jobs": total_jobs,
            "total_jobs_display": jobs_display,
            "countries": stats["country_count"] or 0,
            "sectors": stats["sector_count"] or 0,
        }

        # Sectors that have published stories (with slug for ?sector= filtering)
        from core.models import Sector
        context["filter_sectors"] = Sector.objects.filter(
            success_stories__published=True
        ).distinct().order_by("name")

        # Apply sector filter from query string
        sector_filter = self.request.GET.get("sector")
        if sector_filter:
            context["success_stories"] = context["success_stories"].filter(
                sector__slug=sector_filter
            )
            context["active_filter"] = sector_filter
        else:
            context["active_filter"] = ""

        return context


class SuccessStoryDetailView(DetailView):
    """
    Detailed view of individual success story
    """

    model = SuccessStory
    template_name = "core/why_west_africa/success_story_detail.html"
    context_object_name = "story"

    def get_queryset(self):
        return SuccessStory.objects.filter(published=True).select_related("sector", "member_state")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Related success stories (same sector or member_state)
        context["related_stories"] = (
            SuccessStory.objects.filter(published=True)
            .filter(
                models.Q(sector=self.object.sector)
                | models.Q(member_state=self.object.member_state)
            )
            .exclude(id=self.object.id)[:3]
        )

        return context


# ============================================================================
# API ENDPOINTS (Optional - for AJAX filtering)
# ============================================================================

from django.http import JsonResponse
from django.views import View


class SuccessStoriesAPIView(View):
    """
    JSON API for filtering success stories (for AJAX requests)
    """

    def get(self, request):
        # Get filters
        sector = request.GET.get("sector")
        country = request.GET.get("country")

        # Base queryset
        stories = SuccessStory.objects.filter(published=True)

        # Apply filters
        if sector:
            stories = stories.filter(sector__slug=sector)

        if country:
            stories = stories.filter(member_state__slug=country)

        stories = stories.select_related("sector", "member_state")

        # Serialize data
        data = []
        for story in stories:
            data.append(
                {
                    "id": story.id,
                    "title": story.title,
                    "company": story.company_name,
                    "country": story.member_state.country_name,
                    "country_flag": getattr(story.member_state, "flag_emoji", ""),
                    "sector": story.sector.name if story.sector else "",
                    "investment": float(story.investment_amount) if story.investment_amount else 0,
                    "investment_display": story.investment_amount_display or "",
                    "jobs_created": story.jobs_created or 0,
                    "summary": story.summary,
                    "image": story.image or "",
                }
            )

        return JsonResponse({"success": True, "count": len(data), "stories": data})


# ============================================================================
# SECTOR PAGES (8 pages)
# ============================================================================


class SectorDetailView(DetailView):
    """
    Base view for individual sector pages
    Shows opportunities, leading countries, incentives for specific sector
    """

    model = Sector
    template_name = "core/why_west_africa/sector_detail.html"
    context_object_name = "sector"
    slug_url_kwarg = "sector_slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = self.object

        # Sector opportunities
        context["opportunities"] = InvestmentOpportunity.objects.filter(
            sector=sector, status="active"
        ).select_related("primary_country")[:10]

        # Leading countries for this sector
        context["leading_countries"] = MemberStateIPA.objects.filter(
            sector_profiles__sector=sector, sector_profiles__is_priority=True
        ).distinct()[:4]

        # Sector-specific incentives
        context["sector_incentives"] = InvestmentIncentive.objects.filter(
            applicable_sectors=sector, is_active=True
        ).select_related("member_state")

        # Sector statistics
        context["sector_stats"] = {
            "active_opportunities": InvestmentOpportunity.objects.filter(
                sector=sector, status="active"
            ).count(),
            "countries_active": MemberStateIPA.objects.filter(sector_profiles__sector=sector)
            .distinct()
            .count(),
            "total_investment": InvestmentOpportunity.objects.filter(
                sector=sector, status="active"
            ).aggregate(total=Sum("investment_required_min"))["total"]
            or 0,
        }

        # FDI data for sector (if available)
        latest_year = FDIDataPoint.objects.aggregate(max_year=models.Max("year"))["max_year"]

        if latest_year:
            context["sector_fdi"] = FDIDataPoint.objects.filter(
                sector=sector, year=latest_year
            ).aggregate(total=Sum("fdi_inflow"), projects=Sum("number_of_projects"))

        return context


# Individual sector views using specific templates
class AgricultureSectorView(TemplateView):
    template_name = "core/why_west_africa/agriculture_sector.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = get_object_or_404(Sector, slug="agriculture")

        context["sector"] = sector
        context["opportunities"] = InvestmentOpportunity.objects.filter(
            primary_sector=sector, status="active"
        )[:12]
        context["leading_countries"] = MemberStateIPA.objects.filter(
            sectors__sector=sector, sectors__is_priority=True
        )[:3]

        return context


class EnergySectorView(TemplateView):
    template_name = "core/why_west_africa/energy_sector.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = get_object_or_404(Sector, slug="energy")

        context["sector"] = sector
        context["opportunities"] = InvestmentOpportunity.objects.filter(
            primary_sector=sector, status="active"
        )[:12]
        context["leading_countries"] = MemberStateIPA.objects.filter(
            sectors__sector=sector, sectors__is_priority=True
        )[:3]

        return context


class ManufacturingSectorView(TemplateView):
    template_name = "core/why_west_africa/manufacturing_sector.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = get_object_or_404(Sector, slug="manufacturing")

        context["sector"] = sector
        context["opportunities"] = InvestmentOpportunity.objects.filter(
            primary_sector=sector, status="active"
        )[:12]

        return context


class TechnologySectorView(TemplateView):
    template_name = "core/why_west_africa/technology.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = get_object_or_404(Sector, slug="technology")

        context["sector"] = sector
        context["opportunities"] = InvestmentOpportunity.objects.filter(
            primary_sector=sector, status="active"
        )[:12]

        return context


class InfrastructureSectorView(TemplateView):
    template_name = "core/why_west_africa/infrastructure_sector.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = get_object_or_404(Sector, slug="infrastructure-logistics")

        context["sector"] = sector
        context["opportunities"] = InvestmentOpportunity.objects.filter(
            sector=sector, status="active"
        )[:12]

        return context


class MiningSectorView(TemplateView):
    template_name = "core/why_west_africa/mining_sector.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = get_object_or_404(Sector, slug="mining-natural-resources")

        context["sector"] = sector
        context["opportunities"] = InvestmentOpportunity.objects.filter(
            sector=sector, status="active"
        )[:12]

        return context


class TourismSectorView(TemplateView):
    template_name = "core/why_west_africa/tourism_sector.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = get_object_or_404(Sector, slug="tourism-hospitality")

        context["sector"] = sector
        context["opportunities"] = InvestmentOpportunity.objects.filter(
            sector=sector, status="active"
        )[:12]

        return context


class FinancialServicesSectorView(TemplateView):
    template_name = "core/why_west_africa/financial_services_sector.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = get_object_or_404(Sector, slug="financial-services")

        context["sector"] = sector
        context["opportunities"] = InvestmentOpportunity.objects.filter(
            sector=sector, status="active"
        )[:12]

        return context
