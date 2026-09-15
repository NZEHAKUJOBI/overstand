"""
Class-Based Views for IPAWAS Members App

App Name: members (not member_states)

All views follow Django best practices and use the service layer
for business logic.
"""

import json

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, FormView, ListView, TemplateView
from django_ratelimit.decorators import ratelimit

from members.forms import CountryComparisonForm, InvestorInquiryForm, MemberStateFilterForm
from members.models import InvestmentIncentive, MemberStateIPA, SuccessStory
from members.services import (
    CacheService,
    ComparisonService,
    DataService,
    InquiryService,
    MemberStateService,
)


class MemberStatesHubView(TemplateView):
    """
    Member States Hub/Landing Page
    URL: /members/

    Features:
    - Interactive regional map
    - Filtering & sorting
    - Grid/list view toggle
    - Regional statistics dashboard
    - Country comparison widget
    """

    template_name = "members/hub.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filter parameters FIRST
        language = self.request.GET.get("language")
        region = self.request.GET.get("region")
        gdp_range = self.request.GET.get("gdp_range")
        population_range = self.request.GET.get("population_range")
        search = self.request.GET.get("search")
        sort_by = self.request.GET.get("sort", "alphabetical")

        # Start with all active member states
        member_states = MemberStateIPA.objects.filter(is_active=True)

        # Apply language filter with mapping
        if language:
            language_mapping = {"en": "english", "fr": "french", "pt": "portuguese"}
            mapped_language = language_mapping.get(language, language)
            member_states = member_states.filter(official_language=mapped_language)

        # Apply region filter
        if region:
            member_states = member_states.filter(geographic_region=region)

        # Apply GDP range filter.
        # gdp field stores USD in BILLIONS (e.g. 87.5 = $87.5B), so thresholds
        # are plain billion values — not raw dollar amounts.
        if gdp_range:
            if gdp_range == "large":
                member_states = member_states.filter(gdp__gte=50)   # >= $50B
            elif gdp_range == "medium":
                member_states = member_states.filter(gdp__gte=20, gdp__lt=50)  # $20B–$50B
            elif gdp_range == "small":
                member_states = member_states.filter(gdp__lt=20)    # < $20B

        # Apply population range filter
        if population_range:
            if population_range == "large":
                member_states = member_states.filter(population__gte=50_000_000)
            elif population_range == "medium":
                member_states = member_states.filter(
                    population__gte=10_000_000, population__lt=50_000_000
                )
            elif population_range == "small":
                member_states = member_states.filter(population__lt=10_000_000)

        # Apply search filter
        if search:
            member_states = member_states.filter(
                Q(country_name__icontains=search)
                | Q(ipa_full_name__icontains=search)
                | Q(ipa_acronym__icontains=search)
                | Q(capital_city__icontains=search)
            )

        # Map user-friendly sort names to actual field names
        sort_mapping = {
            "alphabetical": "country_name",
            "alphabetical_desc": "-country_name",
            "population": "population",
            "population_desc": "-population",
            "gdp": "gdp",
            "gdp_desc": "-gdp",
        }

        # Apply sorting
        actual_sort_field = sort_mapping.get(sort_by, "country_name")
        member_states = (
            member_states.select_related()
            .prefetch_related("sectors__sector")
            .order_by(actual_sort_field)
        )

        # Build country data dictionary for JavaScript (using filtered results).
        # Use Python-side filtering on already-prefetched sectors to avoid N+1 queries.
        country_data = {}
        for state in member_states:
            # Filter priority sectors in Python — prefetch cache is already populated
            all_sectors = list(state.sectors.all())
            priority_sectors = [s for s in all_sectors if s.is_priority][:4]

            # Format sectors HTML
            sectors_html = '<div class="d-flex flex-wrap">'
            for ms_sector in priority_sectors:
                sector_name = ms_sector.sector.name
                emoji = ms_sector.sector.emoji if hasattr(ms_sector.sector, "emoji") else ""
                sectors_html += f'<span class="sector-tag">{emoji} {sector_name}</span>'
            sectors_html += "</div>"

            # Build country data
            country_data[state.slug] = {
                "name": state.country_name,
                "code": state.country_code.lower()[:2],
                "capital": state.capital_city,
                "population": state.population_display or f"{state.population / 1_000_000:.1f}M",
                "gdp": state.formatted_gdp,
                "sectors": sectors_html,
            }

        context["country_data_json"] = json.dumps(country_data)
        context["member_states"] = member_states

        # Regional statistics — served from cache (24 h TTL)
        context["regional_stats"] = CacheService.get_or_set_statistics()

        # Featured countries — served from cache (6 h TTL)
        context["featured_states"] = MemberStateService.get_featured_member_states(limit=3)

        # Filter form
        context["filter_form"] = MemberStateFilterForm(
            initial={
                "language": language,
                "region": region,
                "gdp_range": gdp_range,
                "population_range": population_range,
                "search": search,
                "sort": sort_by,
            }
        )

        # View preferences
        context["view_mode"] = self.request.GET.get("view", "grid")
        context["sort_by"] = sort_by

        # Meta tags
        context["page_title"] = "IPAWAS Member States - Investment Opportunities Across West Africa"
        context["meta_description"] = (
            "Explore investment opportunities across 12 ECOWAS member states. "
            "Connect with Investment Promotion Agencies and discover incentives, "
            "sectors, and success stories in West Africa."
        )

        return context


