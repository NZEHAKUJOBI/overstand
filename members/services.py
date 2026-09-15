"""
Service Layer for IPAWAS Members App

This module contains business logic for member states operations:
- MemberStateService: Core operations for member states
- InquiryService: Handle investor inquiries and notifications
- DataService: Aggregate and format data for displays
- ComparisonService: Country comparison logic
- CacheService: Performance optimization

Following domain-driven design principles, business logic is
separated from views and models.

App Name: members (not member_states)
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.conf import settings

logger = logging.getLogger(__name__)
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db.models import Avg, Count, Prefetch, Q, Sum
from django.template.loader import render_to_string
from django.utils import timezone

# Import from members app
from members.models import (
    FDIDataPoint,
    InvestmentIncentive,
    InvestorInquiry,
    IPAStaff,
    MemberStateIPA,
    MemberStateSector,
    SuccessStory,
)


class MemberStateService:
    """
    Core service for member state operations.
    Handles queries, filtering, and data aggregation.
    """

    @staticmethod
    def get_active_member_states(order_by="country_name"):
        """
        Get all active member states (excluding Mali, Niger, Burkina Faso).

        Args:
            order_by: Field to order by (default: country_name)

        Returns:
            QuerySet of active MemberStateIPA objects
        """
        return (
            MemberStateIPA.objects.filter(is_active=True)
            .select_related()
            .prefetch_related(
                Prefetch("sectors", queryset=MemberStateSector.objects.select_related("sector"))
            )
            .order_by(order_by)
        )

    @staticmethod
    def get_member_state_by_slug(slug: str):
        """
        Get a single member state by slug with all related data.

        Args:
            slug: Country slug (e.g., 'nigeria')

        Returns:
            MemberStateIPA object or None
        """
        try:
            return (
                MemberStateIPA.objects.select_related()
                .prefetch_related(
                    Prefetch(
                        "sectors",
                        queryset=MemberStateSector.objects.select_related("sector").filter(
                            is_priority=True
                        ),
                    ),
                    Prefetch(
                        "incentives",
                        queryset=InvestmentIncentive.objects.filter(
                            is_active=True
                        ).prefetch_related("applicable_sectors"),
                    ),
                    Prefetch(
                        "success_stories",
                        queryset=SuccessStory.objects.filter(published=True).select_related(
                            "sector"
                        ),
                    ),
                    Prefetch(
                        "staff",
                        queryset=IPAStaff.objects.filter(is_active=True, show_on_website=True),
                    ),
                    "fdi_data",
                )
                .get(slug=slug, is_active=True)
            )
        except MemberStateIPA.DoesNotExist:
            return None

    @staticmethod
    def get_member_state_by_code(country_code: str):
        """
        Get a member state by country code.

        Args:
            country_code: ISO 3166-1 alpha-3 code (e.g., 'NGA')

        Returns:
            MemberStateIPA object or None
        """
        try:
            return MemberStateIPA.objects.get(country_code=country_code, is_active=True)
        except MemberStateIPA.DoesNotExist:
            return None

    @staticmethod
    def filter_member_states(
        language: Optional[str] = None,
        region: Optional[str] = None,
        gdp_range: Optional[str] = None,
        population_range: Optional[str] = None,
        search_query: Optional[str] = None,
        featured_only: bool = False,
    ):
        """
        Filter member states based on multiple criteria.

        Args:
            language: 'english', 'french', 'portuguese', or None
            region: 'west_coast', 'sahel', 'gulf_of_guinea', or None
            gdp_range: 'large', 'medium', 'small', or None
            population_range: 'large', 'medium', 'small', or None
            search_query: Text search in country name or IPA name
            featured_only: Only return featured member states

        Returns:
            Filtered QuerySet
        """
        queryset = MemberStateIPA.objects.filter(is_active=True)

        # Featured filter
        if featured_only:
            queryset = queryset.filter(featured=True)

        # Language filter
        if language and language in ["english", "french", "portuguese"]:
            queryset = queryset.filter(official_language=language)

        # Region filter
        if region and region in ["west_coast", "sahel", "gulf_of_guinea"]:
            queryset = queryset.filter(geographic_region=region)

        # GDP range filter
        if gdp_range:
            if gdp_range == "large":
                queryset = queryset.filter(gdp__gte=50)
            elif gdp_range == "medium":
                queryset = queryset.filter(gdp__gte=20, gdp__lt=50)
            elif gdp_range == "small":
                queryset = queryset.filter(gdp__lt=20)

        # Population range filter
        if population_range:
            if population_range == "large":
                queryset = queryset.filter(population__gte=50_000_000)
            elif population_range == "medium":
                queryset = queryset.filter(population__gte=10_000_000, population__lt=50_000_000)
            elif population_range == "small":
                queryset = queryset.filter(population__lt=10_000_000)

        # Search filter
        if search_query:
            queryset = queryset.filter(
                Q(country_name__icontains=search_query)
                | Q(ipa_full_name__icontains=search_query)
                | Q(ipa_acronym__icontains=search_query)
                | Q(capital_city__icontains=search_query)
            )

        return queryset.select_related().prefetch_related("sectors__sector")

    @staticmethod
    def get_featured_member_states(limit: int = 3):
        """
        Get featured member states for homepage or special sections.

        Args:
            limit: Maximum number of featured states to return

        Returns:
            QuerySet of featured member states
        """
        cache_key = f"featured_member_states_{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        result = list(
            MemberStateIPA.objects.filter(is_active=True, featured=True)
            .select_related()
            .prefetch_related("sectors__sector")
            .order_by("display_order")[:limit]
        )
        cache.set(cache_key, result, 60 * 60 * 6)  # 6 hours
        return result

    @staticmethod
    def get_member_state_statistics():
        """
        Get aggregate statistics across all active member states.
        Useful for dashboard displays.

        Returns:
            Dict with aggregate stats
        """
        cache_key = "member_states_statistics"
        cached_stats = cache.get(cache_key)
        if cached_stats:
            return cached_stats

        active_states = MemberStateIPA.objects.filter(is_active=True)

        # Calculate aggregates
        aggregates = active_states.aggregate(
            total_population=Sum("population"),
            total_gdp=Sum("gdp"),
            total_fdi=Sum("fdi_inflows"),
            avg_gdp_growth=Avg("gdp_growth_rate"),
            total_countries=Count("id"),
        )

        # Count opportunities (if opportunities app exists)
        try:
            from opportunities.models import InvestmentOpportunity

            total_opportunities = InvestmentOpportunity.objects.filter(
                primary_country__in=active_states, status="active", published=True
            ).count()
        except ImportError:
            total_opportunities = 0

        # Count by language
        language_distribution = active_states.values("official_language").annotate(
            count=Count("id")
        )

        # gdp field stores raw USD (e.g. 252_000_000_000 = $252B); divide by 1e9 for billions.
        total_gdp_billions = float(aggregates["total_gdp"] or 0) / 1_000_000_000

        # Format GDP display (billions or trillions)
        if total_gdp_billions >= 1_000:
            gdp_display = f"${total_gdp_billions / 1_000:.1f}T"
        else:
            gdp_display = f"${total_gdp_billions:.1f}B"

        total_fdi_millions = float(aggregates["total_fdi"] or 0)
        total_countries = aggregates["total_countries"] or 0

        stats = {
            "total_countries": total_countries,
            "total_members": total_countries,          # alias used in hero & glance sections
            "total_population": aggregates["total_population"] or 0,
            "total_gdp": aggregates["total_gdp"] or Decimal("0"),
            "total_gdp_billions": round(total_gdp_billions, 1),
            "total_fdi_millions": round(total_fdi_millions, 0),
            "average_gdp_growth": aggregates["avg_gdp_growth"] or Decimal("0"),
            "total_opportunities": total_opportunities,
            "languages": {
                item["official_language"]: item["count"] for item in language_distribution
            },
        }

        # Format for display
        stats["total_population_display"] = f"{stats['total_population'] / 1_000_000:.0f}M+"
        stats["total_gdp_display"] = gdp_display
        stats["avg_growth_display"] = f"{float(stats['average_gdp_growth']):.1f}%"

        # Cache for 24 hours
        cache.set(cache_key, stats, 60 * 60 * 24)

        return stats

    @staticmethod
    def get_member_states_by_language():
        """
        Get member states grouped by official language.

        Returns:
            Dict with language as key and list of member states as value
        """
        member_states = MemberStateIPA.objects.filter(is_active=True).order_by(
            "official_language", "country_name"
        )

        grouped = {"english": [], "french": [], "portuguese": []}

        for state in member_states:
            if state.official_language in grouped:
                grouped[state.official_language].append(state)

        return grouped

    @staticmethod
    def get_priority_sectors_for_state(member_state: MemberStateIPA):
        """
        Get priority sectors for a specific member state.

        Args:
            member_state: MemberStateIPA instance

        Returns:
            QuerySet of MemberStateSector with priority=True
        """
        return (
            member_state.sectors.filter(is_priority=True)
            .select_related("sector")
            .order_by("display_order", "sector__name")
        )


class InquiryService:
    """
    Service for handling investor inquiries.
    Manages form submissions, email notifications, and tracking.
    """

    @staticmethod
    def create_inquiry(
        member_state, inquiry_data: Dict
    ) -> Tuple[bool, str, Optional[InvestorInquiry]]:
        """
        Create a new investor inquiry and send notifications.

        Args:
            member_state: MemberStateIPA instance
            inquiry_data: Dictionary with inquiry details

        Returns:
            Tuple of (success: bool, message: str, inquiry: InvestorInquiry or None)
        """
        try:
            # Create inquiry
            inquiry = InvestorInquiry.objects.create(
                member_state=member_state,
                inquiry_type=inquiry_data.get("inquiry_type"),
                full_name=inquiry_data.get("full_name"),
                email=inquiry_data.get("email"),
                phone=inquiry_data.get("phone", ""),
                company_name=inquiry_data.get("company_name", ""),
                company_country=inquiry_data.get("company_country", ""),
                sector_of_interest_id=inquiry_data.get("sector_of_interest"),
                estimated_investment=inquiry_data.get("estimated_investment", ""),
                subject=inquiry_data.get("subject"),
                message=inquiry_data.get("message"),
                ip_address=inquiry_data.get("ip_address"),
                user_agent=inquiry_data.get("user_agent", ""),
            )

            # Send notifications
            InquiryService._send_inquiry_notifications(inquiry)

            return (
                True,
                f"Your inquiry has been submitted successfully. Reference: {inquiry.reference_number}",
                inquiry,
            )

        except Exception as e:
            return (False, f"An error occurred while processing your inquiry: {str(e)}", None)

    @staticmethod
    def _send_inquiry_notifications(inquiry: InvestorInquiry):
        """
        Send email notifications for new inquiry.

        Args:
            inquiry: InvestorInquiry instance
        """
        # Email to IPA
        try:
            InquiryService._send_ipa_notification(inquiry)
        except Exception as e:
            logger.exception("Error sending IPA notification for inquiry %s: %s", inquiry.reference_number, e)

        # Confirmation email to investor
        try:
            InquiryService._send_investor_confirmation(inquiry)
        except Exception as e:
            logger.exception("Error sending investor confirmation for inquiry %s: %s", inquiry.reference_number, e)

    @staticmethod
    def _send_ipa_notification(inquiry: InvestorInquiry):
        """Send notification email to IPA"""
        subject = f"New Investment Inquiry - {inquiry.reference_number}"

        context = {
            "inquiry": inquiry,
            "member_state": inquiry.member_state,
            "sector": (
                inquiry.sector_of_interest.name if inquiry.sector_of_interest else "Not specified"
            ),
        }

        # HTML email
        try:
            html_message = render_to_string("members/emails/ipa_notification.html", context)
        except Exception:
            html_message = None

        # Plain text email
        text_message = f"""
