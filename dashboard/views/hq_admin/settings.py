"""
HQ Admin Settings Views
apps/dashboard/views/hq_admin/settings.py
"""

from django.contrib.auth.views import PasswordChangeView as DjangoPasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from dashboard.mixins import IPAWASAdminRequiredMixin


class HQAdminSettingsView(IPAWASAdminRequiredMixin, TemplateView):
    """HQ Admin personal settings."""

    template_name = "dashboard/hq_admin/settings/settings.html"


class HQPasswordChangeView(IPAWASAdminRequiredMixin, DjangoPasswordChangeView):
    """Change password for HQ admin."""

    template_name = "dashboard/hq_admin/settings/password.html"
    success_url = reverse_lazy("dashboard:hq:settings")


class HQ2FASetupView(IPAWASAdminRequiredMixin, TemplateView):
    """Setup two-factor authentication."""

    template_name = "dashboard/hq_admin/settings/2fa.html"


class HQNotificationPreferencesView(IPAWASAdminRequiredMixin, TemplateView):
    """Notification preferences."""

    template_name = "dashboard/hq_admin/settings/notifications.html"
