"""
HQ Admin Member States Views

Views for managing all member states from HQ perspective.
"""

from datetime import timedelta

from django.contrib import messages
from django.db.models import Count, Prefetch, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, TemplateView

from accounts.models import IPAUser
from core.email.services import get_invitation_email_service
from dashboard.mixins import IPAWASAdminRequiredMixin
from dashboard.models import IPADashboardActivity
from dashboard.utils.activity_logs_services import ActivityLogService
from invitations.forms import InvitationForm
from invitations.models import Invitation
from members.models import MemberStateIPA


class MemberStateListView(IPAWASAdminRequiredMixin, ListView):
    """
    List all member states with key statistics.

    Features:
    - Search by name/acronym
    - Filter by status
    - Sort by various metrics
    - Pagination
    """

    model = MemberStateIPA
    template_name = "dashboard/hq_admin/member_states/list.html"
    context_object_name = "member_states"
    paginate_by = 25

    def get_queryset(self):
        queryset = MemberStateIPA.objects.annotate(
            opportunity_count=Count("opportunities"),
            published_opportunity_count=Count(
                "opportunities", filter=Q(opportunities__status="active")
            ),
            inquiry_count=Count("inquiries"),
            team_member_count=Count("ipa_users", filter=Q(ipa_users__is_active=True)),
        ).filter(is_active=True)

        # Search
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(acronym__icontains=search)
                | Q(country__name__icontains=search)
            )

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            pass
            # queryset = queryset.filter(profile_status=status)

        # Filter by activity
        is_active = self.request.GET.get("is_active")
        if is_active:
            queryset = queryset.filter(is_active=is_active == "true")

        # Sort
        sort = self.request.GET.get("sort", "-created_at")
        allowed_sorts = [
            "name",
            "-name",
            "created_at",
            "-created_at",
            "opportunity_count",
            "-opportunity_count",
            "inquiry_count",
            "-inquiry_count",
        ]
        if sort in allowed_sorts:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["status_filter"] = self.request.GET.get("status", "")
        context["sort"] = self.request.GET.get("sort", "-created_at")

        # Summary statistics
        all_states = MemberStateIPA.objects.all()
        context["total_count"] = all_states.count()
        context["active_count"] = all_states.filter(is_active=True).count()
        # context["published_count"] = all_states.filter(profile_status="active").count()

        return context


class MemberStateDetailView(IPAWASAdminRequiredMixin, DetailView):
    """
    Detailed view of a single member state.

    Shows:
    - Profile information
    - Team members
    - Opportunities statistics
    - Recent activities
    - Performance metrics
    """

    model = MemberStateIPA
    template_name = "dashboard/hq_admin/member_states/detail.html"
    context_object_name = "member_state"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.object

        # Time ranges
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)

        # Team Members
        context["team_members"] = (
            IPAUser.objects.filter(member_state=member_state, is_active=True)
            .select_related("user")
            .order_by("-created_at")
        )

        context["admin_count"] = context["team_members"].filter(role="ipa_director").count()
        context["editor_count"] = context["team_members"].filter(role__in=["ipa_manager", "ipa_officer"]).count()

        # Opportunities
        opportunities = member_state.opportunities.all()
        context["total_opportunities"] = opportunities.count()
        context["published_opportunities"] = opportunities.filter(status="active").count()
        context["draft_opportunities"] = opportunities.filter(status="draft").count()
        context["recent_opportunities"] = opportunities.select_related(
            "primary_sector", "created_by"
        ).order_by("-created_at")[:5]

        # Inquiries
        inquiries = member_state.inquiries.all()
        context["total_inquiries"] = inquiries.count()
        context["new_inquiries"] = inquiries.filter(status="new").count()
        context["in_progress_inquiries"] = inquiries.filter(status="in_progress").count()
        context["recent_inquiries"] = inquiries.order_by("-created_at")[:5]

        # Recent Activities
        context["recent_activities"] = (
            IPADashboardActivity.objects.filter(member_state=member_state)
            .select_related("user")
            .order_by("-timestamp")[:10]
        )

        # Pending Invitations
        context["pending_invitations"] = (
            Invitation.objects.filter(member_state=member_state, status="pending")
            .select_related("invited_by")
            .order_by("-created_at")[:5]
        )

        # Performance Metrics
        context["metrics"] = {
            "profile_completion": member_state.get_profile_completion(),
            "activity_score": self._calculate_activity_score(member_state, last_30_days),
            # "avg_response_time": self._calculate_avg_response_time(member_state),
        }

        return context

    def _calculate_activity_score(self, member_state, since):
        """Calculate activity score based on recent actions."""
        activities = IPADashboardActivity.objects.filter(
            member_state=member_state, timestamp__gte=since
        ).count()

        # Score: 0-100 based on activity count
        if activities == 0:
            return 0
        elif activities < 10:
            return 25
        elif activities < 25:
            return 50
        elif activities < 50:
            return 75
        else:
            return 100

    # def _calculate_avg_response_time(self, member_state):
    #     """Calculate average inquiry response time in hours."""
    #     # TODO
    #     responded_inquiries = member_state.inquiries.filter(first_response_at__isnull=False)

    #     if not responded_inquiries.exists():
    #         return None

    #     total_time = sum(
    #         [
    #             (inquiry.first_response_at - inquiry.created_at).total_seconds()
    #             for inquiry in responded_inquiries
    #         ]
    #     )

    #     avg_seconds = total_time / responded_inquiries.count()
    #     return round(avg_seconds / 3600, 1)  # Convert to hours


