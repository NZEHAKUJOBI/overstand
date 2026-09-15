"""
Views for Invitation System.

Handles:
- Creating invitations (HQ admin, IPA admin)
- Viewing invitation lists
- Resending/revoking invitations
- Registration from invitation tokens
"""

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, FormView, ListView

from core.email.services import get_invitation_email_service, get_system_email_service
from dashboard.utils.activity_logs_services import ActivityLogService, NotificationService

from .forms import (
    BulkInvitationForm,
    InvitationForm,
    InvitationRegistrationForm,
    ResendInvitationForm,
    RevokeInvitationForm,
)
from .models import Invitation

User = get_user_model()


class InvitationAccessMixin(UserPassesTestMixin):
    """
    Mixin to ensure user can manage invitations.
    Either IPAWAS admin or IPA admin with can_manage_users permission.
    """

    def test_func(self):
        user = self.request.user

        # IPAWAS admins can always manage invitations
        if user.is_ipawas_admin or user.is_superuser:
            return True

        # IPA admins with can_manage_users permission
        if user.is_ipa_staff and hasattr(user, "ipa_profile"):
            return user.ipa_profile.can_manage_users

        return False

    def handle_no_permission(self):
        messages.error(self.request, _("You don't have permission to manage invitations"))
        return redirect("dashboard:country:overview")


