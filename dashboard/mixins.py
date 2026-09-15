"""
Improved Dashboard Mixins - apps/dashboard/mixins.py

Key improvements:
1. Smart redirects instead of PermissionDenied errors
2. Member state slug validation for IPA staff
3. Protection against cross-member-state access
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect


class SidebarContextMixin:
    """
    Injects sidebar context variables into every member dashboard view.
    Provides: member_state, new_inquiries_count, draft_opportunities_count.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated and user.user_type == "ipa_staff":
            try:
                member_state = user.ipa_profile.member_state
                context["member_state"] = member_state
                context["new_inquiries_count"] = member_state.inquiries.filter(status="new").count()
                context["draft_opportunities_count"] = member_state.opportunities.filter(status="draft").count()
            except AttributeError:
                pass
        return context


class IPAWASAdminRequiredMixin(LoginRequiredMixin):
    """
    Require user to be IPAWAS HQ Admin.
    Redirects IPA staff to their own dashboard instead of showing error.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # If IPA staff tries to access HQ dashboard, redirect them to their dashboard
        if request.user.user_type == "ipa_staff":
            try:
                member_state_slug = request.user.ipa_profile.member_state.slug
                return redirect("dashboard:country:overview", member_state_slug=member_state_slug)
            except AttributeError:
                raise PermissionDenied("Your account is not properly configured.")

        # Only IPAWAS admins can proceed
        if request.user.user_type != "ipawas_admin":
            raise PermissionDenied("Only IPAWAS HQ administrators can access this page.")

        return super().dispatch(request, *args, **kwargs)


class IPAStaffRequiredMixin(LoginRequiredMixin, SidebarContextMixin):
    """
    Require user to be IPA Staff.
    Redirects HQ admins to HQ dashboard instead of showing error.
    """

    login_url = "accounts:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # If HQ admin tries to access member state dashboard, redirect to HQ
        if request.user.user_type == "ipawas_admin":
            return redirect("dashboard:hq:overview")

        # Only IPA staff can proceed
        if request.user.user_type != "ipa_staff":
            raise PermissionDenied("Only IPA staff members can access this page.")

        return super().dispatch(request, *args, **kwargs)


class MemberStateAccessMixin:
    """
    Validates member state access and filters queryset.

    Critical security layer:
    - Validates URL slug matches user's actual member state
    - Prevents Nigerian staff from accessing Ghana's dashboard
    - HQ admins can view any member state

    Think of this as a "security checkpoint" that verifies you have
    a valid pass for the specific building you're entering.
    """

    def dispatch(self, request, *args, **kwargs):
        # Get the member_state_slug from URL
        url_slug = kwargs.get("member_state_slug")

        if request.user.user_type == "ipa_staff" and url_slug:
            try:
                user_member_state = request.user.ipa_profile.member_state

                # Security Check: Does the URL slug match user's member state?
                if user_member_state.slug != url_slug:
                    # Redirect to their correct dashboard
                    return redirect(
                        "dashboard:country:overview", member_state_slug=user_member_state.slug
                    )

                # Store member state in request for easy access in views
                request.member_state = user_member_state

            except AttributeError:
                raise PermissionDenied("Your account is not properly configured.")

        # HQ admins viewing a specific member state
        elif request.user.user_type == "ipawas_admin" and url_slug:
            from members.models import MemberStateIPA

            request.member_state = get_object_or_404(MemberStateIPA, slug=url_slug)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Filter queryset by member state context."""
        queryset = super().get_queryset()

        # Use the validated member_state from dispatch
        if hasattr(self.request, "member_state"):
            queryset = queryset.filter(member_state=self.request.member_state)

        return queryset


class CanEditProfileMixin(IPAStaffRequiredMixin):
    """Require permission to edit profile."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.ipa_profile.can_edit_profile:
            raise PermissionDenied("You don't have permission to edit the profile.")
        return super().dispatch(request, *args, **kwargs)


class CanCreateOpportunitiesMixin(IPAStaffRequiredMixin):
    """Require permission to create opportunities."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.ipa_profile.can_create_opportunities:
            raise PermissionDenied("You don't have permission to create opportunities.")
        return super().dispatch(request, *args, **kwargs)


class CanPublishMixin(IPAStaffRequiredMixin):
    """Require permission to publish opportunities."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.ipa_profile.can_publish_opportunities:
            raise PermissionDenied("You don't have permission to publish content.")
        return super().dispatch(request, *args, **kwargs)


class CanViewInquiriesMixin(LoginRequiredMixin):
    """
    Allow access to investor inquiries.

    HQ admins: see all inquiries.
    IPA staff: see only their member state's inquiries (filtered in get_queryset).
    No extra per-user permission needed — all active staff handle inquiries.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.user_type not in ("ipawas_admin", "ipa_staff"):
            raise PermissionDenied("You don't have permission to view inquiries.")
        return super().dispatch(request, *args, **kwargs)


class CanManageUsersMixin(LoginRequiredMixin):
    """
    Require permission to manage users.
    HQ admins always have permission.
    IPA staff need specific permission.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # HQ admins always have permission
        if request.user.user_type == "ipawas_admin":
            return super().dispatch(request, *args, **kwargs)

        # IPA staff need specific permission
        if request.user.user_type == "ipa_staff":
            if not request.user.ipa_profile.can_manage_users:
                raise PermissionDenied("You don't have permission to manage users.")
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("Invalid user type.")


class CanViewAnalyticsMixin(IPAStaffRequiredMixin):
    """Require permission to view analytics."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.ipa_profile.can_view_analytics:
            raise PermissionDenied("You don't have permission to view analytics.")
        return super().dispatch(request, *args, **kwargs)
