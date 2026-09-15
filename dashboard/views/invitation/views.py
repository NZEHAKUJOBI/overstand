"""
Invitation Views
apps/dashboard/views/invitations/views.py

Handles invitation management for both HQ and Member State admins.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, FormView, ListView, View

from core.email.services import get_invitation_email_service, get_system_email_service
from dashboard.mixins import CanManageUsersMixin, MemberStateAccessMixin
from dashboard.utils.activity_logs_services import ActivityLogService, NotificationService
from invitations.forms import BulkInvitationForm, InvitationForm, InvitationRegistrationForm
from invitations.models import Invitation


class InvitationListView(CanManageUsersMixin, ListView):
    """List invitations (filtered by member state for IPA staff)."""

    model = Invitation
    template_name = "dashboard/invitations/list.html"
    context_object_name = "invitations"
    paginate_by = 25

    def _base_queryset(self):
        """Queryset scoped to the current user's member state (no search/filter applied)."""
        qs = Invitation.objects.select_related("member_state", "invited_by")
        if self.request.user.user_type == "ipa_staff":
            qs = qs.filter(member_state=self.request.user.ipa_profile.member_state)
        return qs.order_by("-created_at")

    def get_queryset(self):
        qs = self._base_queryset()

        status = self.request.GET.get("status", "").strip()
        if status in {"pending", "accepted", "expired", "revoked"}:
            qs = qs.filter(status=status)

        role = self.request.GET.get("role", "").strip()
        valid_roles = {"ipa_director", "ipa_manager", "ipa_officer", "ipa_data_entry", "ipa_analyst"}
        if role in valid_roles:
            qs = qs.filter(role=role)

        search = self.request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(email__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.user_type == "ipa_staff":
            member_state = self.request.user.ipa_profile.member_state
            context["member_state"] = member_state

        if self.request.user.user_type == "ipa_staff":
            context["base_template"] = "dashboard/members/base.html"
        else:
            context["base_template"] = "dashboard/hq_admin/base.html"

        # Status counts reflect total scope (unaffected by current filter)
        base = self._base_queryset()
        context["total_count"] = base.count()
        context["accepted_count"] = base.filter(status="accepted").count()
        context["expired_count"] = base.filter(status="expired").count()
        context["revoked_count"] = base.filter(status="revoked").count()
        context["pending_count"] = base.filter(status="pending").count()

        return context


class InvitationDetailView(CanManageUsersMixin, DetailView):
    """View invitation details."""

    model = Invitation
    template_name = "dashboard/invitations/detail.html"
    context_object_name = "invitation"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.user_type == "ipa_staff":
            context["member_state"] = self.request.user.ipa_profile.member_state
            context["base_template"] = "dashboard/members/base.html"
        else:
            context["member_state"] = None
            context["base_template"] = "dashboard/hq_admin/base.html"
        return context


class InvitationCreateView(MemberStateAccessMixin, CanManageUsersMixin, CreateView):
    """Create new invitation."""

    model = Invitation
    form_class = InvitationForm
    template_name = "dashboard/invitations/create.html"

    def get_success_url(self):
        user = self.request.user
        if user.user_type == "ipa_staff":
            return reverse(
                "dashboard:country:invitations:list",
                kwargs={"member_state_slug": user.ipa_profile.member_state.slug},
            )
        return reverse("dashboard:hq:invitations:list")

    def dispatch(self, request, *args, **kwargs):
        # IPA staff must access invitation create via their own member state slug URL.
        # If they hit the flat /dashboard/invitations/create/ path (no slug in URL),
        # redirect them to the correct country-scoped URL.
        if request.user.is_authenticated and request.user.user_type == "ipa_staff":
            url_slug = kwargs.get("member_state_slug")
            if not url_slug:
                try:
                    slug = request.user.ipa_profile.member_state.slug
                    return redirect(
                        "dashboard:country:invitations:create",
                        member_state_slug=slug,
                    )
                except AttributeError:
                    pass
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        # Set member state for IPA staff — always from their profile, never from POST data
        if self.request.user.user_type == "ipa_staff":
            kwargs["member_state"] = self.request.user.ipa_profile.member_state

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.user_type == "ipa_staff":
            member_state = self.request.user.ipa_profile.member_state
            context["member_state"] = member_state
            context["base_template"] = "dashboard/members/base.html"
            context["invitations_list_url"] = reverse(
                "dashboard:country:invitations:list",
                kwargs={"member_state_slug": member_state.slug},
            )
        else:
            context["member_state"] = None
            context["base_template"] = "dashboard/hq_admin/base.html"
            context["invitations_list_url"] = reverse("dashboard:hq:invitations:list")

        return context

    def form_valid(self, form):
        """Save invitation and send email"""
        user = self.request.user

        try:
            with transaction.atomic():
                # Determine user_type and member_state
                user_type = form.cleaned_data.get("user_type", "ipa_staff")
                if user_type == "ipawas_admin":
                    # HQ admin invitation — no member state
                    member_state = None
                elif user.is_ipa_staff and hasattr(user, "ipa_profile"):
                    member_state = user.ipa_profile.member_state
                else:
                    member_state = form.cleaned_data.get("member_state")

                # Create invitation
                invitation = Invitation.objects.create_invitation(
                    email=form.cleaned_data["email"],
                    invited_by=user,
                    member_state=member_state,
                    role=form.cleaned_data.get("role", ""),
                    user_type=user_type,
                    is_primary_contact=form.cleaned_data.get("is_primary_contact", False),
                    invitation_message=form.cleaned_data.get("invitation_message", ""),
                    expires_in_days=int(form.cleaned_data.get("expires_in_days") or 7),
                )

                # Send invitation email
                email_service = get_invitation_email_service()
                email_sent = email_service.send_invitation_email(invitation)

                if not email_sent:
                    messages.warning(
                        self.request,
                        _(
                            "Invitation created but email could not be sent. "
                            "Please resend the invitation manually."
                        ),
                    )
                else:
                    messages.success(
                        self.request,
                        _("Invitation sent successfully to %(email)s")
                        % {"email": invitation.email},
                    )

                # Log activity
                ActivityLogService.log_user_invite(
                    user=user,
                    invitation=invitation,
                    ip_address=self.request.META.get("REMOTE_ADDR"),
                )

                return HttpResponseRedirect(self.get_success_url())

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request, _("Error creating invitation: %(error)s") % {"error": str(e)}
            )
            return self.form_invalid(form)


