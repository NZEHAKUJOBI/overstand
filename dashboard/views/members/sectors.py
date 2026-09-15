"""Member State Sectors Views"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify
from django.views.generic import DeleteView, FormView, ListView, UpdateView, View

from core.models import Sector as GlobalSector
from dashboard.forms import SectorAddForm, SectorEditForm
from dashboard.mixins import CanEditProfileMixin, IPAStaffRequiredMixin
from members.models import MemberStateSector


class SectorListView(IPAStaffRequiredMixin, ListView):
    model = MemberStateSector
    template_name = "dashboard/members/sectors/list.html"
    context_object_name = "sectors"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get member state
        member_state = self.request.user.ipa_profile.member_state
        context["member_state"] = member_state

        # Calculate counts for header stats
        context["opportunities_count"] = member_state.opportunities.count()
        context["sectors_count"] = member_state.sectors.count()
        context["team_members_count"] = member_state.ipa_users.filter(is_active=True).count()

        # Checklist flags for completion items
        context["has_basic_info"] = bool(member_state.ipa_full_name and member_state.overview)
        context["has_sectors"] = member_state.sectors.exists()
        context["has_published_opportunities"] = member_state.opportunities.filter(
            status="active"
        ).exists()
        # context["has_featured_image"] = bool(member_state.featured_image)

        return context

    def get_queryset(self):
        return MemberStateSector.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        ).order_by("display_order")


class SectorAddView(CanEditProfileMixin, FormView):
    form_class = SectorAddForm
    template_name = "dashboard/members/sectors/form.html"

    def get_success_url(self):
        return reverse(
            "dashboard:country:sectors",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        context["existing_sector_names"] = list(
            GlobalSector.objects.values_list("name", flat=True).order_by("name")
        )
        return context

    def form_valid(self, form):
        member_state = self.request.user.ipa_profile.member_state
        sector_name = form.cleaned_data["sector_name"]

        # Ensure unique slug — append a suffix if the auto-slug is taken
        base_slug = slugify(sector_name)
        slug = base_slug
        counter = 1
        while GlobalSector.objects.filter(slug=slug).exclude(name=sector_name).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        sector, _ = GlobalSector.objects.get_or_create(
            name=sector_name,
            defaults={"slug": slug},
        )

        if MemberStateSector.objects.filter(member_state=member_state, sector=sector).exists():
            form.add_error("sector_name", "This sector has already been added to your country profile.")
            return self.form_invalid(form)

        MemberStateSector.objects.create(
            member_state=member_state,
            sector=sector,
            description=form.cleaned_data.get("description", ""),
            investment_potential=form.cleaned_data.get("investment_potential", ""),
            is_priority=form.cleaned_data.get("is_priority", False),
        )
        messages.success(self.request, f"Sector \"{sector_name}\" added successfully.")
        return redirect(self.get_success_url())



class SectorEditView(CanEditProfileMixin, UpdateView):
    model = MemberStateSector
    form_class = SectorEditForm
    template_name = "dashboard/members/sectors/form.html"

    def get_queryset(self):
        return MemberStateSector.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def get_success_url(self):
        return reverse(
            "dashboard:country:sectors",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )


class SectorDeleteView(CanEditProfileMixin, DeleteView):
    model = MemberStateSector
    template_name = "dashboard/members/sectors/confirm_delete.html"

    def get_queryset(self):
        return MemberStateSector.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def get_success_url(self):
        return reverse(
            "dashboard:country:sectors",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )


class SectorReorderView(CanEditProfileMixin, View):
    def post(self, request, member_state_slug):
        # Handle reordering logic
        return redirect("dashboard:country:sectors", member_state_slug=member_state_slug)
