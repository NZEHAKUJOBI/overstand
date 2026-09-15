"""
HQ Admin Reports Views
apps/dashboard/views/hq_admin/reports.py

Platform reports and analytics for HQ administrators.
"""

import csv
import json
from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from accounts.models import User
from dashboard.mixins import IPAWASAdminRequiredMixin
from dashboard.models import IPADashboardActivity
from members.models import InvestorInquiry, MemberStateIPA
from opportunities.models import InvestmentOpportunity


class ReportsOverviewView(IPAWASAdminRequiredMixin, TemplateView):
    """Reports dashboard overview."""

    template_name = "dashboard/hq_admin/reports/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["available_reports"] = [
            {
                "title": "Platform Statistics",
                "description": "Overall platform performance metrics",
                "url": "dashboard:hq:platform_stats",
                "icon": "chart-line",
            },
            {
                "title": "Member State Comparison",
                "description": "Compare performance across member states",
                "url": "dashboard:hq:comparison",
                "icon": "balance-scale",
            },
            {
                "title": "Activity Summary",
                "description": "System-wide activity report",
                "url": "dashboard:hq:activity_summary",
                "icon": "tasks",
            },
        ]

        return context


class PlatformStatsView(IPAWASAdminRequiredMixin, TemplateView):
    """Platform-wide statistics report."""

    template_name = "dashboard/hq_admin/reports/platform_stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)

        # Member States Stats
        member_states = MemberStateIPA.objects.all()
        context["member_state_stats"] = {
            "total": member_states.count(),
            "active": member_states.filter(is_active=True).count(),
            # "published": member_states.filter(profile_status="active").count(),
        }

        # Opportunities Stats
        opportunities = InvestmentOpportunity.objects.all()
        context["opportunity_stats"] = {
            "total": opportunities.count(),
            "published": opportunities.filter(status="active").count(),
            "draft": opportunities.filter(status="draft").count(),
            "last_30_days": opportunities.filter(created_at__gte=last_30_days).count(),
        }

        # Inquiries Stats
        inquiries = InvestorInquiry.objects.all()
        context["inquiry_stats"] = {
            "total": inquiries.count(),
            "new": inquiries.filter(status="new").count(),
            "in_progress": inquiries.filter(status="in_progress").count(),
            "last_30_days": inquiries.filter(created_at__gte=last_30_days).count(),
        }

        # Users Stats
        users = User.objects.filter(user_type="ipa_staff")
        context["user_stats"] = {
            "total": users.count(),
            "active": users.filter(is_active=True).count(),
            "new_30_days": users.filter(date_joined__gte=last_30_days).count(),
        }

        return context


class MemberStateComparisonView(IPAWASAdminRequiredMixin, TemplateView):
    """Compare performance across member states."""

    template_name = "dashboard/hq_admin/reports/comparison.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get member states with metrics
        member_states = (
            MemberStateIPA.objects.annotate(
                opportunity_count=Count("opportunities"),
                published_opp_count=Count(
                    "opportunities", filter=Q(opportunities__status="active")
                ),
                inquiry_count=Count("inquiries"),
                team_size=Count("ipa_users", filter=Q(ipa_users__is_active=True)),
            )
            .filter(is_active=True)
            .order_by("-opportunity_count")
        )

        context["member_states"] = member_states

        return context


class ActivitySummaryView(IPAWASAdminRequiredMixin, TemplateView):
    """System-wide activity summary."""

    template_name = "dashboard/hq_admin/reports/activity_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        # Activity by action type
        context["activities_by_type"] = (
            IPADashboardActivity.objects.filter(timestamp__gte=last_30_days)
            .values("action_type")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Daily activity trend
        context["daily_activity"] = list(
            IPADashboardActivity.objects.filter(timestamp__gte=last_30_days)
            .annotate(date=TruncDate("timestamp"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        return context


class ReportsExportView(IPAWASAdminRequiredMixin, View):
    """Export reports to CSV."""

    def get(self, request):
        report_type = request.GET.get("type", "platform_stats")

        if report_type == "member_states":
            return self._export_member_states()
        elif report_type == "opportunities":
            return self._export_opportunities()
        else:
            return self._export_platform_stats()

    def _export_member_states(self):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="member_states.csv"'

        writer = csv.writer(response)
        writer.writerow(["Name", "Acronym", "Opportunities", "Inquiries", "Team Size", "Status"])

        member_states = MemberStateIPA.objects.annotate(
            opp_count=Count("opportunities"),
            inq_count=Count("inquiries"),
            team_count=Count("ipa_users"),
        )

        for ms in member_states:
            writer.writerow(
                [
                    ms.name,
                    ms.acronym,
                    ms.opp_count,
                    ms.inq_count,
                    ms.team_count,
                    ms.profile_status,
                ]
            )

        return response

    def _export_opportunities(self):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="opportunities.csv"'

        writer = csv.writer(response)
        writer.writerow(["Title", "Member State", "Sector", "Investment", "Status", "Created"])

        opportunities = InvestmentOpportunity.objects.select_related(
            "primary_country", "primary_sector"
        )

        for opp in opportunities:
            investment_max = opp.investment_required_max or ""
            investment_range = (
                f"${opp.investment_required_min}-${investment_max}M"
                if investment_max
                else f"${opp.investment_required_min}M"
            )
            writer.writerow(
                [
                    opp.title,
                    opp.primary_country.country_name,
                    opp.primary_sector.name if opp.primary_sector else "",
                    investment_range,
                    opp.status,
                    opp.created_at.strftime("%Y-%m-%d"),
                ]
            )

        return response

    def _export_platform_stats(self):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="platform_stats.csv"'

        writer = csv.writer(response)
        writer.writerow(["Metric", "Value"])

        writer.writerow(["Total Member States", MemberStateIPA.objects.count()])
        writer.writerow(["Total Opportunities", InvestmentOpportunity.objects.count()])
        writer.writerow(["Total Inquiries", InvestorInquiry.objects.count()])
        writer.writerow(["Total Users", User.objects.filter(user_type="ipa_staff").count()])

        return response
