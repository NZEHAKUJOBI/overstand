"""
Permission System for IPAWAS Dashboard.

Provides mixins, decorators, and utilities for role-based access control.
Ensures users can only access their own member state's data.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from members.models import MemberStateIPA

# ============================================================================
# MIXINS FOR CLASS-BASED VIEWS
# ============================================================================


class IPAStaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin to require user to be IPA staff.
    Redirects non-IPA users to home page.
    """

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_ipa_staff

    def handle_no_permission(self):
        messages.error(self.request, _("You must be an IPA staff member to access this page"))
        return redirect("home")


class IPAWASAdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin to require user to be IPAWAS admin.
    """

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_ipawas_admin or user.is_superuser)

    def handle_no_permission(self):
        messages.error(self.request, _("You must be an IPAWAS administrator to access this page"))
        return redirect("home")


class MemberStateAccessMixin:
    """
    Mixin to ensure IPA users can only access their own member state's data.
    Automatically filters querysets by member state.
    """

    def get_member_state(self):
        """Get the member state for the current user"""
        user = self.request.user

        # IPAWAS admins can access any member state
        if user.is_ipawas_admin or user.is_superuser:
            # Check if member state is specified in URL or query params
            member_state_slug = self.kwargs.get("member_state_slug") or self.request.GET.get(
                "member_state"
            )

            if member_state_slug:

                return MemberStateIPA.objects.get(slug=member_state_slug)

            return None

        # IPA staff can only access their own member state
        if user.is_ipa_staff and hasattr(user, "ipa_profile"):
            return user.ipa_profile.member_state

        return None

    def get_queryset(self):
        """Filter queryset by member state"""
        queryset = super().get_queryset()
        member_state = self.get_member_state()

        if member_state and hasattr(queryset.model, "member_state"):
            queryset = queryset.filter(member_state=member_state)

        return queryset

    def get_context_data(self, **kwargs):
        """Add member state to context"""
        context = super().get_context_data(**kwargs)
        context["current_member_state"] = self.get_member_state()
        return context


class PermissionRequiredMixin:
    """
    Mixin to check specific IPA permissions.

    Usage:
        class MyView(PermissionRequiredMixin, ...):
            required_permission = 'can_publish_opportunities'
    """

    required_permission = None

    def dispatch(self, request, *args, **kwargs):
        """Check permission before dispatching"""
        if not self.has_permission():
            messages.error(request, _("You don't have permission to perform this action"))
            return redirect("dashboard:country:overview")

        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        """Check if user has required permission"""
        user = self.request.user

        # IPAWAS admins have all permissions
        if user.is_ipawas_admin or user.is_superuser:
            return True

        # Check IPA user permission
        if user.is_ipa_staff and hasattr(user, "ipa_profile"):
            if self.required_permission:
                return getattr(user.ipa_profile, self.required_permission, False)
            return True

        return False


class CanEditProfileMixin(PermissionRequiredMixin):
    """Mixin to check can_edit_profile permission"""

    required_permission = "can_edit_profile"


class CanManageSectorsMixin(PermissionRequiredMixin):
    """Mixin to check can_manage_sectors permission"""

    required_permission = "can_manage_sectors"


class CanCreateOpportunitiesMixin(PermissionRequiredMixin):
    """Mixin to check can_create_opportunities permission"""

    required_permission = "can_create_opportunities"


class CanPublishOpportunitiesMixin(PermissionRequiredMixin):
    """Mixin to check can_publish_opportunities permission"""

    required_permission = "can_publish_opportunities"


class CanManageUsersMixin(PermissionRequiredMixin):
    """Mixin to check can_manage_users permission"""

    required_permission = "can_manage_users"


class CanViewAnalyticsMixin(PermissionRequiredMixin):
    """Mixin to check can_view_analytics permission"""

    required_permission = "can_view_analytics"


class CanExportDataMixin(PermissionRequiredMixin):
    """Mixin to check can_export_data permission"""

    required_permission = "can_export_data"


# ============================================================================
# DECORATORS FOR FUNCTION-BASED VIEWS
# ============================================================================


def ipa_staff_required(view_func):
    """
    Decorator to require user to be IPA staff.

    Usage:
        @ipa_staff_required
        def my_view(request):
            ...
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("Please log in to access this page"))
            return redirect("login")

        if not request.user.is_ipa_staff:
            messages.error(request, _("You must be an IPA staff member to access this page"))
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return wrapper


def ipawas_admin_required(view_func):
    """
    Decorator to require user to be IPAWAS admin.

    Usage:
        @ipawas_admin_required
        def my_view(request):
            ...
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("Please log in to access this page"))
            return redirect("login")

        if not (request.user.is_ipawas_admin or request.user.is_superuser):
            messages.error(request, _("You must be an IPAWAS administrator to access this page"))
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return wrapper


def permission_required(permission_name):
    """
    Decorator to check specific IPA permission.

    Usage:
        @permission_required('can_publish_opportunities')
        def my_view(request):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, _("Please log in to access this page"))
                return redirect("login")

            # IPAWAS admins have all permissions
            if request.user.is_ipawas_admin or request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check IPA permission
            if request.user.is_ipa_staff and hasattr(request.user, "ipa_profile"):
                if getattr(request.user.ipa_profile, permission_name, False):
                    return view_func(request, *args, **kwargs)

            messages.error(request, _("You don't have permission to perform this action"))
            return redirect("dashboard:country:overview")

        return wrapper

    return decorator


