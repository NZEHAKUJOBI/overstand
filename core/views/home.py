"""
Home page view for IPAWAS
"""
import json

from django.core.cache import cache
from django.db.models import Avg, Count, Sum
from django.shortcuts import render

from core.geo import get_visitor_ecowas_iso3
from knowledge_hub.models import NewsArticle
from members.models import MemberStateIPA, SuccessStory

# Cache TTL constants
_BASE_TTL = 60 * 15       # 15 minutes — non-personalised data
_OPP_TTL = 60 * 10        # 10 minutes — per-country opportunity lists
_BASE_KEY = "homepage_base"
_OPP_KEY = "homepage_opps_{iso3}"


def _format_population(total):
    """Format total population for display (e.g. 331_000_000 → '331M+')."""
    if not total:
        return "350M+"
    millions = total / 1_000_000
    return f"{millions:.0f}M+"


def _format_gdp(total):
    """Format combined GDP for display. `total` is Sum of gdp fields stored in raw USD."""
    if not total:
        return "$650B+"
    # gdp field stores raw USD (e.g. 252_000_000_000 = $252B); convert to billions
    billions = float(total) / 1_000_000_000
    if billions >= 1_000:
        return f"${billions / 1_000:.1f}T+"
    return f"${billions:.0f}B+"


def _format_growth(avg):
    """Format average GDP growth rate (e.g. Decimal('5.8') → '5.8%')."""
    if not avg:
        return "6.2%"
    return f"{float(avg):.1f}%"


def _get_personalized_opportunities(visitor_iso3, limit=6):
    """
    Return up to `limit` active published opportunities.
    If visitor is from an ECOWAS country, their country's opportunities
    come first (up to 3), then the rest fills to the limit.
    Falls back gracefully to latest global if anything fails.
    """
    try:
        from opportunities.models import InvestmentOpportunity

        base_qs = (
            InvestmentOpportunity.objects.filter(status="active", published=True)
            .select_related("primary_country", "primary_sector")
            .only(
                "id", "title", "slug", "summary", "thumbnail_image",
                "investment_required_min", "investment_required_max",
                "priority_level", "featured", "published_date",
                "primary_country__country_name", "primary_country__flag_emoji",
                "primary_country__slug", "primary_country__country_code",
                "primary_sector__name", "primary_sector__emoji",
            )
            .order_by("-featured", "-priority_level", "-published_date")
        )

        total_count = base_qs.count()

        if visitor_iso3:
            local = list(
                base_qs.filter(primary_country__country_code=visitor_iso3)[:3]
            )
            local_ids = [o.id for o in local]
            others = list(base_qs.exclude(id__in=local_ids)[: limit - len(local)])
            return local + others, total_count

        return list(base_qs[:limit]), total_count

    except Exception:
        return [], 0


def _get_personalized_states(all_states, visitor_iso3):
    """
    Reorder the already-fetched member states list so the visitor's
    own country card appears first. No extra DB query needed.
    """
    if not visitor_iso3:
        return all_states

    local = [s for s in all_states if s.country_code == visitor_iso3]
    others = [s for s in all_states if s.country_code != visitor_iso3]
    return local + others


def _get_personalized_stories_from_pool(pool, visitor_iso3, limit=3):
    """
    Reorder a pre-fetched pool of SuccessStory objects so the visitor's
    country story appears first. No DB query — works on an in-memory list.
    """
    if not visitor_iso3 or not pool:
        return pool[:limit]
    local = [s for s in pool if s.member_state.country_code == visitor_iso3]
    others = [s for s in pool if s.member_state.country_code != visitor_iso3]
    return (local + others)[:limit]


def _find_visitor_state(states_list, visitor_iso3):
    """Find the visitor's MemberStateIPA from an already-fetched list (no extra query)."""
    if not visitor_iso3:
        return None
    for state in states_list:
        if state.country_code == visitor_iso3:
            return state
    return None