class InvitationResendView(CanManageUsersMixin, View):
    """Resend invitation email."""

    def post(self, request, pk, member_state_slug=None):
        invitation = get_object_or_404(Invitation, pk=pk)

        # IPA staff can only resend invitations for their own member state.
        # HQ admin invitations (member_state=None) are only manageable by IPAWAS admins.
        user = request.user
        if user.user_type == "ipa_staff" and hasattr(user, "ipa_profile"):
            if invitation.member_state is None or invitation.member_state != user.ipa_profile.member_state:
                messages.error(request, "You don't have permission to resend this invitation.")
                return redirect("dashboard:country:invitations:list", member_state_slug=member_state_slug or user.ipa_profile.member_state.slug)

        try:
            if not invitation.resend():
                messages.error(
                    request,
                    f"Cannot resend invitation (status: {invitation.get_status_display()})"
                )
            else:
                email_service = get_invitation_email_service()
                email_service.send_invitation_email(invitation)
                messages.success(request, f"Invitation resent to {invitation.email}")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        if member_state_slug:
            return redirect("dashboard:country:invitations:list", member_state_slug=member_state_slug)
        return redirect("dashboard:hq:invitations:list")


class InvitationRevokeView(CanManageUsersMixin, View):
    """Revoke invitation."""

    def post(self, request, pk, member_state_slug=None):
        invitation = get_object_or_404(Invitation, pk=pk)

        # IPA staff can only revoke invitations for their own member state.
        # HQ admin invitations (member_state=None) are only manageable by IPAWAS admins.
        user = request.user
        if user.user_type == "ipa_staff" and hasattr(user, "ipa_profile"):
            if invitation.member_state is None or invitation.member_state != user.ipa_profile.member_state:
                messages.error(request, "You don't have permission to revoke this invitation.")
                return redirect("dashboard:country:invitations:list", member_state_slug=member_state_slug or user.ipa_profile.member_state.slug)

        try:
            invitation.revoke(revoked_by=request.user)
            messages.success(request, f"Invitation for {invitation.email} has been revoked")
        except Exception as e:
            messages.error(request, f"Cannot revoke invitation: {str(e)}")

        if member_state_slug:
            return redirect("dashboard:country:invitations:list", member_state_slug=member_state_slug)
        return redirect("dashboard:hq:invitations:list")