def member_state_access_required(view_func):
    """
    Decorator to ensure user can only access their own member state's data.
    Expects member_state_id or member_state_slug in kwargs.

    Usage:
        @member_state_access_required
        def my_view(request, member_state_slug):
            ...
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("Please log in to access this page"))
            return redirect("login")

        # IPAWAS admins can access any member state
        if request.user.is_ipawas_admin or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # IPA staff can only access their own member state
        if request.user.is_ipa_staff and hasattr(request.user, "ipa_profile"):
            user_member_state = request.user.ipa_profile.member_state

            # Get member state from kwargs
            member_state = None
            if "member_state_slug" in kwargs:
                member_state = MemberStateIPA.objects.get(slug=kwargs["member_state_slug"])
            elif "member_state_id" in kwargs:
                member_state = MemberStateIPA.objects.get(id=kwargs["member_state_id"])

            if member_state and member_state != user_member_state:
                raise PermissionDenied(_("You can only access your own member state's data"))

            return view_func(request, *args, **kwargs)

        messages.error(request, _("Invalid access"))
        return redirect("home")

    return wrapper


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def user_can_edit_object(user, obj):
    """
    Check if user can edit a specific object.

    Args:
        user: User instance
        obj: Object to check (must have member_state attribute)

    Returns:
        bool: True if user can edit object
    """
    # IPAWAS admins can edit anything
    if user.is_ipawas_admin or user.is_superuser:
        return True

    # IPA staff can only edit their member state's objects
    if user.is_ipa_staff and hasattr(user, "ipa_profile"):
        if hasattr(obj, "member_state"):
            return obj.member_state == user.ipa_profile.member_state

    return False


def user_can_publish(user):
    """
    Check if user can publish content.

    Args:
        user: User instance

    Returns:
        bool: True if user can publish
    """
    # IPAWAS admins can publish
    if user.is_ipawas_admin or user.is_superuser:
        return True

    # Check IPA permission
    if user.is_ipa_staff and hasattr(user, "ipa_profile"):
        return user.ipa_profile.can_publish_opportunities

    return False


def user_can_manage_users(user):
    """
    Check if user can manage other users.

    Args:
        user: User instance

    Returns:
        bool: True if user can manage users
    """
    # IPAWAS admins can manage all users
    if user.is_ipawas_admin or user.is_superuser:
        return True

    # IPA admins with permission
    if user.is_ipa_staff and hasattr(user, "ipa_profile"):
        return user.ipa_profile.can_manage_users

    return False


def get_user_member_state(user):
    """
    Get the member state for a user.

    Args:
        user: User instance

    Returns:
        MemberStateIPA instance or None
    """
    if user.is_ipa_staff and hasattr(user, "ipa_profile"):
        return user.ipa_profile.member_state
    return None


def get_user_permissions_dict(user):
    """
    Get dictionary of all permissions for a user.

    Args:
        user: User instance

    Returns:
        dict: Permissions dictionary
    """
    # IPAWAS admins have all permissions
    if user.is_ipawas_admin or user.is_superuser:
        return {
            "publish_opportunities": True,
            "approve_data": True,
            "manage_users": True,
            "edit_profile": True,
            "manage_sectors": True,
            "create_opportunities": True,
            "edit_incentives": True,
            "manage_success_stories": True,
            "view_inquiries": True,
            "respond_to_inquiries": True,
            "view_analytics": True,
            "export_data": True,
        }

    # IPA staff permissions
    if user.is_ipa_staff and hasattr(user, "ipa_profile"):
        return user.ipa_profile.get_permissions_summary()

    # No permissions for other users
    return {}


class ObjectPermissionChecker:
    """
    Helper class for checking object-level permissions.

    Usage:
        checker = ObjectPermissionChecker(request.user)
        if checker.can_edit(opportunity):
            ...
    """

    def __init__(self, user):
        self.user = user

    def can_view(self, obj):
        """Check if user can view object"""
        # Everyone can view published content
        if hasattr(obj, "is_published") and obj.is_published:
            return True

        # Check ownership
        return user_can_edit_object(self.user, obj)

    def can_edit(self, obj):
        """Check if user can edit object"""
        return user_can_edit_object(self.user, obj)

    def can_delete(self, obj):
        """Check if user can delete object"""
        # Only admins can delete
        if self.user.is_ipawas_admin or self.user.is_superuser:
            return True

        if self.user.is_ipa_staff and hasattr(self.user, "ipa_profile"):
            if self.user.ipa_profile.role == "ipa_director":
                return user_can_edit_object(self.user, obj)

        return False

    def can_publish(self, obj):
        """Check if user can publish object"""
        # Must be able to edit AND have publish permission
        if not user_can_edit_object(self.user, obj):
            return False

        return user_can_publish(self.user)