New Investment Inquiry Received

Reference Number: {inquiry.reference_number}
Date: {inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}

INVESTOR DETAILS:
Name: {inquiry.full_name}
Email: {inquiry.email}
Phone: {inquiry.phone or 'Not provided'}
Company: {inquiry.company_name or 'Not provided'}
Country: {inquiry.company_country or 'Not provided'}

INQUIRY DETAILS:
Type: {inquiry.get_inquiry_type_display()}
Subject: {inquiry.subject}
Sector of Interest: {context['sector']}
Estimated Investment: {inquiry.estimated_investment or 'Not specified'}

MESSAGE:
{inquiry.message}

---
This inquiry was submitted through the IPAWAS Member States Portal.
Please respond to the investor at: {inquiry.email}

View inquiry details in the admin panel.
        """.strip()

        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inquiry.member_state.contact_email],
            cc=[getattr(settings, "CONTACT_EMAIL", "infodesk@ipawas.org")],
        )

        if html_message:
            email.attach_alternative(html_message, "text/html")

        email.send(fail_silently=False)

    @staticmethod
    def _send_investor_confirmation(inquiry: InvestorInquiry):
        """Send confirmation email to investor"""
        subject = f"Inquiry Received - {inquiry.reference_number}"

        context = {
            "inquiry": inquiry,
            "member_state": inquiry.member_state,
        }

        # HTML email
        try:
            html_message = render_to_string("members/emails/investor_confirmation.html", context)
        except Exception:
            html_message = None

        # Plain text email
        text_message = f"""
