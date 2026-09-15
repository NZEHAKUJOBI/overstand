"""
HQ Admin System Management Views
apps/dashboard/views/hq_admin/system.py

System configuration and management for HQ administrators.
"""

from datetime import timedelta

from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import FormView, ListView, TemplateView

from accounts.models import User
from dashboard.mixins import IPAWASAdminRequiredMixin
from dashboard.models import IPADashboardActivity
from members.models import MemberStateIPA
from opportunities.models import InvestmentOpportunity


class SystemConfigView(IPAWASAdminRequiredMixin, TemplateView):
    """System configuration overview."""

    template_name = "dashboard/hq_admin/system/config.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # System statistics

        context["system_stats"] = {
            "total_users": User.objects.filter(user_type="ipa_staff").count(),
            "total_member_states": MemberStateIPA.objects.count(),
            "total_opportunities": InvestmentOpportunity.objects.count(),
            "database_size": self._get_database_size(),
        }

        return context

    def _get_database_size(self):
        """Get approximate database size (placeholder)."""
        return "Calculate in production"


class SystemLogsView(IPAWASAdminRequiredMixin, ListView):
    """View system activity logs with pagination."""

    model = IPADashboardActivity
    template_name = "dashboard/hq_admin/system/logs.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        queryset = IPADashboardActivity.objects.select_related("user", "member_state").order_by(
            "-timestamp"
        )

        # Apply filters from GET parameters
        action_type = self.request.GET.get("action_type")
        if action_type:
            queryset = queryset.filter(action_type=action_type)

        user_search = self.request.GET.get("user")
        if user_search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=user_search)
                | Q(user__last_name__icontains=user_search)
                | Q(user__email__icontains=user_search)
            )

        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filter options
        context["available_actions"] = IPADashboardActivity.objects.values_list(
            "action_type", flat=True
        ).distinct()

        return context


class EmailSettingsView(IPAWASAdminRequiredMixin, TemplateView):
    """Email configuration settings."""

    template_name = "dashboard/hq_admin/system/email.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from django.conf import settings

        context["email_settings"] = {
            "backend": settings.EMAIL_BACKEND,
            "host": getattr(settings, "EMAIL_HOST", "Not configured"),
            "from_email": settings.DEFAULT_FROM_EMAIL,
        }

        return context


class SecuritySettingsView(IPAWASAdminRequiredMixin, TemplateView):
    """Security configuration."""

    template_name = "dashboard/hq_admin/system/security.html"


class MaintenanceModeView(IPAWASAdminRequiredMixin, TemplateView):
    """Maintenance mode control."""

    template_name = "dashboard/hq_admin/system/maintenance.html"
