"""
Dashboard Routing View - apps/dashboard/views/routing.py

Smart router that redirects users to their appropriate dashboard:
- IPAWAS Admin → /dashboard/hq/
- IPA Staff → /dashboard/<their-member-state-slug>/
- Public/Investors → Public site or login
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View

logger = logging.getLogger(__name__)


class DashboardRoutingView(LoginRequiredMixin, View):
    """
    Smart router that sends users to their appropriate dashboard.

    Think of this as a "reception desk" that checks your credentials
    and directs you to the right office.
    """

    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            # HQ Admin → Send to HQ dashboard
            if user.user_type == "ipawas_admin":
                return redirect("dashboard:hq:overview")

            # IPA Staff → Send to their member state dashboard
            elif user.user_type == "ipa_staff":
                try:
                    member_state_slug = user.ipa_profile.member_state.slug
                    return redirect("dashboard:country:overview", member_state_slug=member_state_slug)
                except AttributeError:
                    # IPA staff without a member state assignment yet
                    return redirect("accounts:profile")

            # Investors or other types → Send to public site
            else:
                return redirect("home")

        except Exception as exc:
            logger.exception("DashboardRoutingView crashed for user %s (type=%s): %s",
                             getattr(user, "email", "?"),
                             getattr(user, "user_type", "?"),
                             exc)
            raise
