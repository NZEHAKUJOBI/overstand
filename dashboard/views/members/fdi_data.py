"""FDI Data Points CRUD Views"""

from django.contrib import messages
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dashboard.forms import FDIDataPointForm
from dashboard.mixins import CanEditProfileMixin, IPAStaffRequiredMixin
from members.models import FDIDataPoint


class FDIDataListView(IPAStaffRequiredMixin, ListView):
    model = FDIDataPoint
    template_name = "dashboard/members/fdi_data/list.html"
    context_object_name = "data_points"

    def get_queryset(self):
        return FDIDataPoint.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        ).order_by("data_type", "-year")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context


class FDIDataCreateView(CanEditProfileMixin, CreateView):
    model = FDIDataPoint
    form_class = FDIDataPointForm
    template_name = "dashboard/members/fdi_data/form.html"

    def get_success_url(self):
        return reverse(
            "dashboard:country:fdi_data",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        form.instance.member_state = self.request.user.ipa_profile.member_state
        messages.success(self.request, "Data point added successfully.")
        return super().form_valid(form)


class FDIDataEditView(CanEditProfileMixin, UpdateView):
    model = FDIDataPoint
    form_class = FDIDataPointForm
    template_name = "dashboard/members/fdi_data/form.html"

    def get_queryset(self):
        return FDIDataPoint.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        )

    def get_success_url(self):
        return reverse(
            "dashboard:country:fdi_data",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        messages.success(self.request, "Data point updated successfully.")
        return super().form_valid(form)


class FDIDataDeleteView(CanEditProfileMixin, DeleteView):
    model = FDIDataPoint
    template_name = "dashboard/members/fdi_data/confirm_delete.html"

    def get_queryset(self):
        return FDIDataPoint.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        )

    def get_success_url(self):
        return reverse(
            "dashboard:country:fdi_data",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        messages.success(self.request, "Data point deleted.")
        return super().form_valid(form)
