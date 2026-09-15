"""
Team Management Views - apps/dashboard/views/members/team.py

Handles listing, activating/deactivating, and updating roles for IPA team
members belonging to a member state.
"""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView, View

from accounts.models import IPAUser
from dashboard.mixins import IPAStaffRequiredMixin


class TeamView(IPAStaffRequiredMixin, TemplateView):
    """List all team members for the current member state."""

    template_name = "dashboard/members/team.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.request.user.ipa_profile.member_state

        team_members = (
            IPAUser.objects.filter(member_state=member_state)
            .select_related("user")
            .order_by("-is_primary_contact", "user__first_name")
        )

        today = timezone.now().date()
        active_count = sum(
            1
            for m in team_members
            if m.last_dashboard_login and m.last_dashboard_login.date() == today
        )

        director_roles = {"ipa_director", "ipa_manager"}
        admin_count = sum(1 for m in team_members if m.role in director_roles)

        context["team_members"] = team_members
        context["admin_count"] = admin_count
        context["active_count"] = active_count
        return context


class TeamMemberDeactivateView(IPAStaffRequiredMixin, View):
    """Deactivate a team member (must have can_manage_users)."""

    def post(self, request, pk, **kwargs):
        if not request.user.ipa_profile.can_manage_users:
            messages.error(request, "You do not have permission to manage users.")
            return redirect("dashboard:country:team")

        member_state = request.user.ipa_profile.member_state
        member = get_object_or_404(IPAUser, pk=pk, member_state=member_state)

        if member.user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect("dashboard:country:team")

        member.is_active = False
        member.save(update_fields=["is_active"])
        messages.success(request, f"{member.user.get_full_name()} has been deactivated.")
        return redirect("dashboard:country:team")


class TeamMemberActivateView(IPAStaffRequiredMixin, View):
    """Reactivate a previously deactivated team member."""

    def post(self, request, pk, **kwargs):
        if not request.user.ipa_profile.can_manage_users:
            messages.error(request, "You do not have permission to manage users.")
            return redirect("dashboard:country:team")

        member_state = request.user.ipa_profile.member_state
        member = get_object_or_404(IPAUser, pk=pk, member_state=member_state)
        member.is_active = True
        member.save(update_fields=["is_active"])
        messages.success(request, f"{member.user.get_full_name()} has been reactivated.")
        return redirect("dashboard:country:team")


class TeamMemberUpdateRoleView(IPAStaffRequiredMixin, View):
    """
    Update a team member's role (and auto-cascade permissions via model.save()).
    Only users with can_manage_users may call this.
    A director cannot downgrade another director unless they are themselves
    a director — prevents privilege escalation.
    """

    VALID_ROLES = {role for role, _ in IPAUser.IPA_ROLES}

    def post(self, request, pk, **kwargs):
        if not request.user.ipa_profile.can_manage_users:
            return JsonResponse(
                {"success": False, "error": "You do not have permission to manage users."},
                status=403,
            )

        member_state = request.user.ipa_profile.member_state
        member = get_object_or_404(IPAUser, pk=pk, member_state=member_state)

        if member.user == request.user:
            return JsonResponse(
                {"success": False, "error": "You cannot change your own role."},
                status=400,
            )

        new_role = request.POST.get("role", "").strip()
        if new_role not in self.VALID_ROLES:
            return JsonResponse(
                {"success": False, "error": "Invalid role selected."},
                status=400,
            )

        # Only a director can assign the director role
        requester_role = request.user.ipa_profile.role
        if new_role == "ipa_director" and requester_role != "ipa_director":
            return JsonResponse(
                {"success": False, "error": "Only an IPA Director can assign the Director role."},
                status=403,
            )

        old_role_display = member.get_role_display()
        member.role = new_role
        # model.save() auto-cascades all permission fields based on the new role
        member.save()
        new_role_display = member.get_role_display()

        messages.success(
            request,
            f"{member.user.get_full_name()}'s role has been updated from "
            f"{old_role_display} to {new_role_display}.",
        )
        return JsonResponse(
            {
                "success": True,
                "message": f"Role updated to {new_role_display}.",
                "new_role": new_role,
                "new_role_display": new_role_display,
                # Return refreshed permissions so the card updates without a reload
                "permissions": {
                    "can_publish_opportunities": member.can_publish_opportunities,
                    "can_manage_users": member.can_manage_users,
                    "can_view_analytics": member.can_view_analytics,
                },
            }
        )
