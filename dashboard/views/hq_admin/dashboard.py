"""
HQ Admin Dashboard Views
apps/dashboard/views/hq_admin/dashboard.py

Main dashboard view for IPAWAS Headquarters administrators.
Shows system-wide statistics and recent activities.
"""

from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import IPAUser, User
from dashboard.mixins import IPAWASAdminRequiredMixin
from dashboard.models import IPADashboardActivity
from invitations.models import Invitation
from members.models import InvestorInquiry, MemberStateIPA
from opportunities.models import InvestmentOpportunity


class HQDashboardView(IPAWASAdminRequiredMixin, TemplateView):
    """
    HQ Admin dashboard overview.

    Shows:
    - Total member states statistics
    - System-wide metrics
    - Recent activities across all countries
    - Pending invitations
    - System health indicators
    """

    template_name = "dashboard/hq_admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Time ranges
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)

        # Member States Statistics
        member_states = MemberStateIPA.objects.filter(is_active=True)
        context["total_member_states"] = MemberStateIPA.objects.count()
        context["active_member_states"] = member_states.count()

        # System-wide User Statistics
        all_users = User.objects.filter(user_type="ipa_staff", is_active=True)
        context["total_users"] = all_users.count()
        context["new_users_30_days"] = all_users.filter(date_joined__gte=last_30_days).count()
        context["active_users_7_days"] = all_users.filter(last_login__gte=last_7_days).count()

        # Opportunities Statistics
        all_opportunities = InvestmentOpportunity.objects.all()
        context["total_opportunities"] = all_opportunities.count()
        context["published_opportunities"] = all_opportunities.filter(status="active").count()
        context["draft_opportunities"] = all_opportunities.filter(status="draft").count()
        context["opportunities_30_days"] = all_opportunities.filter(
            created_at__gte=last_30_days
        ).count()

        # Calculate trend
        previous_30_days = now - timedelta(days=60)
        previous_count = all_opportunities.filter(
            created_at__gte=previous_30_days, created_at__lt=last_30_days
        ).count()
        if previous_count > 0:
            context["opportunities_trend"] = round(
                ((context["opportunities_30_days"] - previous_count) / previous_count) * 100, 1
            )
        else:
            context["opportunities_trend"] = 100 if context["opportunities_30_days"] > 0 else 0

        # Inquiries Statistics
        all_inquiries = InvestorInquiry.objects.all()
        context["total_inquiries"] = all_inquiries.count()
        context["pending_inquiries"] = all_inquiries.filter(status="new").count()
        context["inquiries_30_days"] = all_inquiries.filter(created_at__gte=last_30_days).count()

        # Invitations Statistics
        pending_invitations = Invitation.objects.filter(status="pending")
        context["pending_invitations"] = pending_invitations.count()
        context["total_invitations"] = Invitation.objects.count()

        # Recent Activities (system-wide)
        context["recent_activities"] = IPADashboardActivity.objects.select_related(
            "user", "member_state"
        ).order_by("-timestamp")[:3]

        # Member States Performance (Top 5 by opportunities)
        context["top_member_states"] = member_states.annotate(
            opportunity_count=Count("opportunities"),
            inquiry_count=Count("inquiries"),
            published_count=Count("opportunities", filter=Q(opportunities__status="active")),
            team_size=Count("ipa_users"),
        ).order_by("-opportunity_count")[:5]

        # Pending Invitations (Recent 5)
        context["recent_invitations"] = pending_invitations.select_related(
            "member_state", "invited_by"
        ).order_by("-created_at")[:5]

        # System Health Indicators
        context["health_indicators"] = {
            "member_states_with_opportunities": member_states.filter(opportunities__isnull=False)
            .distinct()
            .count(),
            "member_states_published": member_states.filter(is_active=True).count(),
            "avg_opportunities_per_state": round(
                all_opportunities.values("primary_country")
                .annotate(count=Count("id"))
                .aggregate(avg=Avg("count"))["avg"]
                or 0,
                1,
            ),
        }

        # Quick Actions
        context["quick_actions"] = [
            {
                "title": "View All Member States",
                "url": "dashboard:hq:member_states",
                "icon": "globe",
                "color": "primary",
            },
            {
                "title": "Manage Users",
                "url": "dashboard:hq:users",
                "icon": "users",
                "color": "success",
            },
            {
                "title": "View Reports",
                "url": "dashboard:hq:reports",
                "icon": "chart-bar",
                "color": "info",
            },
            {
                "title": "System Logs",
                "url": "dashboard:hq:logs",
                "icon": "list",
                "color": "warning",
            },
            {
                "title": "Platform Analytics",
                "url": "dashboard:hq:analytics",
                "icon": "analytics",
                "color": "primary",
            },
            {
                "title": "System Settings",
                "url": "dashboard:hq:config",
                "icon": "cog",
                "color": "secondary",
            },
        ]

        return context