class MemberStateInviteView(IPAWASAdminRequiredMixin, FormView):
    """
    Invite users to a specific member state.
    HQ admin can invite users to any member state.
    """

    template_name = "dashboard/hq_admin/member_states/invite.html"
    form_class = InvitationForm

    def dispatch(self, request, *args, **kwargs):
        self.member_state = get_object_or_404(MemberStateIPA, slug=self.kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["member_state"] = self.member_state
        return kwargs

    def form_valid(self, form):

        try:
            invitation = Invitation.objects.create_invitation(
                member_state=self.member_state,
                email=form.cleaned_data["email"],
                role=form.cleaned_data["role"],
                invited_by=self.request.user,
            )

            # Send invitation email
            email_service = get_invitation_email_service()
            email_sent = email_service.send_invitation_email(invitation)

            if email_sent:
                messages.success(
                    self.request,
                    f"Invitation sent successfully to {invitation.email} for {self.member_state.country_name}",
                )
            else:
                messages.warning(
                    self.request,
                    f"Invitation created for {invitation.email}, but email delivery failed. "
                    f"You can resend the invitation from the invitations list.",
                )

            # Log activity
            ActivityLogService.log_activity(
                user=self.request.user,
                action_type="user_invite",
                description=f"Invited {invitation.email} to {self.member_state.country_name} as {invitation.role}",
                member_state=self.member_state,
            )

            return redirect("dashboard:hq:member_state_detail", slug=self.member_state.slug)

        except Exception as e:
            messages.error(self.request, f"Error sending invitation: {str(e)}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.member_state
        return context


class MemberStateUsersView(IPAWASAdminRequiredMixin, ListView):
    """
    List all users for a specific member state.
    """

    model = IPAUser
    template_name = "dashboard/hq_admin/member_states/users.html"
    context_object_name = "users"
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        self.member_state = get_object_or_404(MemberStateIPA, slug=self.kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            IPAUser.objects.filter(member_state=self.member_state)
            .select_related("user")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.member_state

        # Statistics
        all_users = self.get_queryset()
        context["total_users"] = all_users.count()
        context["active_users"] = all_users.filter(is_active=True).count()
        context["admin_users"] = all_users.filter(role="ipa_director").count()

        return context


class MemberStateActivitiesView(IPAWASAdminRequiredMixin, ListView):
    """
    View all activities for a specific member state.
    """

    model = IPADashboardActivity
    template_name = "dashboard/hq_admin/member_states/activities.html"
    context_object_name = "activities"
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        self.member_state = get_object_or_404(MemberStateIPA, slug=self.kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (
            IPADashboardActivity.objects.filter(member_state=self.member_state)
            .select_related("user")
            .order_by("-timestamp")
        )

        # Filter by action
        action = self.request.GET.get("action")
        if action:
            queryset = queryset.filter(action_type=action)

        # Filter by date range
        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.member_state

        # Get unique actions for filter
        context["available_actions"] = (
            IPADashboardActivity.objects.filter(member_state=self.member_state)
            .values_list("action_type", flat=True)
            .distinct()
        )

        return context


class MemberStateAnalyticsView(IPAWASAdminRequiredMixin, TemplateView):
    """
    Analytics dashboard for a specific member state.
    """

    template_name = "dashboard/hq_admin/member_states/analytics.html"

    def dispatch(self, request, *args, **kwargs):
        self.member_state = get_object_or_404(MemberStateIPA, slug=self.kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.member_state

        # Time ranges
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)

        # Opportunities Analytics
        opportunities = self.member_state.opportunities.all()
        context["opportunities_data"] = {
            "total": opportunities.count(),
            "published": opportunities.filter(status="active").count(),
            "last_30_days": opportunities.filter(created_at__gte=last_30_days).count(),
            "by_sector": list(
                opportunities.values("primary_sector__name")
                .annotate(count=Count("id"))
                .order_by("-count")[:5]
            ),
        }

        # Inquiries Analytics
        inquiries = self.member_state.inquiries.all()
        context["inquiries_data"] = {
            "total": inquiries.count(),
            "new": inquiries.filter(status="new").count(),
            "last_30_days": inquiries.filter(created_at__gte=last_30_days).count(),
            "conversion_rate": self._calculate_conversion_rate(inquiries),
        }

        # Activity Trend (last 90 days)
        context["activity_trend"] = self._get_activity_trend(last_90_days)

        return context

    def _calculate_conversion_rate(self, inquiries):
        """Calculate inquiry to opportunity conversion rate."""
        total = inquiries.count()
        if total == 0:
            return 0

        converted = inquiries.filter(status="qualified").count()
        return round((converted / total) * 100, 1)

    def _get_activity_trend(self, since):
        """Get daily activity counts for trend chart."""

        activities = (
            IPADashboardActivity.objects.filter(
                member_state=self.member_state, timestamp__gte=since
            )
            .annotate(date=TruncDate("timestamp"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        return list(activities)
