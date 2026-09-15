"""
Member State Dashboard View - Improved
apps/dashboard/views/member_state/dashboard.py

Now works with slug-based URLs: /dashboard/<member-state-slug>/
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from dashboard.mixins import IPAStaffRequiredMixin, MemberStateAccessMixin


class DashboardOverviewView(IPAStaffRequiredMixin, MemberStateAccessMixin, TemplateView):
    """
    Country dashboard overview for IPA staff.

    URL: /dashboard/<member-state-slug>/
    Example: /dashboard/nigeria/ or /dashboard/ghana/
    """

    template_name = "dashboard/members/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Member state is already validated and set by MemberStateAccessMixin
        member_state = self.request.member_state
        context["member_state"] = member_state

        # Time ranges
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)

        # Opportunities Statistics
        opportunities = member_state.opportunities.all()
        total_opportunities = opportunities.count()
        published_opportunities = opportunities.filter(status="active").count()
        draft_opportunities = opportunities.filter(status="draft").count()
        opportunities_30_days = opportunities.filter(created_at__gte=last_30_days).count()

        # Calculate trend
        previous_30_days = now - timedelta(days=60)
        previous_count = opportunities.filter(
            created_at__gte=previous_30_days, created_at__lt=last_30_days
        ).count()
        if previous_count > 0:
            trend = round(((opportunities_30_days - previous_count) / previous_count) * 100, 1)
        else:
            trend = 100 if opportunities_30_days > 0 else 0

        context["opportunity_stats"] = {
            "total": total_opportunities,
            "published": published_opportunities,
            "draft": draft_opportunities,
            "last_30_days": opportunities_30_days,
            "trend": trend,
        }

        # Inquiries Statistics
        inquiries = member_state.inquiries.all()
        context["inquiry_stats"] = {
            "total": inquiries.count(),
            "new": inquiries.filter(status="new").count(),
            "in_progress": inquiries.filter(status="in_progress").count(),
            "last_30_days": inquiries.filter(created_at__gte=last_30_days).count(),
        }

        # Team Statistics
        team_members = member_state.ipa_users.filter(is_active=True)
        context["team_stats"] = {
            "total": team_members.count(),
            "active_7_days": team_members.filter(user__last_login__gte=last_7_days).count(),
        }

        # Profile Completion — single canonical source on the model
        profile_completion = member_state.get_profile_completion()
        context["profile_completion"] = profile_completion

        # Recent Activities (last 10)
        from dashboard.models import IPADashboardActivity

        context["recent_activities"] = (
            IPADashboardActivity.objects.filter(member_state=member_state)
            .select_related("user")
            .order_by("-timestamp")[:3]
        )

        # Latest Inquiries (last 5)
        context["latest_inquiries"] = inquiries.order_by("-created_at")[:5]

        # Pending Tasks — receives already-computed completion to avoid a second calculation
        context["pending_tasks"] = self._get_pending_tasks(member_state, profile_completion)

        # Quick Actions
        context["quick_actions"] = self._get_quick_actions(member_state)

        return context

    def _get_pending_tasks(self, member_state, completion=None):
        """Get pending tasks for the dashboard.

        Args:
            member_state: The current MemberStateIPA instance.
            completion: Pre-computed profile completion dict (avoids a redundant DB query).
                        If not provided, it will be calculated fresh.
        """
        tasks = []

        slug = member_state.slug

        # Unanswered inquiries
        new_inquiries_count = member_state.inquiries.filter(status="new").count()
        if new_inquiries_count > 0:
            tasks.append(
                {
                    "title": f'Review {new_inquiries_count} new inquir{"y" if new_inquiries_count == 1 else "ies"}',
                    "href": reverse("dashboard:country:inquiries:list", kwargs={"member_state_slug": slug}),
                    "priority": "high",
                }
            )

        # Draft opportunities
        draft_count = member_state.opportunities.filter(status="draft").count()
        if draft_count > 0:
            tasks.append(
                {
                    "title": f'Publish {draft_count} draft opportunit{"y" if draft_count == 1 else "ies"}',
                    "href": reverse("dashboard:country:opportunities", kwargs={"member_state_slug": slug}),
                    "priority": "medium",
                }
            )

        # Profile completion — use the pre-computed value if available
        if completion is None:
            completion = member_state.get_profile_completion()
        if completion["percentage"] < 80:
            tasks.append(
                {
                    "title": f'Complete profile ({completion["percentage"]}% done)',
                    "href": reverse("dashboard:country:profile", kwargs={"member_state_slug": slug}),
                    "priority": "medium",
                }
            )

        return tasks

    def _get_quick_actions(self, member_state):
        """Get quick action links based on permissions."""
        user = self.request.user
        ipa_profile = user.ipa_profile
        actions = []
        slug = member_state.slug

        actions.append(
            {
                "title": "Update Profile",
                "href": reverse("dashboard:country:profile", kwargs={"member_state_slug": slug}),
                "icon": "building",
                "color": "primary",
            }
        )

        if ipa_profile.can_create_opportunities:
            actions.append(
                {
                    "title": "Create Opportunity",
                    "href": reverse("dashboard:country:opportunities_create", kwargs={"member_state_slug": slug}),
                    "icon": "plus-circle",
                    "color": "success",
                }
            )

        if ipa_profile.can_edit_profile:
            actions.append(
                {
                    "title": "Add Sector",
                    "href": reverse("dashboard:country:sectors_add", kwargs={"member_state_slug": slug}),
                    "icon": "industry",
                    "color": "info",
                }
            )

        return actions