class BulkInvitationView(CanManageUsersMixin, FormView):
    """
    Create multiple invitations at once.

    Features:
    - Supports up to 50 emails per batch
    - Handles both HQ admins (with member_state selection) and IPA staff (auto member_state)
    - Creates invitations in transaction (all-or-nothing for creation, but continues on email errors)
    - Sends invitation emails
    - Logs activity
    - Provides detailed success/error feedback
    """

    form_class = BulkInvitationForm
    template_name = "dashboard/invitations/bulk.html"
    success_url = reverse_lazy("dashboard:invitations:list")

    def get_form_kwargs(self):
        """Pass user context to form"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        # Set member state for IPA staff
        if self.request.user.user_type == "ipa_staff":
            kwargs["member_state"] = self.request.user.ipa_profile.member_state

        return kwargs

    def get_context_data(self, **kwargs):
        """Add additional context"""
        context = super().get_context_data(**kwargs)

        # Add member state info for display
        if self.request.user.user_type == "ipa_staff":
            context["member_state"] = self.request.user.ipa_profile.member_state

        if self.request.user.user_type == "ipa_staff":
            context["base_template"] = "dashboard/members/base.html"
        else:
            context["base_template"] = "dashboard/hq_admin/base.html"

        return context

    def form_valid(self, form):
        """Create multiple invitations"""
        user = self.request.user
        emails = form.cleaned_data["emails"]  # Already validated and deduplicated
        role = form.cleaned_data["role"]
        invitation_message = form.cleaned_data.get("invitation_message", "")

        # Determine member state
        if user.user_type == "ipa_staff":
            # IPA staff: use their member state
            member_state = user.ipa_profile.member_state
        else:
            # HQ admin: member_state from form (may be None for HQ admin bulk invitations)
            member_state = form.cleaned_data.get("member_state")

        # Track results
        created_invitations = []
        failed_invitations = []
        email_errors = []

        try:
            # Create all invitations in a transaction
            with transaction.atomic():
                for email in emails:
                    try:
                        # Check if invitation already exists
                        existing = Invitation.objects.filter(
                            email=email, member_state=member_state, status="pending"
                        ).first()

                        if existing:
                            failed_invitations.append(
                                {"email": email, "reason": _("Pending invitation already exists")}
                            )
                            continue

                        # Create invitation
                        invitation = Invitation.objects.create_invitation(
                            email=email,
                            invited_by=user,
                            member_state=member_state,
                            role=role,
                            user_type="ipawas_admin" if member_state is None else "ipa_staff",
                            invitation_message=invitation_message,
                            expires_in_days=7,
                        )

                        created_invitations.append(invitation)

                    except Exception as e:
                        failed_invitations.append({"email": email, "reason": str(e)})

            # Send emails (outside transaction so email failures don't rollback invitations)
            if created_invitations:
                email_service = get_invitation_email_service()

                for invitation in created_invitations:
                    try:
                        # Send invitation email
                        email_sent = email_service.send_invitation_email(invitation)

                        if not email_sent:
                            messages.warning(
                                self.request,
                                _(
                                    "Invitation created but email could not be sent. "
                                    "Please resend the invitation manually."
                                ),
                            )
                        else:
                            messages.success(
                                self.request,
                                _("Invitation sent successfully to %(email)s")
                                % {"email": invitation.email},
                            )

                    except Exception as e:
                        email_errors.append({"email": invitation.email, "reason": str(e)})

            # Log activity
            ms_label = member_state.ipa_acronym if member_state else "HQ Admin"
            ActivityLogService.log_activity(
                user=user,
                action_type="bulk_invitation",
                description=f"Bulk invited {len(created_invitations)} users for {ms_label}",
                member_state=member_state,
                changes={
                    "total_emails": len(emails),
                    "created": len(created_invitations),
                    "failed": len(failed_invitations),
                    "email_errors": len(email_errors),
                },
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

            # Provide feedback
            if created_invitations:
                messages.success(
                    self.request,
                    _("Successfully created %(count)d invitation(s) for %(state)s")
                    % {"count": len(created_invitations), "state": ms_label},
                )

            if failed_invitations:
                error_details = []
                for item in failed_invitations[:5]:  # Show first 5 errors
                    error_details.append(f"{item['email']}: {item['reason']}")

                error_message = _("Failed to create %(count)d invitation(s): %(details)s") % {
                    "count": len(failed_invitations),
                    "details": "; ".join(error_details),
                }

                if len(failed_invitations) > 5:
                    error_message += f" (and {len(failed_invitations) - 5} more)"

                messages.warning(self.request, error_message)

            if email_errors:
                messages.warning(
                    self.request,
                    _(
                        "%(count)d invitation(s) created but email failed to send. "
                        "You can resend from the invitations list."
                    )
                    % {"count": len(email_errors)},
                )

            # Redirect to list even if there were errors
            return HttpResponseRedirect(self.success_url)

        except Exception as e:
            messages.error(
                self.request, _("Error processing bulk invitations: %(error)s") % {"error": str(e)}
            )
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form validation errors"""
        # Extract and display form errors
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    messages.error(self.request, error)
                else:
                    messages.error(self.request, f"{field.replace('_', ' ').title()}: {error}")

        return super().form_invalid(form)


