import logging

logger = logging.getLogger(__name__)
"""
Dashboard Router Middleware - apps/dashboard/middleware.py

Automatically routes authenticated users to their appropriate dashboard:
- IPAWAS HQ Admin → /dashboard/hq/
- Member State IPA Staff → /dashboard/

This middleware ensures users land on the correct dashboard based on their type.
"""

from django.shortcuts import redirect


class DashboardRouterMiddleware:
    """
    Routes users to appropriate dashboard based on user_type.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process authenticated users
        if request.user.is_authenticated:
            logger.debug("DashboardRouterMiddleware: routing authenticated user")
            # Check if user is accessing dashboard root
            if request.path == "/dashboard/" or request.path == "/dashboard":
                # Route based on user type
                if hasattr(request.user, "user_type"):
                    if request.user.user_type == "ipawas_admin":
                        # HQ Admin → HQ Dashboard
                        return redirect("dashboard:hq:overview")
                    elif request.user.user_type == "ipa_staff":
                        # IPA Staff → Country Dashboard (requires member_state slug)
                        try:
                            slug = request.user.ipa_profile.member_state.slug
                            return redirect("dashboard:country:overview", member_state_slug=slug)
                        except Exception:
                            pass

        response = self.get_response(request)
        return response


class DashboardAccessMiddleware:
    """
    Ensures users can only access dashboards they have permission for.
    - HQ Admins can access both HQ and Member State dashboards
    - IPA Staff can only access Member State dashboard for their country
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process authenticated users accessing dashboard
        if request.user.is_authenticated and request.path.startswith("/dashboard/"):
            # Check HQ dashboard access
            if request.path.startswith("/dashboard/hq/"):
                if (
                    not hasattr(request.user, "user_type")
                    or request.user.user_type != "ipawas_admin"
                ):
                    # Non-HQ admin trying to access HQ dashboard — redirect to their country dashboard
                    try:
                        slug = request.user.ipa_profile.member_state.slug
                        return redirect("dashboard:country:overview", member_state_slug=slug)
                    except Exception:
                        pass

        response = self.get_response(request)
        return response