class MemberStateDetailView(DetailView):
    """
    Individual Country Detail Page
    URL: /members/<country-slug>/

    7-tab interface:
    1. Overview
    2. Priority Sectors
    3. Investment Opportunities
    4. Incentives & Benefits
    5. Success Stories
    6. Economic Data & Charts
    7. Contact IPA
    """

    model = MemberStateIPA
    template_name = "members/detail.html"
    context_object_name = "member_state"
    slug_url_kwarg = "country_slug"
    slug_field = "slug"

    def get_queryset(self):
        """Only return active member states"""
        return MemberStateIPA.objects.filter(is_active=True)

    def get_object(self, queryset=None):
        """Get member state with caching — avoids a DB hit on every page load"""
        slug = self.kwargs.get(self.slug_url_kwarg)
        member_state = CacheService.get_or_set_member_state(slug)

        if not member_state:
            # Cache miss or inactive state — fall back to regular query
            member_state = super().get_object(queryset)

        return member_state

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.object

        # Active tab (from URL parameter)
        context["active_tab"] = self.request.GET.get("tab", "overview")

        # Priority sectors
        context["priority_sectors"] = MemberStateService.get_priority_sectors_for_state(
            member_state
        )

        # Investment opportunities (if opportunities app exists)
        # Single query — evaluate the full list, then slice for display
        try:
            from opportunities.models import InvestmentOpportunity

            opp_qs = list(
                InvestmentOpportunity.objects.filter(
                    primary_country=member_state, status="active", published=True
                ).select_related("primary_sector")
            )
            context["opportunities"] = opp_qs[:9]
            context["opportunities_count"] = len(opp_qs)
        except ImportError:
            context["opportunities"] = []
            context["opportunities_count"] = 0

        # Incentives
        context["incentives"] = (
            member_state.incentives.filter(is_active=True)
            .select_related("document_file")
            .prefetch_related("applicable_sectors")
        )

        # Success stories
        context["success_stories"] = member_state.success_stories.filter(
            published=True
        ).select_related("sector")[:3]

        # FDI time series data
        context["fdi_data"] = DataService.get_fdi_time_series(
            member_state, data_type="fdi_inflow", years=5
        )

        # All FDI data for charts
        context["all_fdi_data"] = DataService.get_all_fdi_data_for_state(member_state)

        # Sector distribution
        context["sector_distribution"] = DataService.calculate_sector_distribution(member_state)

        # Staff members
        context["staff"] = member_state.staff.filter(is_active=True, show_on_website=True).order_by(
            "display_order"
        )

        # Inquiry form
        context["inquiry_form"] = InvestorInquiryForm()

        # Success message if inquiry was submitted
        if self.request.GET.get("success") == "1":
            context["inquiry_success"] = True

        # Meta tags
        context["page_title"] = f"{member_state.country_name} Investment Opportunities | IPAWAS"
        context["meta_description"] = (
            f"Discover investment opportunities in {member_state.country_name}. "
            f"Connect with {member_state.ipa_acronym} for guidance on investing "
            f"in West Africa's {self._get_country_superlative(member_state)} market."
        )

        return context

    def _get_country_superlative(self, member_state):
        """Generate superlative description for country"""
        # Simple logic - can be enhanced
        if member_state.population > 100_000_000:
            return "largest"
        elif member_state.gdp > 100:
            return "leading"
        else:
            return "dynamic"


class CountryComparisonView(TemplateView):
    """
    Country Comparison Tool
    URL: /members/compare/?countries=nigeria,ghana,senegal

    Compare 2-4 countries side-by-side
    """

    template_name = "members/compare.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Handle both multi-value checkbox form (?countries=a&countries=b)
        # and comma-separated link format (?countries=a,b)
        raw_list = self.request.GET.getlist("countries")
        if len(raw_list) == 1 and "," in raw_list[0]:
            raw_list = raw_list[0].split(",")
        country_slugs = [slug.strip() for slug in raw_list if slug.strip()]

        if country_slugs and len(country_slugs) >= 2:
            # Generate comparison data
            comparison = ComparisonService.compare_countries(country_slugs)

            if "error" not in comparison:
                context["comparison"] = comparison
                context["has_comparison"] = True
            else:
                context["error_message"] = comparison["error"]
                context["has_comparison"] = False
        else:
            context["has_comparison"] = False

        # All active countries for selection
        context["all_member_states"] = MemberStateService.get_active_member_states()

        # Comparison form
        context["comparison_form"] = CountryComparisonForm()

        # Selected slugs for pre-selection
        context["selected_slugs"] = country_slugs

        # Meta tags
        context["page_title"] = "Compare IPAWAS Member States | Investment Analysis"
        context["meta_description"] = (
            "Compare investment opportunities, economic indicators, and business climate "
            "across West African countries. Make informed investment decisions."
        )

        return context