# class BulkInvitationView(CanManageUsersMixin, FormView):
#     """Send multiple invitations."""

#     template_name = "dashboard/invitations/bulk.html"

# Implement bulk invitation logic


# class InvitationRegistrationView(FormView):
#     """Public registration page from invitation token."""

#     template_name = "dashboard/invitations/register.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         token = self.kwargs["token"]

#         try:
#             invitation = Invitation.objects.get(token=token, status="pending")
#             context["invitation"] = invitation
#         except Invitation.DoesNotExist:
#             context["error"] = "Invalid or expired invitation"

#         return context


class InvitationRegistrationView(FormView):
    """
    Public registration view for invited users.
    Uses token from invitation.
    """

    form_class = InvitationRegistrationForm
    template_name = "invitations/registration.html"

    def dispatch(self, request, *args, **kwargs):
        """Validate invitation token"""
        token = kwargs.get("token")

        try:
            self.invitation = Invitation.objects.get_by_token(token)

            # Mark registration started
            self.invitation.mark_registration_started()

        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, "invitations/invalid_token.html", {"error_message": str(e)})

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Redirect to appropriate dashboard after registration"""
        if self.invitation.member_state:
            return reverse(
                "dashboard:country:overview",
                kwargs={"member_state_slug": self.invitation.member_state.slug},
            )
        # HQ admin users go to the HQ dashboard
        return reverse("dashboard:hq:overview")

    def get_form_kwargs(self):
        """Pass invitation to form"""
        kwargs = super().get_form_kwargs()
        kwargs["invitation"] = self.invitation
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitation"] = self.invitation
        context["member_state"] = self.invitation.member_state
        context["role"] = self.invitation.get_role_display()
        return context

    def form_valid(self, form):
        """Create user and IPA profile"""
        try:
            with transaction.atomic():
                # Create user — user_type is set from invitation.user_type in form.save()
                user = form.save(commit=False)
                user.accepted_invitation_at = timezone.now()
                user.save()

                ipa_user = None

                if self.invitation.member_state:
                    # IPA staff path: create the IPAUser profile
                    from accounts.models import IPAUser

                    ipa_user = IPAUser.objects.create(
                        user=user,
                        member_state=self.invitation.member_state,
                        role=self.invitation.role,
                        is_primary_contact=self.invitation.is_primary_contact,
                        dashboard_access_granted_at=timezone.now(),
                    )
                # HQ admin path: no IPAUser record needed

                # Mark invitation as accepted
                self.invitation.accept(user)

                # Send welcome email
                email_service = get_system_email_service()
                email_service.send_welcome_email(user, ipa_user)

                # Log activity
                ActivityLogService.log_user_create(
                    user=user,
                    created_by=self.invitation.invited_by,
                    ipa_user=ipa_user,
                    ip_address=self.request.META.get("REMOTE_ADDR"),
                )

                # Notify inviter
                if self.invitation.invited_by:
                    NotificationService.notify_invitation_accepted(
                        inviter=self.invitation.invited_by,
                        invitation=self.invitation,
                        new_user=user,
                    )

                # Log user in
                login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")

                messages.success(
                    self.request,
                    _("Welcome to IPAWAS! Your account has been created successfully."),
                )

                return HttpResponseRedirect(self.get_success_url())

        except Exception as e:
            messages.error(self.request, _("Error creating account: %(error)s") % {"error": str(e)})
            return self.form_invalid(form)


class InvitationQRView(CanManageUsersMixin, DetailView):
    """
    Display and print the QR code for a single invitation.
    Standalone page — no nav bar, print-optimised.
    """

    model = Invitation
    template_name = "dashboard/invitations/qr_card.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        invitation = self.object
        abs_url = self.request.build_absolute_uri(invitation.get_registration_url())
        ctx["registration_url"] = abs_url
        ctx["qr_api_url"] = (
            f"https://api.qrserver.com/v1/create-qr-code/"
            f"?size=280x280&color=1b7a4c&bgcolor=ffffff&qzone=2&data={abs_url}"
        )
        return ctx


class InvitationBulkQRView(CanManageUsersMixin, View):
    """
    Print-ready page showing QR cards for ALL pending invitations
    in the current admin's scope. One card per invitee.
    """

    template_name = "dashboard/invitations/qr_bulk.html"

    def get(self, request, member_state_slug=None):
        from members.models import MemberStateIPA

        qs = Invitation.objects.filter(status="pending")

        if member_state_slug:
            member_state = get_object_or_404(MemberStateIPA, slug=member_state_slug)
            qs = qs.filter(member_state=member_state)
        elif not (request.user.is_staff or getattr(request.user, "user_type", "") == "ipawas_admin"):
            # IPA staff: scope to their own member state
            try:
                qs = qs.filter(member_state=request.user.ipa_profile.member_state)
            except Exception:
                qs = Invitation.objects.none()

        invitations = []
        for inv in qs.select_related("member_state").order_by("member_state__country_name", "email"):
            abs_url = request.build_absolute_uri(inv.get_registration_url())
            invitations.append({
                "invitation": inv,
                "registration_url": abs_url,
                "qr_api_url": (
                    f"https://api.qrserver.com/v1/create-qr-code/"
                    f"?size=240x240&color=1b7a4c&bgcolor=ffffff&qzone=2&data={abs_url}"
                ),
            })

        return render(request, self.template_name, {
            "invitations": invitations,
            "member_state_slug": member_state_slug,
        })