def index(request):
    """
    Home page with interactive West Africa map and dynamic, geo-personalized content.

    Content ordering:
    - ECOWAS visitors: their country's opportunities/stories/state card appear first
    - Non-ECOWAS or undetected visitors: global ordering (featured → priority → date)
    - Geo lookup fails silently — page always renders with graceful fallback
    """
    # --- Geo-detection (always safe — returns None on failure) ---
    visitor_iso3 = get_visitor_ecowas_iso3(request)

    # --- Base context: cached 15 min (same for all visitors) ---
    base = cache.get(_BASE_KEY)
    if base is None:
        member_states_qs = (
            MemberStateIPA.objects.filter(is_active=True)
            .select_related()
            .prefetch_related("sectors__sector")
        )
        member_states_list = list(member_states_qs)

        agg = MemberStateIPA.objects.filter(is_active=True).aggregate(
            total_population=Sum("population"),
            total_gdp=Sum("gdp"),
            avg_growth=Avg("gdp_growth_rate"),
            active_count=Count("id"),
        )

        featured_stories_raw = list(
            SuccessStory.objects.filter(published=True)
            .select_related("member_state", "sector")
            .order_by("-featured", "-year")[:6]   # fetch 6 so geo can pick best 3
        )

        latest_news = list(
            NewsArticle.objects.filter(published=True, category="investment_news")
            .select_related("featured_media")
            .order_by("-publication_date")[:3]
        )

        # Build country_data dict for D3 map
        country_data = {}
        for state in member_states_list:
            all_sectors = list(state.sectors.all())
            priority_sectors = [s for s in all_sectors if s.is_priority][:4]
            sectors_html = '<div class="d-flex flex-wrap">'
            for ms_sector in priority_sectors:
                sector_name = ms_sector.sector.name
                emoji = ms_sector.sector.emoji if hasattr(ms_sector.sector, "emoji") else ""
                sectors_html += f'<span class="sector-tag">{emoji} {sector_name}</span>'
            sectors_html += "</div>"
            pop_display = state.population_display or (
                f"{state.population / 1_000_000:.1f}M" if state.population else "N/A"
            )
            gdp_display = state.gdp_display or (
                f"${float(state.gdp):.1f}B" if state.gdp else "N/A"  # gdp stored in USD billions
            )
            country_data[state.slug] = {
                "name": state.country_name,
                "code": (state.country_code or "").lower()[:2],
                "capital": state.capital_city or "",
                "population": pop_display,
                "gdp": gdp_display,
                "sectors": sectors_html,
            }

        base = {
            "member_states_list": member_states_list,
            "agg": agg,
            "featured_stories_raw": featured_stories_raw,
            "latest_news": latest_news,
            "country_data_json": json.dumps(country_data),
        }
        cache.set(_BASE_KEY, base, _BASE_TTL)

    member_states_list = base["member_states_list"]
    agg = base["agg"]

    # --- Stats ---
    opp_count = base.get("opp_count", 0)
    stats = {
        "population_display": _format_population(agg["total_population"]),
        "population_raw": int(agg["total_population"] / 1_000_000) if agg["total_population"] else 350,
        "gdp_display": _format_gdp(agg["total_gdp"]),
        "growth_display": _format_growth(agg["avg_growth"]),
        "active_members": agg["active_count"] or 12,
        "opportunities_count": opp_count,
    }

    # --- Personalized opportunities: cached per country code (10 min) ---
    opp_cache_key = _OPP_KEY.format(iso3=visitor_iso3 or "global")
    cached_opps = cache.get(opp_cache_key)
    if cached_opps is None:
        featured_opportunities, opp_count = _get_personalized_opportunities(visitor_iso3)
        cache.set(opp_cache_key, (featured_opportunities, opp_count), _OPP_TTL)
        stats["opportunities_count"] = opp_count
    else:
        featured_opportunities, opp_count = cached_opps
        stats["opportunities_count"] = opp_count

    # --- Featured states: geo-reordered from already-cached list (no DB hit) ---
    featured_states_raw = (
        [s for s in member_states_list if s.featured]
        or member_states_list
    )[:6]
    featured_states = _get_personalized_states(featured_states_raw, visitor_iso3)

    # --- Visitor's own state (for personalised headings — no DB hit) ---
    visitor_state = _find_visitor_state(member_states_list, visitor_iso3)

    # --- Success stories: geo-reorder the cached pool ---
    featured_stories = _get_personalized_stories_from_pool(
        base["featured_stories_raw"], visitor_iso3
    )

    context = {
        "country_data_json": base["country_data_json"],
        "member_states": member_states_list,
        "latest_news": base["latest_news"],
        "stats": stats,
        "featured_opportunities": featured_opportunities,
        "featured_states": featured_states,
        "featured_stories": featured_stories,
        # Geo context for template personalisation
        "visitor_iso3": visitor_iso3,
        "visitor_state": visitor_state,
    }

    return render(request, "core/index.html", context)