class InvitationListView(LoginRequiredMixin, InvitationAccessMixin, ListView):
    """
    List all invitations.

    - IPAWAS admins see all invitations
    - IPA admins see only their member state's invitations
    """

    model = Invitation
    template_name = "invitations/invitation_list.html"
    context_object_name = "invitations"
    paginate_by = 25

    def get_queryset(self):
        """Filter invitations based on user role"""
        user = self.request.user
        queryset = Invitation.objects.select_related("member_state", "invited_by", "created_user")

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # IPA admins see only their member state
        if user.is_ipa_staff and hasattr(user, "ipa_profile"):
            queryset = queryset.filter(member_state=user.ipa_profile.member_state)

        # Filter by member state (for IPAWAS admins)
        member_state_id = self.request.GET.get("member_state")
        if member_state_id and user.is_ipawas_admin:
            queryset = queryset.filter(member_state_id=member_state_id)

        # Search by email
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(email__icontains=search)

        return queryset.order_by("-invited_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter options
        context["status_filter"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("search", "")

        # Add counts by status
        base_qs = self.get_queryset()
        context["pending_count"] = base_qs.filter(status="pending").count()
        context["accepted_count"] = base_qs.filter(status="accepted").count()
        context["expired_count"] = base_qs.filter(status="expired").count()
        context["revoked_count"] = base_qs.filter(status="revoked").count()

        # Member state filter for IPAWAS admins
        if self.request.user.is_ipawas_admin:
            from members.models import MemberStateIPA

            context["member_states"] = MemberStateIPA.objects.filter(is_active=True).order_by(
                "country_name"
            )
            context["selected_member_state"] = self.request.GET.get("member_state", "")

        return context


class InvitationDetailView(LoginRequiredMixin, InvitationAccessMixin, DetailView):
    """View invitation details"""

    model = Invitation
    template_name = "invitations/invitation_detail.html"
    context_object_name = "invitation"

    def get_queryset(self):
        """Filter invitations based on user role"""
        user = self.request.user
        queryset = Invitation.objects.select_related(
            "member_state", "invited_by", "created_user", "revoked_by"
        )

        # IPA admins can only see their member state's invitations
        if user.is_ipa_staff and hasattr(user, "ipa_profile"):
            queryset = queryset.filter(member_state=user.ipa_profile.member_state)

        return queryset


class InvitationCreateView(LoginRequiredMixin, InvitationAccessMixin, CreateView):
    """Create new invitation"""

    model = Invitation
    form_class = InvitationForm
    template_name = "invitations/invitation_create.html"
    success_url = reverse_lazy("dashboard:invitations:list")

    def get_form_kwargs(self):
        """Pass user and member state to form"""
        kwargs = super().get_form_kwargs()
        user = self.request.user

        # Set invited_by
        kwargs["invited_by"] = user

        # Set member_state for IPA admins
        if user.is_ipa_staff and hasattr(user, "ipa_profile"):
            kwargs["member_state"] = user.ipa_profile.member_state

        return kwargs

    def form_valid(self, form):
        """Save invitation and send email"""
        user = self.request.user

        try:
            with transaction.atomic():
                # Get or set member state
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
                    user_type=form.cleaned_data.get("user_type", "ipa_staff"),
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

                return HttpResponseRedirect(self.success_url)

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request, _("Error creating invitation: %(error)s") % {"error": str(e)}
            )
            return self.form_invalid(form)


class InvitationResendView(LoginRequiredMixin, InvitationAccessMixin, FormView):
    """Resend invitation email"""

    form_class = ResendInvitationForm
    template_name = "invitations/invitation_resend.html"

    def dispatch(self, request, *args, **kwargs):
        self.invitation = get_object_or_404(Invitation, pk=kwargs["pk"])

        # Check permission — IPA staff can only manage their own member state's invitations.
        # HQ admin invitations (member_state=None) are only manageable by IPAWAS admins.
        user = request.user
        if user.is_ipa_staff and hasattr(user, "ipa_profile"):
            if self.invitation.member_state is None:
                raise PermissionDenied
            if self.invitation.member_state != user.ipa_profile.member_state:
                raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitation"] = self.invitation
        return context

    def form_valid(self, form):
        """Resend invitation"""
        try:
            # Resend invitation (extends expiration)
            if not self.invitation.resend():
                messages.error(
                    self.request,
                    _("Cannot resend this invitation (status: %(status)s)")
                    % {"status": self.invitation.get_status_display()},
                )
                return redirect("dashboard:invitations:detail", pk=self.invitation.pk)

            # Send email
            email_service = get_invitation_email_service()
            email_sent = email_service.send_invitation_email(self.invitation)

            if email_sent:
                messages.success(
                    self.request,
                    _("Invitation resent successfully to %(email)s")
                    % {"email": self.invitation.email},
                )
            else:
                messages.warning(self.request, _("Invitation updated but email could not be sent"))

            # Log activity
            ActivityLogService.log_activity(
                user=self.request.user,
                action_type="invitation_resend",
                description=f"Resent invitation to {self.invitation.email}",
                member_state=self.invitation.member_state,
                content_object=self.invitation,
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

            return redirect("dashboard:invitations:detail", pk=self.invitation.pk)

        except Exception as e:
            messages.error(
                self.request, _("Error resending invitation: %(error)s") % {"error": str(e)}
            )
            return redirect("dashboard:invitations:detail", pk=self.invitation.pk)


class InvitationRevokeView(LoginRequiredMixin, InvitationAccessMixin, FormView):
    """Revoke invitation"""

    form_class = RevokeInvitationForm
    template_name = "invitations/invitation_revoke.html"

    def dispatch(self, request, *args, **kwargs):
        self.invitation = get_object_or_404(Invitation, pk=kwargs["pk"])

        # Check permission — HQ admin invitations only manageable by IPAWAS admins
        user = request.user
        if user.is_ipa_staff and hasattr(user, "ipa_profile"):
            if self.invitation.member_state is None:
                raise PermissionDenied
            if self.invitation.member_state != user.ipa_profile.member_state:
                raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitation"] = self.invitation
        return context

    def form_valid(self, form):
        """Revoke invitation"""
        try:
            reason = form.cleaned_data.get("reason", "")
            self.invitation.revoke(revoked_by=self.request.user, reason=reason)

            messages.success(
                self.request,
                _("Invitation to %(email)s has been revoked") % {"email": self.invitation.email},
            )

            # Log activity
            ActivityLogService.log_activity(
                user=self.request.user,
                action_type="invitation_revoke",
                description=f"Revoked invitation to {self.invitation.email}",
                member_state=self.invitation.member_state,
                content_object=self.invitation,
                changes={"reason": reason},
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

            return redirect("dashboard:invitations:list")

        except ValidationError as e:
            messages.error(self.request, str(e))
            return redirect("dashboard:invitations:detail", pk=self.invitation.pk)


# class InvitationRegistrationView(FormView):
#     """
#     Public registration view for invited users.
#     Uses token from invitation.
#     """

#     form_class = InvitationRegistrationForm
#     template_name = "invitations/registration.html"
#     success_url = reverse_lazy("dashboard:country:overview")

#     def dispatch(self, request, *args, **kwargs):
#         """Validate invitation token"""
#         token = kwargs.get("token")

#         try:
#             self.invitation = Invitation.objects.get_by_token(token)

#             # Mark registration started
#             self.invitation.mark_registration_started()

#         except ValidationError as e:
#             messages.error(request, str(e))
#             return render(request, "invitations/invalid_token.html", {"error_message": str(e)})

#         return super().dispatch(request, *args, **kwargs)

#     def get_form_kwargs(self):
#         """Pass invitation to form"""
#         kwargs = super().get_form_kwargs()
#         kwargs["invitation"] = self.invitation
#         return kwargs

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["invitation"] = self.invitation
#         context["member_state"] = self.invitation.member_state
#         context["role"] = self.invitation.get_role_display()
#         return context

#     def form_valid(self, form):
#         """Create user and IPA profile"""
#         try:
#             with transaction.atomic():
#                 # Create user
#                 user = form.save()
#                 user.accepted_invitation_at = timezone.now()
#                 user.save()

#                 # Create IPA profile
#                 from accounts.models import IPAUser

#                 ipa_user = IPAUser.objects.create(
#                     user=user,
#                     member_state=self.invitation.member_state,
#                     role=self.invitation.role,
#                     is_primary_contact=self.invitation.is_primary_contact,
#                     dashboard_access_granted_at=timezone.now(),
#                 )

#                 # Mark invitation as accepted
#                 self.invitation.accept(user)

#                 # Send welcome email
#                 email_service = get_system_email_service()
#                 email_service.send_welcome_email(user, ipa_user)

#                 # Log activity
#                 ActivityLogService.log_user_create(
#                     user=user,
#                     created_by=self.invitation.invited_by,
#                     ipa_user=ipa_user,
#                     ip_address=self.request.META.get("REMOTE_ADDR"),
#                 )

#                 # Notify inviter
#                 if self.invitation.invited_by:
#                     NotificationService.notify_invitation_accepted(
#                         inviter=self.invitation.invited_by,
#                         invitation=self.invitation,
#                         new_user=user,
#                     )

#                 # Log user in
#                 login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")

#                 messages.success(
#                     self.request,
#                     _("Welcome to IPAWAS! Your account has been created successfully."),
#                 )

#                 return HttpResponseRedirect(self.success_url)

#         except Exception as e:
#             messages.error(self.request, _("Error creating account: %(error)s") % {"error": str(e)})
#             return self.form_invalid(form)


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


class BulkInvitationView(LoginRequiredMixin, InvitationAccessMixin, FormView):
    """Create multiple invitations at once"""

    form_class = BulkInvitationForm
    template_name = "invitations/bulk_invitation.html"
    success_url = reverse_lazy("dashboard:invitations:list")

    def get_form_kwargs(self):
        """Pass user to form"""
        kwargs = super().get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        """Create multiple invitations"""
        user = self.request.user
        emails = form.cleaned_data["emails"]
        role = form.cleaned_data["role"]
        invitation_message = form.cleaned_data.get("invitation_message", "")

        # Get member state
        if user.is_ipa_staff and hasattr(user, "ipa_profile"):
            member_state = user.ipa_profile.member_state
        elif "member_state" in form.cleaned_data and form.cleaned_data["member_state"]:
            member_state = form.cleaned_data["member_state"]
        else:
            member_state = None  # Valid for HQ admin bulk invitations

        created_count = 0
        error_emails = []

        try:
            with transaction.atomic():
                email_service = get_invitation_email_service()

                for email in emails:
                    try:
                        # Create invitation
                        invitation = Invitation.objects.create_invitation(
                            email=email,
                            invited_by=user,
                            member_state=member_state,
                            role=role,
                            user_type="ipawas_admin" if member_state is None else "ipa_staff",
                            invitation_message=invitation_message,
                        )

                        # Send email
                        email_service.send_invitation_email(invitation)
                        created_count += 1

                    except Exception as e:
                        error_emails.append(f"{email} ({str(e)})")

                # Log bulk activity
                ActivityLogService.log_activity(
                    user=user,
                    action_type="bulk_import",
                    description=f"Bulk invited {created_count} users",
                    member_state=member_state,
                    changes={"count": created_count, "errors": error_emails},
                    ip_address=self.request.META.get("REMOTE_ADDR"),
                )

                messages.success(
                    self.request,
                    _("Successfully sent %(count)d invitation(s)") % {"count": created_count},
                )

                if error_emails:
                    messages.warning(
                        self.request,
                        _("Failed to invite: %(emails)s") % {"emails": ", ".join(error_emails)},
                    )

                return HttpResponseRedirect(self.success_url)

        except Exception as e:
            messages.error(
                self.request, _("Error processing bulk invitations: %(error)s") % {"error": str(e)}
            )
            return self.form_invalid(form)