Dear {inquiry.full_name},

Thank you for your inquiry to {inquiry.member_state.ipa_full_name} ({inquiry.member_state.ipa_acronym}).

Your inquiry has been successfully received and assigned the reference number: {inquiry.reference_number}

INQUIRY DETAILS:
Type: {inquiry.get_inquiry_type_display()}
Subject: {inquiry.subject}
Submitted: {inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}

A representative from {inquiry.member_state.ipa_acronym} will review your inquiry and respond within 2-3 business days.

If you have any questions in the meantime, please contact:
{inquiry.member_state.contact_email}
{inquiry.member_state.contact_phone}

You can also visit their website at: {inquiry.member_state.ipa_website}

Best regards,
{inquiry.member_state.ipa_acronym} Team
via IPAWAS

---
This is an automated confirmation email. Please do not reply directly to this email.
        """.strip()

        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inquiry.email],
        )

        if html_message:
            email.attach_alternative(html_message, "text/html")

        email.send(fail_silently=True)

    @staticmethod
    def get_inquiries_by_status(status: str = "new"):
        """
        Get inquiries filtered by status.

        Args:
            status: 'new', 'in_progress', 'responded', 'closed'

        Returns:
            QuerySet of InvestorInquiry
        """
        return InvestorInquiry.objects.filter(status=status).select_related(
            "member_state", "sector_of_interest", "assigned_to"
        )

    @staticmethod
    def assign_inquiry(inquiry: InvestorInquiry, user):
        """
        Assign inquiry to a user.

        Args:
            inquiry: InvestorInquiry instance
            user: User instance
        """
        inquiry.assigned_to = user
        if inquiry.status == "new":
            inquiry.status = "in_progress"
        inquiry.save(update_fields=["assigned_to", "status", "updated_at"])


class DataService:
    """
    Service for aggregating and formatting data for visualizations.
    Handles FDI data, sector analysis, and trend calculations.
    """

    @staticmethod
    def get_fdi_time_series(member_state: MemberStateIPA, data_type="fdi_inflow", years=5):
        """
        Get FDI time series data for charts.

        Args:
            member_state: MemberStateIPA instance
            data_type: Type of data to retrieve
            years: Number of recent years to include

        Returns:
            List of dictionaries with year and value
        """
        current_year = timezone.now().year
        start_year = current_year - years

        data_points = (
            FDIDataPoint.objects.filter(
                member_state=member_state,
                data_type=data_type,
                year__gte=start_year,
                validation_status="published",
            )
            .order_by("year")
            .values("year", "value", "value_display")
        )

        return list(data_points)

    @staticmethod
    def get_all_fdi_data_for_state(member_state: MemberStateIPA):
        """
        Get all published FDI data for a member state.

        Args:
            member_state: MemberStateIPA instance

        Returns:
            Dict with data_type as key and list of data points as value
        """
        data_points = FDIDataPoint.objects.filter(
            member_state=member_state, validation_status="published"
        ).order_by("data_type", "year")

        grouped = {}
        for point in data_points:
            if point.data_type not in grouped:
                grouped[point.data_type] = []
            grouped[point.data_type].append(
                {
                    "year": point.year,
                    "value": float(point.value),
                    "value_display": point.value_display,
                    "source": point.data_source,
                }
            )

        return grouped

    @staticmethod
    def calculate_sector_distribution(member_state: MemberStateIPA):
        """
        Calculate distribution of opportunities by sector.

        Args:
            member_state: MemberStateIPA instance

        Returns:
            List of dictionaries with sector and count
        """
        try:
            from opportunities.models import InvestmentOpportunity

            distribution = (
                InvestmentOpportunity.objects.filter(
                    primary_country=member_state, status="active", published=True
                )
                .values("primary_sector__name")
                .annotate(count=Count("id"))
                .order_by("-count")
            )

            return list(distribution)
        except ImportError:
            return []

    @staticmethod
    def get_regional_comparison_data(member_states: List[MemberStateIPA]):
        """
        Get comparison data for multiple member states.

        Args:
            member_states: List of MemberStateIPA instances

        Returns:
            Dictionary with comparison metrics
        """
        comparison = {
            "countries": [],
            "gdp": [],
            "population": [],
            "gdp_per_capita": [],
            "gdp_growth": [],
            "opportunities": [],
        }

        for state in member_states:
            comparison["countries"].append(state.country_name)
            comparison["gdp"].append(float(state.gdp))
            comparison["population"].append(state.population)
            comparison["gdp_per_capita"].append(
                float(state.gdp_per_capita) if state.gdp_per_capita else 0
            )
            comparison["gdp_growth"].append(
                float(state.gdp_growth_rate) if state.gdp_growth_rate else 0
            )

            # Get opportunities count
            try:
                comparison["opportunities"].append(state.get_opportunities_count())
            except Exception:
                comparison["opportunities"].append(0)

        return comparison

    @staticmethod
    def get_latest_fdi_inflow(member_state: MemberStateIPA):
        """
        Get the most recent FDI inflow data point.

        Args:
            member_state: MemberStateIPA instance

        Returns:
            FDIDataPoint or None
        """
        return (
            FDIDataPoint.objects.filter(
                member_state=member_state, data_type="fdi_inflow", validation_status="published"
            )
            .order_by("-year")
            .first()
        )


class ComparisonService:
    """
    Service for country comparison functionality.
    Handles side-by-side analysis of member states.
    """

    @staticmethod
    def compare_countries(country_slugs: List[str]) -> Dict:
        """
        Generate comprehensive comparison data for selected countries.

        Args:
            country_slugs: List of country slugs to compare (2-4 countries)

        Returns:
            Dictionary with comparison data
        """
        if not country_slugs or len(country_slugs) < 2:
            return {"error": "Please select at least 2 countries to compare"}

        if len(country_slugs) > 4:
            return {"error": "Maximum 4 countries can be compared at once"}

        # Get member states
        member_states = MemberStateIPA.objects.filter(
            slug__in=country_slugs, is_active=True
        ).prefetch_related("sectors__sector", "incentives")

        if member_states.count() != len(country_slugs):
            return {"error": "One or more countries not found"}

        comparison = {
            "countries": list(member_states),
            "economic_indicators": ComparisonService._compare_economic_indicators(member_states),
            "sectors": ComparisonService._compare_sectors(member_states),
            "incentives": ComparisonService._compare_incentives(member_states),
            "business_climate": ComparisonService._compare_business_climate(member_states),
            "contact_info": ComparisonService._compare_contact_info(member_states),
        }

        return comparison

    @staticmethod
    def _compare_economic_indicators(member_states) -> Dict:
        """Compare economic indicators"""
        return {
            "gdp": [round(float(state.gdp) / 1_000_000_000, 2) if state.gdp else 0 for state in member_states],
            "gdp_display": [state.formatted_gdp for state in member_states],
            "population": [state.population or 0 for state in member_states],
            "population_millions": [round(state.population / 1_000_000, 1) if state.population else 0 for state in member_states],
            "population_display": [state.population_display or "—" for state in member_states],
            "gdp_per_capita": [
                float(state.gdp_per_capita) if state.gdp_per_capita else 0
                for state in member_states
            ],
            "gdp_growth": [
                float(state.gdp_growth_rate) if state.gdp_growth_rate else 0
                for state in member_states
            ],
            "capital_cities": [state.capital_city or "—" for state in member_states],
            "currencies": [
                f"{state.currency_name} ({state.currency_code})" if state.currency_name else "—"
                for state in member_states
            ],
        }

    @staticmethod
    def _compare_sectors(member_states) -> Dict:
        """Compare priority sectors"""
        sectors_by_country = {}

        for state in member_states:
            priority_sectors = state.sectors.filter(is_priority=True)
            sectors_by_country[state.country_name] = [
                {"name": sector.sector.name, "description": sector.description}
                for sector in priority_sectors
            ]

        return sectors_by_country

    @staticmethod
    def _compare_incentives(member_states) -> Dict:
        """Compare investment incentives"""
        incentives_by_country = {}

        for state in member_states:
            incentives = state.incentives.filter(is_active=True)
            incentives_by_country[state.country_name] = {
                "count": incentives.count(),
                "types": list(incentives.values_list("incentive_type", flat=True).distinct()),
                "details": [
                    {
                        "title": inc.title,
                        "type": inc.get_incentive_type_display(),
                        "duration": inc.duration,
                        "benefit": inc.benefit_amount,
                    }
                    for inc in incentives[:5]  # Top 5
                ],
            }

        return incentives_by_country

    @staticmethod
    def _compare_business_climate(member_states) -> Dict:
        """Compare business climate indicators"""
        return {
            "ease_of_doing_business": [
                state.ease_of_doing_business_rank if state.ease_of_doing_business_rank else None
                for state in member_states
            ],
            "competitiveness_score": [
                float(state.competitiveness_score) if state.competitiveness_score else 0
                for state in member_states
            ],
        }

    @staticmethod
    def _compare_contact_info(member_states) -> Dict:
        """Compare contact information"""
        return {
            state.country_name: {
                "ipa_name": state.ipa_full_name,
                "ipa_acronym": state.ipa_acronym,
                "email": state.contact_email,
                "phone": state.contact_phone,
                "website": state.ipa_website,
            }
            for state in member_states
        }


class CacheService:
    """
    Service for managing cache operations.
    Improves performance for frequently accessed data.
    """

    CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
    SHORT_CACHE_TIMEOUT = 60 * 60  # 1 hour

    @staticmethod
    def get_or_set_member_state(slug: str):
        """Get member state from cache or database"""
        cache_key = f"member_state_{slug}"
        member_state = cache.get(cache_key)

        if not member_state:
            member_state = MemberStateService.get_member_state_by_slug(slug)
            if member_state:
                cache.set(cache_key, member_state, CacheService.CACHE_TIMEOUT)

        return member_state

    @staticmethod
    def get_or_set_active_states():
        """Get all active states from cache or database"""
        cache_key = "all_active_member_states"
        member_states = cache.get(cache_key)

        if not member_states:
            member_states = list(MemberStateService.get_active_member_states())
            cache.set(cache_key, member_states, CacheService.CACHE_TIMEOUT)

        return member_states

    @staticmethod
    def get_or_set_statistics():
        """Get statistics from cache or database"""
        cache_key = "member_states_statistics"
        stats = cache.get(cache_key)

        if not stats:
            stats = MemberStateService.get_member_state_statistics()
            cache.set(cache_key, stats, CacheService.CACHE_TIMEOUT)

        return stats

    @staticmethod
    def invalidate_member_state_cache(slug: str):
        """Invalidate cache for a specific member state"""
        cache_key = f"member_state_{slug}"
        cache.delete(cache_key)
        cache.delete("all_active_member_states")
        cache.delete("member_states_statistics")

    @staticmethod
    def invalidate_all_member_states_cache():
        """Invalidate all member states cache"""
        # Get all member states and invalidate their cache
        for state in MemberStateIPA.objects.all():
            cache_key = f"member_state_{state.slug}"
            cache.delete(cache_key)

        # Delete aggregate caches
        cache.delete("all_active_member_states")
        cache.delete("member_states_statistics")

    @staticmethod
    def warm_cache():
        """
        Warm up the cache with frequently accessed data.
        Should be called after data updates or periodically.
        """
        # Cache all active member states
        CacheService.get_or_set_active_states()

        # Cache statistics
        CacheService.get_or_set_statistics()

        # Cache individual states
        for state in MemberStateIPA.objects.filter(is_active=True):
            CacheService.get_or_set_member_state(state.slug)
