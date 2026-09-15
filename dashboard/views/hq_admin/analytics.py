"""
HQ Admin Analytics Views
apps/dashboard/views/hq_admin/analytics.py
"""

from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.views.generic import TemplateView

from dashboard.mixins import IPAWASAdminRequiredMixin
from dashboard.models import IPADashboardActivity
from members.models import InvestorInquiry, MemberStateIPA
from opportunities.models import InvestmentOpportunity


class PlatformAnalyticsView(IPAWASAdminRequiredMixin, TemplateView):
    """Platform-wide analytics overview."""

    template_name = "dashboard/hq_admin/analytics/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)

        # --- Member States ---
        member_states = MemberStateIPA.objects.filter(is_active=True)
        context["total_member_states"] = MemberStateIPA.objects.count()
        context["active_member_states"] = member_states.count()

        # States with at least one published opportunity
        context["states_with_content"] = (
            member_states.filter(opportunities__status="active").distinct().count()
        )

        # --- Opportunities ---
        opportunities = InvestmentOpportunity.objects.all()
        context["opportunity_summary"] = {
            "total": opportunities.count(),
            "published": opportunities.filter(status="active").count(),
            "draft": opportunities.filter(status="draft").count(),
            "last_30_days": opportunities.filter(created_at__gte=last_30_days).count(),
        }

        # Top 5 member states by published opportunity count
        context["top_states_by_opportunities"] = list(
            member_states.annotate(
                published_count=Count("opportunities", filter=Q(opportunities__status="active"))
            )
            .order_by("-published_count")[:5]
            .values("country_name", "ipa_acronym", "slug", "published_count")
        )

        # Opportunity breakdown by sector (top 8)
        context["opportunities_by_sector"] = list(
            opportunities.filter(status="active")
            .values("primary_sector__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )

        # --- Inquiries ---
        inquiries = InvestorInquiry.objects.all()
        context["inquiry_summary"] = {
            "total": inquiries.count(),
            "new": inquiries.filter(status="new").count(),
            "in_progress": inquiries.filter(status="in_progress").count(),
            "last_30_days": inquiries.filter(created_at__gte=last_30_days).count(),
        }

        # --- Activity trend (last 90 days, daily) ---
        context["activity_trend"] = list(
            IPADashboardActivity.objects.filter(timestamp__gte=last_90_days)
            .annotate(date=TruncDate("timestamp"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        # --- Monthly opportunity creation (last 6 months) ---
        last_6_months = now - timedelta(days=180)
        context["opportunity_trend"] = list(
            opportunities.filter(created_at__gte=last_6_months)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        return context


class AllOpportunitiesAnalyticsView(IPAWASAdminRequiredMixin, TemplateView):
    """Deep analytics for all investment opportunities."""

    template_name = "dashboard/hq_admin/analytics/opportunities.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)

        opportunities = InvestmentOpportunity.objects.all()

        # --- Status breakdown ---
        context["by_status"] = list(
            opportunities.values("status").annotate(count=Count("id")).order_by("-count")
        )

        # --- By opportunity type ---
        context["by_type"] = list(
            opportunities.values("opportunity_type").annotate(count=Count("id")).order_by("-count")
        )

        # --- By sector (top 10) ---
        context["by_sector"] = list(
            opportunities.values("primary_sector__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # --- By member state ---
        context["by_member_state"] = list(
            opportunities.values("primary_country__country_name", "primary_country__ipa_acronym")
            .annotate(
                total=Count("id"),
                published=Count("id", filter=Q(status="active")),
            )
            .order_by("-total")
        )

        # --- Monthly creation trend (last 12 months) ---
        last_12_months = now - timedelta(days=365)
        context["creation_trend"] = list(
            opportunities.filter(created_at__gte=last_12_months)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        # --- Investment range distribution ---
        # Bucket opportunities into investment size tiers (USD)
        context["investment_tiers"] = {
            "under_1m": opportunities.filter(investment_required_min__lt=1_000_000).count(),
            "1m_to_10m": opportunities.filter(
                investment_required_min__gte=1_000_000,
                investment_required_min__lt=10_000_000,
            ).count(),
            "10m_to_50m": opportunities.filter(
                investment_required_min__gte=10_000_000,
                investment_required_min__lt=50_000_000,
            ).count(),
            "over_50m": opportunities.filter(investment_required_min__gte=50_000_000).count(),
        }

        # --- Summary KPIs ---
        context["summary"] = {
            "total": opportunities.count(),
            "published": opportunities.filter(status="active").count(),
            "draft": opportunities.filter(status="draft").count(),
            "regional": opportunities.filter(is_regional=True).count(),
            "last_30_days": opportunities.filter(created_at__gte=last_30_days).count(),
        }

        return context


class AllInquiriesAnalyticsView(IPAWASAdminRequiredMixin, TemplateView):
    """Deep analytics for all investor inquiries."""

    template_name = "dashboard/hq_admin/analytics/inquiries.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)

        inquiries = InvestorInquiry.objects.all()

        # --- Status breakdown ---
        context["by_status"] = list(
            inquiries.values("status").annotate(count=Count("id")).order_by("-count")
        )

        # --- By member state (top 10) ---
        context["by_member_state"] = list(
            inquiries.values("member_state__country_name", "member_state__ipa_acronym")
            .annotate(
                total=Count("id"),
                pending=Count("id", filter=Q(status="new")),
            )
            .order_by("-total")[:10]
        )

        # --- Monthly inquiry trend (last 12 months) ---
        last_12_months = now - timedelta(days=365)
        context["monthly_trend"] = list(
            inquiries.filter(created_at__gte=last_12_months)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        # --- Daily trend (last 90 days) ---
        context["daily_trend"] = list(
            inquiries.filter(created_at__gte=last_90_days)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        # --- Conversion rate: new → qualified ---
        total = inquiries.count()
        qualified = inquiries.filter(status="qualified").count()
        context["conversion_rate"] = round((qualified / total) * 100, 1) if total else 0

        # --- Summary KPIs ---
        context["summary"] = {
            "total": total,
            "new": inquiries.filter(status="new").count(),
            "in_progress": inquiries.filter(status="in_progress").count(),
            "qualified": qualified,
            "last_30_days": inquiries.filter(created_at__gte=last_30_days).count(),
        }

        return context


class PlatformTrafficView(IPAWASAdminRequiredMixin, TemplateView):
    """
    Platform activity analytics using the IPADashboardActivity audit log as a traffic proxy.
    Shows which actions, users, and member states drive the most platform engagement.
    """

    template_name = "dashboard/hq_admin/analytics/traffic.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)

        activities = IPADashboardActivity.objects.all()
        recent = activities.filter(timestamp__gte=last_30_days)

        # --- Daily activity trend (last 90 days) ---
        context["daily_trend"] = list(
            activities.filter(timestamp__gte=last_90_days)
            .annotate(date=TruncDate("timestamp"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        # --- Activity breakdown by action type (last 30 days, top 10) ---
        context["by_action_type"] = list(
            recent.values("action_type").annotate(count=Count("id")).order_by("-count")[:10]
        )

        # --- Activity breakdown by member state (last 30 days) ---
        context["by_member_state"] = list(
            recent.filter(member_state__isnull=False)
            .values("member_state__country_name", "member_state__ipa_acronym")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # --- Most active users (last 30 days, top 10) ---
        context["most_active_users"] = list(
            recent.filter(user__isnull=False)
            .values("user__first_name", "user__last_name", "user__email")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # --- Summary KPIs ---
        context["summary"] = {
            "total_actions_30_days": recent.count(),
            "unique_users_30_days": recent.filter(user__isnull=False)
            .values("user")
            .distinct()
            .count(),
            "active_member_states_30_days": recent.filter(member_state__isnull=False)
            .values("member_state")
            .distinct()
            .count(),
        }

        return context
