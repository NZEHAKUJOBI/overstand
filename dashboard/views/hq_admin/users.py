"""
HQ Admin Users Management Views
apps/dashboard/views/hq_admin/users.py

System-wide user management for HQ administrators.
"""

from django.contrib import messages
from django.db.models import Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView, UpdateView, View

from accounts.forms import IPAUserPermissionsForm, UserEditForm
from accounts.models import IPAUser, User
from dashboard.mixins import IPAWASAdminRequiredMixin
from dashboard.models import IPADashboardActivity
from dashboard.utils.activity_logs_services import ActivityLogService
from members.models import MemberStateIPA


class SystemUsersView(IPAWASAdminRequiredMixin, ListView):
    """
    List all users across all member states.

    Features:
    - Search by name/email
    - Filter by member state, role, status
    - Sort options
    - Bulk actions
    """

    model = User
    template_name = "dashboard/hq_admin/users/list.html"
    context_object_name = "users"
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            User.objects.filter(user_type="ipa_staff")
            .select_related("ipa_profile", "ipa_profile__member_state")
            .annotate(activity_count=Count("dashboard_activities"))
        )

        # Search
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        # Filter by member state
        member_state = self.request.GET.get("member_state")
        if member_state:
            queryset = queryset.filter(ipa_profile__member_state__slug=member_state)

        # Filter by role
        role = self.request.GET.get("role")
        if role:
            queryset = queryset.filter(ipa_profile__role=role)

        # Filter by status
        is_active = self.request.GET.get("is_active")
        if is_active:
            queryset = queryset.filter(is_active=is_active == "true")

        # Sort
        sort = self.request.GET.get("sort", "-date_joined")
        allowed_sorts = [
            "email",
            "-email",
            "date_joined",
            "-date_joined",
            "last_login",
            "-last_login",
            "activity_count",
            "-activity_count",
        ]
        if sort in allowed_sorts:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filter options
        context["member_states"] = MemberStateIPA.objects.filter(is_active=True).order_by(
            "country_name"
        )

        # Current filters
        context["search_query"] = self.request.GET.get("search", "")
        context["member_state_filter"] = self.request.GET.get("member_state", "")
        context["role_filter"] = self.request.GET.get("role", "")
        context["is_active_filter"] = self.request.GET.get("is_active", "")
        context["sort"] = self.request.GET.get("sort", "-date_joined")

        # Summary statistics
        all_users = User.objects.filter(user_type="ipa_staff")
        context["total_users"] = all_users.count()
        context["active_users"] = all_users.filter(is_active=True).count()
        context["inactive_users"] = all_users.filter(is_active=False).count()

        return context


class UserDetailView(IPAWASAdminRequiredMixin, DetailView):
    """
    Detailed view of a specific user.

    Shows:
    - User information
    - IPA profile details
    - Permissions
    - Activity history
    - Login history
    """

    model = User
    template_name = "dashboard/hq_admin/users/detail.html"
    context_object_name = "user_obj"

    def get_queryset(self):
        return User.objects.filter(user_type="ipa_staff").select_related(
            "ipa_profile", "ipa_profile__member_state"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        # IPA Profile details
        try:
            context["ipa_profile"] = user.ipa_profile
        except IPAUser.DoesNotExist:
            context["ipa_profile"] = None

        # Recent Activities
        context["recent_activities"] = (
            IPADashboardActivity.objects.filter(user=user)
            .select_related("member_state")
            .order_by("-timestamp")[:20]
        )

        # Activity Statistics
        now = timezone.now()
        from datetime import timedelta

        last_30_days = now - timedelta(days=30)

        context["activity_stats"] = {
            "total_activities": IPADashboardActivity.objects.filter(user=user).count(),
            "activities_30_days": IPADashboardActivity.objects.filter(
                user=user, timestamp__gte=last_30_days
            ).count(),
            "last_login": user.last_login,
            "login_count": getattr(user, "login_count", 0),
        }

        # Log view
        ActivityLogService.log_activity(
            user=self.request.user,
            action_type="viewed_user_detail",
            description=f"Viewed user details for {user.get_full_name()} ({user.email})",
        )

        return context


class UserEditView(IPAWASAdminRequiredMixin, UpdateView):
    """
    Edit user information.
    """

    model = User
    form_class = UserEditForm
    template_name = "dashboard/hq_admin/users/edit.html"

    def get_queryset(self):
        return User.objects.filter(user_type="ipa_staff")

    def get_success_url(self):
        return reverse_lazy("dashboard:hq:user_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(self.request, f"User {self.object.get_full_name()} updated successfully")

        # Log activity
        ActivityLogService.log_activity(
            user=self.request.user,
            action_type="updated_user",
            description=f"Updated user {self.object.get_full_name()} ({self.object.email})",
            member_state=(
                self.object.ipa_profile.member_state
                if hasattr(self.object, "ipa_profile")
                else None
            ),
        )

        return response


class UserDeactivateView(IPAWASAdminRequiredMixin, View):
    """
    Deactivate or reactivate a user.
    """

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, user_type="ipa_staff")

        # Toggle active status
        user.is_active = not user.is_active
        user.save()

        action = "activated" if user.is_active else "deactivated"

        messages.success(request, f"User {user.get_full_name()} has been {action}")

        # Log activity
        ActivityLogService.log_activity(
            user=request.user,
            action_type=f"{action}_user",
            description=f"{action.capitalize()} user {user.get_full_name()} ({user.email})",
            member_state=user.ipa_profile.member_state if hasattr(user, "ipa_profile") else None,
        )

        return redirect("dashboard:hq:user_detail", pk=pk)


class UserPermissionsView(IPAWASAdminRequiredMixin, UpdateView):
    """
    Manage user permissions.
    """

    model = IPAUser
    form_class = IPAUserPermissionsForm
    template_name = "dashboard/hq_admin/users/permissions.html"

    def get_object(self):
        user = get_object_or_404(User, pk=self.kwargs["pk"], user_type="ipa_staff")
        return user.ipa_profile

    def get_success_url(self):
        return reverse_lazy("dashboard:hq:user_detail", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request, f"Permissions updated for {self.object.user.get_full_name()}"
        )

        # Log activity
        ActivityLogService.log_activity(
            user=self.request.user,
            action_type="updated_permissions",
            description=f"Updated permissions for {self.object.user.get_full_name()}",
            member_state=self.object.member_state,
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_obj"] = self.object.user
        return context