@method_decorator(
    ratelimit(key="ip", rate="5/h", method="POST", block=True),
    name="dispatch",
)
class InquiryCreateView(FormView):
    """
    Handle investor inquiry form submissions
    URL: /members/<country-slug>/contact/

    Creates InvestorInquiry and sends notifications.

    Bot protection (Option 2 — rate limiting):
      Max 5 POST requests per IP per hour.  Legitimate investors won't hit
      this ceiling; bots running mass submissions will be blocked with 403.
    """

    form_class = InvestorInquiryForm
    template_name = "members/detail.html"

    def dispatch(self, request, *args, **kwargs):
        """Get member state before processing"""
        country_slug = self.kwargs.get("country_slug")
        self.member_state = get_object_or_404(MemberStateIPA, slug=country_slug, is_active=True)
        # GET requests have no business here — redirect to the contact section
        if request.method == "GET":
            return redirect(f"/members/{country_slug}/?tab=contact#contact-section")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Process valid form submission"""
        # Prepare inquiry data
        inquiry_data = form.cleaned_data.copy()
        inquiry_data["ip_address"] = self.get_client_ip()
        inquiry_data["user_agent"] = self.request.META.get("HTTP_USER_AGENT", "")

        # Create inquiry via service
        success, message, inquiry = InquiryService.create_inquiry(self.member_state, inquiry_data)

        if success:
            messages.success(self.request, message)
        else:
            messages.error(self.request, message)

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request, "Please correct the errors in the form below.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect back to country page with contact tab"""
        country_slug = self.kwargs.get("country_slug")
        return f"/members/{country_slug}/#contact-section"

    def get_client_ip(self):
        """Extract client IP address"""
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        return ip


class FilterMemberStatesView(ListView):
    """
    AJAX endpoint for filtering member states
    Returns JSON for dynamic filtering

    URL: /members/api/filter/?language=english&region=west_coast
    """

    model = MemberStateIPA

    def get_queryset(self):
        """Apply filters from GET parameters"""
        language = self.request.GET.get("language")
        region = self.request.GET.get("region")
        gdp_range = self.request.GET.get("gdp_range")
        population_range = self.request.GET.get("population_range")
        search = self.request.GET.get("search")

        return MemberStateService.filter_member_states(
            language=language,
            region=region,
            gdp_range=gdp_range,
            population_range=population_range,
            search_query=search,
        )

    def render_to_response(self, context):
        """Return JSON response"""
        # Eagerly prefetch sectors so the loop below makes zero extra DB queries
        queryset = self.get_queryset().prefetch_related("sectors__sector")

        # Serialize member states
        member_states_data = []
        for state in queryset:
            # Use Python-side filter on prefetched sectors (no extra queries)
            priority_sectors = [s for s in state.sectors.all() if s.is_priority][:4]
            member_states_data.append(
                {
                    "country_name": state.country_name,
                    "slug": state.slug,
                    "ipa_acronym": state.ipa_acronym,
                    "ipa_full_name": state.ipa_full_name,
                    "population_display": state.population_display,
                    "gdp_display": state.formatted_gdp,
                    "capital_city": state.capital_city,
                    "flag_emoji": state.flag_emoji,
                    "card_image": state.card_image,
                    "official_language": state.get_official_language_display(),
                    "url": f"/members/{state.slug}/",
                    "priority_sectors": [s.sector.name for s in priority_sectors],
                    "opportunities_count": state.get_opportunities_count(),
                }
            )

        return JsonResponse({"member_states": member_states_data, "count": len(member_states_data)})


class RegionalStatisticsView(TemplateView):
    """
    AJAX endpoint for regional statistics
    Returns JSON for dashboard updates

    URL: /members/api/statistics/
    """

    def render_to_response(self, context):
        """Return JSON response with statistics — served from cache"""
        stats = CacheService.get_or_set_statistics()
        return JsonResponse(stats)


# Additional utility views


class MemberStatesByLanguageView(TemplateView):
    """
    View member states grouped by language
    URL: /members/by-language/
    """

    template_name = "members/by_language.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["states_by_language"] = MemberStateService.get_member_states_by_language()
        return context


class MemberStateSearchView(ListView):
    """
    Search member states
    URL: /members/search/?q=nigeria
    """

    model = MemberStateIPA
    template_name = "members/search_results.html"
    context_object_name = "results"
    paginate_by = 12

    def get_queryset(self):
        """Search across multiple fields"""
        query = self.request.GET.get("q", "")

        if query:
            return MemberStateService.filter_member_states(search_query=query)
        return MemberStateIPA.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context
