"""
Investor Services Views - CORRECTED for existing schema

Works with YOUR existing InvestorInquiry model structure.
Place this in: investor_services/views.py
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from core.models import Sector
from members.models import InvestorInquiry, MemberStateIPA


class InvestorServicesHubView(TemplateView):
    """Main landing page for investor services"""

    template_name = "core/investor_services/hub.html"


class InvestmentAdvisoryView(TemplateView):
    """Investment advisory services page with request form"""

    template_name = "core/investor_services/advisory.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["countries"] = MemberStateIPA.objects.filter(is_active=True).order_by(
            "country_name"
        )
        context["sectors"] = Sector.objects.filter(is_active=True).order_by("name")
        return context

    def post(self, request, *args, **kwargs):
        """Handle advisory request form submission"""
        try:
            # Get primary member state (use first selected country or default)
            countries_list = request.POST.getlist("countries", [])
            if countries_list:
                member_state = MemberStateIPA.objects.get(slug=countries_list[0])
            else:
                # Default to first active IPA if none selected
                member_state = MemberStateIPA.objects.filter(is_active=True).first()

            # Get sector (use first selected sector or None)
            sectors_list = request.POST.getlist("sectors", [])
            sector_of_interest = None
            if sectors_list:
                sector_of_interest = Sector.objects.filter(slug=sectors_list[0]).first()

            # Create inquiry using existing model structure
            full_name = f"{request.POST.get('investor_first_name', '')} {request.POST.get('investor_last_name', '')}".strip()

            # Build detailed message
            project_desc = request.POST.get("project_description", "")
            advisory_type = request.POST.get("advisory_type", "")
            investment_capacity = request.POST.get("investment_capacity", "")
            decision_timeline = request.POST.get("decision_timeline", "")
            additional_msg = request.POST.get("message", "")

            message_parts = []
            if advisory_type:
                message_parts.append(f"Advisory Type: {advisory_type}")
            if investment_capacity:
                message_parts.append(f"Investment Capacity: {investment_capacity}")
            if decision_timeline:
                message_parts.append(f"Decision Timeline: {decision_timeline}")
            if project_desc:
                message_parts.append(f"\nProject Description:\n{project_desc}")
            if additional_msg:
                message_parts.append(f"\nAdditional Information:\n{additional_msg}")
            if countries_list:
                message_parts.append(f"\nPreferred Countries: {', '.join(countries_list)}")
            if sectors_list:
                message_parts.append(f"\nPreferred Sectors: {', '.join(sectors_list)}")

            full_message = "\n\n".join(message_parts)

            inquiry = InvestorInquiry.objects.create(
                member_state=member_state,
                inquiry_type="other",  # or 'general'
                full_name=full_name,
                email=request.POST.get("investor_email", ""),
                phone=request.POST.get("investor_phone", ""),
                company_name=request.POST.get("company_name", ""),
                company_country=request.POST.get("investor_country", ""),
                sector_of_interest=sector_of_interest,
                estimated_investment=investment_capacity,
                subject=f"Investment Advisory Request - {advisory_type}",
                message=full_message,
                ip_address=request.META.get(
                    "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR")
                ),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            )

            return JsonResponse(
                {
                    "success": True,
                    "reference": inquiry.reference_number,
                    "message": "Advisory request submitted successfully!",
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class IPAConnectionHubView(TemplateView):
    """IPA directory and connection page"""

    template_name = "core/investor_services/ipa_connection.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ipas"] = (
            MemberStateIPA.objects.filter(is_active=True)
            .prefetch_related("ipa_users")
            .order_by("country_name")
        )
        return context


class InvestorToolkitView(TemplateView):
    """Interactive investor toolkit with calculators"""

    template_name = "core/investor_services/toolkit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["countries"] = MemberStateIPA.objects.filter(is_active=True).order_by(
            "country_name"
        )
        context["sectors"] = Sector.objects.filter(is_active=True).order_by("name")
        return context


class ResourcesGuidesView(TemplateView):
    """Resources and guides library"""

    template_name = "core/investor_services/resources.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sectors"] = Sector.objects.filter(is_active=True).order_by("name")
        context["countries"] = MemberStateIPA.objects.filter(is_active=True).order_by(
            "country_name"
        )
        return context


class SiteVisitCoordinationView(TemplateView):
    """Site visit coordination and request page"""

    template_name = "core/investor_services/site_visits.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["countries"] = MemberStateIPA.objects.filter(is_active=True).order_by(
            "country_name"
        )
        context["sectors"] = Sector.objects.filter(is_active=True).order_by("name")
        return context

    def post(self, request, *args, **kwargs):
        """Handle site visit request form submission"""
        try:
            # Get primary member state (use first selected country)
            countries_list = request.POST.getlist("countries", [])
            if countries_list:
                member_state = MemberStateIPA.objects.get(slug=countries_list[0])
            else:
                member_state = MemberStateIPA.objects.filter(is_active=True).first()

            # Get sector
            sectors_list = request.POST.getlist("sectors", [])
            sector_of_interest = None
            if sectors_list:
                sector_of_interest = Sector.objects.filter(slug=sectors_list[0]).first()

            # Build detailed message
            full_name = (
                f"{request.POST.get('first_name', '')} {request.POST.get('last_name', '')}".strip()
            )
            visit_purpose = request.POST.getlist("visit_purpose", [])
            date_from = request.POST.get("preferred_date_from", "")
            date_to = request.POST.get("preferred_date_to", "")
            duration = request.POST.get("duration_days", "")
            num_people = request.POST.get("number_of_people", "")
            facilities = request.POST.get("specific_facilities", "")
            special_req = request.POST.get("special_requirements", "")

            message_parts = [
                f"SITE VISIT REQUEST",
                f"\nVisit Purpose: {', '.join(visit_purpose)}",
                f"Preferred Dates: {date_from} to {date_to}",
                f"Duration: {duration} days",
                f"Number of People: {num_people}",
                f"\nCountries to Visit: {', '.join(countries_list)}",
            ]

            if sectors_list:
                message_parts.append(f"Sectors of Interest: {', '.join(sectors_list)}")
            if facilities:
                message_parts.append(f"\nSpecific Facilities:\n{facilities}")
            if special_req:
                message_parts.append(f"\nSpecial Requirements:\n{special_req}")

            full_message = "\n".join(message_parts)

            inquiry = InvestorInquiry.objects.create(
                member_state=member_state,
                inquiry_type="site_visit",
                full_name=full_name,
                email=request.POST.get("email", ""),
                phone=request.POST.get("phone", ""),
                company_name=request.POST.get("company_name", ""),
                company_country=request.POST.get("country", ""),
                sector_of_interest=sector_of_interest,
                estimated_investment=request.POST.get("investment_capacity", ""),
                subject=f"Site Visit Request - {', '.join(countries_list[:2])}",
                message=full_message,
                ip_address=request.META.get(
                    "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR")
                ),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            )

            return JsonResponse(
                {
                    "success": True,
                    "reference": inquiry.reference_number,
                    "message": "Site visit request submitted successfully!",
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


# AJAX endpoints for toolkit calculators

# Disclaimer appended to all calculator results — clearly marks outputs as estimates
_INDICATIVE_DISCLAIMER = (
    "These figures are indicative estimates only and are provided for illustrative "
    "purposes. They do not constitute financial, legal, or investment advice. "
    "Actual incentives, costs, and returns will vary by jurisdiction, project scope, "
    "and prevailing market conditions. Please consult the relevant Investment Promotion "
    "Agency and qualified advisors before making any investment decision."
)


@require_http_methods(["POST"])
def incentive_calculator_ajax(request):
    """
    Calculate indicative investment incentives.

    Note: figures are based on representative regional averages and are
    for illustrative purposes only (see disclaimer in response).
    """
    try:
        country_slug = request.POST.get("country")
        sector_slug = request.POST.get("sector")
        investment_amount = float(request.POST.get("investment_amount", 0))

        # Representative averages — replace with live DB data when incentive
        # tables are populated in MemberStateIPA / Sector models.
        tax_holiday_savings = investment_amount * 0.25 * 5  # 25% tax rate, 5 years
        import_duty_waiver = investment_amount * 0.15
        land_cost_reduction = investment_amount * 0.05
        total_incentives = tax_holiday_savings + import_duty_waiver + land_cost_reduction

        return JsonResponse(
            {
                "success": True,
                "indicative": True,
                "disclaimer": _INDICATIVE_DISCLAIMER,
                "results": {
                    "tax_holiday_savings": f"${tax_holiday_savings:,.2f}",
                    "import_duty_waiver": f"${import_duty_waiver:,.2f}",
                    "land_cost_reduction": f"${land_cost_reduction:,.2f}",
                    "total_incentives": f"${total_incentives:,.2f}",
                    "effective_investment": f"${investment_amount - total_incentives:,.2f}",
                },
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@require_http_methods(["POST"])
def cost_comparison_ajax(request):
    """
    Compare indicative operating costs across countries.

    Note: figures are based on representative regional averages and are
    for illustrative purposes only (see disclaimer in response).
    """
    try:
        countries = request.POST.getlist("countries[]")

        # Representative averages — replace with live DB data when cost
        # tables are populated in MemberStateIPA model.
        results = {}
        base_costs = {
            "labor": [800, 1200, 950, 1100],
            "utilities": [150, 200, 180, 160],
            "rent": [2000, 3500, 2500, 2800],
        }

        for i, country in enumerate(countries[:4]):
            results[country] = {
                "labor_monthly_usd": base_costs["labor"][i % 4],
                "utilities_monthly_usd": base_costs["utilities"][i % 4],
                "rent_sqm_usd": base_costs["rent"][i % 4],
            }

        return JsonResponse(
            {
                "success": True,
                "indicative": True,
                "disclaimer": _INDICATIVE_DISCLAIMER,
                "results": results,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@require_http_methods(["POST"])
def roi_estimator_ajax(request):
    """
    Estimate indicative ROI for an investment.

    Note: figures are based on representative sector multipliers and are
    for illustrative purposes only (see disclaimer in response).
    """
    try:
        investment_amount = float(request.POST.get("investment_amount", 0))
        sector_slug = request.POST.get("sector")
        timeline_months = int(request.POST.get("timeline", 36))

        # Representative sector multipliers — replace with live DB benchmarks
        # when sector performance data is available.
        sector_multipliers = {
            "default": 1.15,
            "agriculture": 1.20,
            "energy": 1.25,
            "manufacturing": 1.18,
            "ict": 1.30,
        }

        multiplier = sector_multipliers.get(sector_slug, sector_multipliers["default"])
        expected_revenue = investment_amount * multiplier * (timeline_months / 12)
        net_profit = expected_revenue * 0.15
        roi_percentage = (net_profit / investment_amount) * 100
        breakeven_months = int((investment_amount / (net_profit / (timeline_months / 12))))

        return JsonResponse(
            {
                "success": True,
                "indicative": True,
                "disclaimer": _INDICATIVE_DISCLAIMER,
                "results": {
                    "investment_amount": f"${investment_amount:,.2f}",
                    "expected_revenue": f"${expected_revenue:,.2f}",
                    "estimated_profit": f"${net_profit:,.2f}",
                    "roi_percentage": f"{roi_percentage:.1f}%",
                    "breakeven_months": breakeven_months,
                    "timeline_months": timeline_months,
                },
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
