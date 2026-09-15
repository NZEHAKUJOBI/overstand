"""Investment Incentives CRUD Views"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dashboard.forms import IncentiveForm
from dashboard.mixins import CanEditProfileMixin, IPAStaffRequiredMixin
from media_app.models import MediaFile
from media_app.services.cloudinary_service import CloudinaryService
from members.models import InvestmentIncentive


def _resolve_media_file_id(raw_id, member_state):
    """
    Parse and validate a picker-supplied MediaFile PK.
    Returns the integer ID only if the file belongs to this member state; None otherwise.
    """
    try:
        pk = int(raw_id)
    except (ValueError, TypeError):
        return None
    if MediaFile.objects.filter(pk=pk, member_state=member_state, is_deleted=False).exists():
        return pk
    return None


class IncentiveListView(IPAStaffRequiredMixin, ListView):
    model = InvestmentIncentive
    template_name = "dashboard/members/incentives/list.html"
    context_object_name = "incentives"

    def get_queryset(self):
        return InvestmentIncentive.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        ).prefetch_related("applicable_sectors").order_by("display_order", "title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context


class IncentiveCreateView(CanEditProfileMixin, CreateView):
    model = InvestmentIncentive
    form_class = IncentiveForm
    template_name = "dashboard/members/incentives/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["member_state"] = self.request.user.ipa_profile.member_state
        return kwargs

    def get_success_url(self):
        return reverse(
            "dashboard:country:incentives",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        incentive = form.save(commit=False)
        incentive.member_state = self.request.user.ipa_profile.member_state

        # Media library picker takes priority over direct file upload
        document_file_id = _resolve_media_file_id(
            self.request.POST.get("document_file_id"), incentive.member_state
        )
        if document_file_id:
            incentive.document_file_id = document_file_id
        else:
            document = form.cleaned_data.get("document")
            if document:
                folder = f"ipawas/{incentive.member_state.slug}/incentives"
                result = CloudinaryService.upload_file(document, folder, resource_type="raw")
                if result["success"]:
                    incentive.document_url = result["data"]["secure_url"]
                    incentive.document_name = document.name
                else:
                    messages.error(self.request, f"Document upload failed: {result.get('error')}")

        incentive.save()
        form.save_m2m()
        messages.success(self.request, "Incentive created successfully.")
        return redirect(self.get_success_url())


class IncentiveEditView(CanEditProfileMixin, UpdateView):
    model = InvestmentIncentive
    form_class = IncentiveForm
    template_name = "dashboard/members/incentives/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["member_state"] = self.request.user.ipa_profile.member_state
        return kwargs

    def get_queryset(self):
        return InvestmentIncentive.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        )

    def get_success_url(self):
        return reverse(
            "dashboard:country:incentives",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        incentive = form.save(commit=False)

        document_file_id = _resolve_media_file_id(
            self.request.POST.get("document_file_id"), incentive.member_state
        )
        if document_file_id:
            incentive.document_file_id = document_file_id
        else:
            document = form.cleaned_data.get("document")
            if document:
                folder = f"ipawas/{incentive.member_state.slug}/incentives"
                result = CloudinaryService.upload_file(document, folder, resource_type="raw")
                if result["success"]:
                    incentive.document_url = result["data"]["secure_url"]
                    incentive.document_name = document.name
                else:
                    messages.error(self.request, f"Document upload failed: {result.get('error')}")

        incentive.save()
        form.save_m2m()
        messages.success(self.request, "Incentive updated successfully.")
        return redirect(self.get_success_url())


class IncentiveDeleteView(CanEditProfileMixin, DeleteView):
    model = InvestmentIncentive
    template_name = "dashboard/members/incentives/confirm_delete.html"

    def get_queryset(self):
        return InvestmentIncentive.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        )

    def get_success_url(self):
        return reverse(
            "dashboard:country:incentives",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        messages.success(self.request, "Incentive deleted.")
        return super().form_valid(form)
