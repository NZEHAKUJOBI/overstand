"""
Investor Inquiry Views for Dashboard
apps/dashboard/views/inquiries.py

Handles inquiry management for both HQ and Member State admins.
Pattern similar to invitations feature.
"""

from django.contrib import messages
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from core.email.services import get_inquiry_email_service
from dashboard.mixins import CanViewInquiriesMixin
from members.models import InvestorInquiry


class InquiryListView(CanViewInquiriesMixin, ListView):
    """
    List investor inquiries (filtered by member state for IPA staff).

    HQ Admin: Sees all inquiries
    IPA Staff: Sees only their member state's inquiries
    """

    model = InvestorInquiry
    template_name = "dashboard/inquiries/list.html"
    context_object_name = "inquiries"
    paginate_by = 25

    def get_queryset(self):
        queryset = InvestorInquiry.objects.select_related(
            "member_state", "sector_of_interest", "assigned_to"
        )

        # Filter by member state for IPA staff
        if self.request.user.user_type == "ipa_staff":
            queryset = queryset.filter(member_state=self.request.user.ipa_profile.member_state)

        # Handle status filter
        status_filter = self.request.GET.get("status")
        if status_filter and status_filter in ["new", "in_progress", "responded", "closed"]:
            queryset = queryset.filter(status=status_filter)

        # Handle search
        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(reference_number__icontains=search_query)
                | Q(full_name__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(company_name__icontains=search_query)
                | Q(subject__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add member state for IPA staff
        if self.request.user.user_type == "ipa_staff":
            member_state = self.request.user.ipa_profile.member_state
            context["member_state"] = member_state

        # Set base template based on user type
        if self.request.user.user_type == "ipa_staff":
            context["base_template"] = "dashboard/members/base.html"
        else:
            context["base_template"] = "dashboard/hq_admin/base.html"

        # Add status counts via a single aggregated query (avoids N+1 with 5 separate .count() calls)
        all_inquiries = self.get_queryset()
        counts = all_inquiries.aggregate(
            total=Count("id"),
            new=Count(Case(When(status="new", then=Value(1)), output_field=IntegerField())),
            in_progress=Count(Case(When(status="in_progress", then=Value(1)), output_field=IntegerField())),
            responded=Count(Case(When(status="responded", then=Value(1)), output_field=IntegerField())),
            closed=Count(Case(When(status="closed", then=Value(1)), output_field=IntegerField())),
        )
        context["status_counts"] = {
            "all": counts["total"],
            "new": counts["new"],
            "in_progress": counts["in_progress"],
            "responded": counts["responded"],
            "closed": counts["closed"],
        }

        # Add current filter
        context["current_status"] = self.request.GET.get("status", "all")
        context["search_query"] = self.request.GET.get("q", "")

        return context


class InquiryDetailView(CanViewInquiriesMixin, DetailView):
    """
    View investor inquiry details.

    Shows full inquiry information and allows status updates.
    """

    model = InvestorInquiry
    template_name = "dashboard/inquiries/detail.html"
    context_object_name = "inquiry"

    def get_queryset(self):
        queryset = InvestorInquiry.objects.select_related(
            "member_state", "sector_of_interest", "assigned_to"
        )

        # Filter by member state for IPA staff
        if self.request.user.user_type == "ipa_staff":
            queryset = queryset.filter(member_state=self.request.user.ipa_profile.member_state)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add member state for IPA staff
        if self.request.user.user_type == "ipa_staff":
            member_state = self.request.user.ipa_profile.member_state
            context["member_state"] = member_state

        # Set base template based on user type
        if self.request.user.user_type == "ipa_staff":
            context["base_template"] = "dashboard/members/base.html"
        else:
            context["base_template"] = "dashboard/hq_admin/base.html"

        return context


class InquiryUpdateStatusView(CanViewInquiriesMixin, View):
    """
    Update inquiry status.

    Allows marking inquiries as: new, in_progress, responded, closed
    """

    def post(self, request, pk):
        inquiry = get_object_or_404(InvestorInquiry, pk=pk)

        # Check permission for IPA staff
        if request.user.user_type == "ipa_staff":
            if inquiry.member_state != request.user.ipa_profile.member_state:
                messages.error(request, "You don't have permission to update this inquiry.")
                member_state_slug = request.user.ipa_profile.member_state.slug
                return redirect("dashboard:country:inquiries:list", member_state_slug=member_state_slug)

        new_status = request.POST.get("status")

        if new_status in ["new", "in_progress", "responded", "closed"]:
            old_status = inquiry.get_status_display()
            inquiry.status = new_status
            inquiry.save()

            messages.success(
                request,
                f"Inquiry {inquiry.reference_number} status updated from {old_status} to {inquiry.get_status_display()}",
            )
        else:
            messages.error(request, "Invalid status")

        return redirect(inquiry.get_absolute_url())


class InquiryAssignView(CanViewInquiriesMixin, View):
    """
    Assign inquiry to a team member.
    """

    def post(self, request, pk, member_state_slug=None):

        inquiry = get_object_or_404(InvestorInquiry, pk=pk)

        # Check permission for IPA staff
        if request.user.user_type == "ipa_staff":
            if inquiry.member_state != request.user.ipa_profile.member_state:
                messages.error(request, "You don't have permission to assign this inquiry.")
                slug = request.user.ipa_profile.member_state.slug
                return redirect("dashboard:country:inquiries:list", member_state_slug=slug)

        # Assign to current user or specific user (implement user selection as needed)
        inquiry.assigned_to = request.user
        inquiry.status = "in_progress"
        inquiry.save()

        messages.success(
            request,
            f"Inquiry {inquiry.reference_number} assigned to {request.user.get_full_name()}",
        )

        return redirect(inquiry.get_absolute_url())


class InquiryAddNoteView(CanViewInquiriesMixin, View):
    """
    Add internal note to inquiry.
    """

    def post(self, request, pk, member_state_slug=None):
        inquiry = get_object_or_404(InvestorInquiry, pk=pk)

        # Check permission for IPA staff
        if request.user.user_type == "ipa_staff":
            if inquiry.member_state != request.user.ipa_profile.member_state:
                messages.error(request, "You don't have permission to add notes to this inquiry.")
                slug = request.user.ipa_profile.member_state.slug
                return redirect("dashboard:country:inquiries:list", member_state_slug=slug)

        note = request.POST.get("note")

        if note:
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            user_name = request.user.get_full_name()
            new_note = f"[{timestamp}] {user_name}:\n{note}\n\n"

            inquiry.internal_notes = new_note + (inquiry.internal_notes or "")
            inquiry.save()

            messages.success(request, "Note added successfully")
        else:
            messages.error(request, "Note cannot be empty")

        return redirect(inquiry.get_absolute_url())


class InquiryReplyView(CanViewInquiriesMixin, View):
    """
    Send an email reply to an investor inquiry.

    Handles both HQ admin and IPA staff (country) contexts.
    On success: sends email, marks inquiry 'responded', prepends internal note.
    On failure: adds Django error message and redirects back to detail page.
    """

    def _redirect_to_detail(self, request, inquiry, member_state_slug=None):
        """Redirect back to the inquiry detail page."""
        return redirect(inquiry.get_absolute_url())

    def post(self, request, pk, member_state_slug=None):
        inquiry = get_object_or_404(InvestorInquiry, pk=pk)

        # Cross-state guard for IPA staff
        if request.user.user_type == "ipa_staff":
            if inquiry.member_state != request.user.ipa_profile.member_state:
                slug = request.user.ipa_profile.member_state.slug
                return redirect("dashboard:country:inquiries:list", member_state_slug=slug)

        reply_message = request.POST.get("reply_message", "").strip()
        if not reply_message:
            messages.error(request, "Reply message cannot be empty.")
            return self._redirect_to_detail(request, inquiry, member_state_slug)

        # Send email via service
        email_service = get_inquiry_email_service()
        sent = email_service.send_inquiry_response(
            inquiry=inquiry,
            reply_message=reply_message,
            replied_by=request.user,
        )

        if not sent:
            messages.error(request, "Failed to send reply email. Please try again.")
            return self._redirect_to_detail(request, inquiry, member_state_slug)

        # Update status and prepend internal note
        inquiry.status = "responded"
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        sender = request.user.get_full_name()
        note_entry = f"[{timestamp}] REPLY sent by {sender}:\n{reply_message}\n\n"
        inquiry.internal_notes = note_entry + (inquiry.internal_notes or "")
        inquiry.save()

        # Log activity
        try:
            from dashboard.models import IPADashboardActivity
            IPADashboardActivity.objects.create(
                user=request.user,
                action_type="inquiry_respond",
                description=f"Replied to inquiry {inquiry.reference_number} from {inquiry.full_name}",
                member_state=inquiry.member_state,
            )
        except Exception:
            pass  # Activity logging is non-critical

        messages.success(request, f"Reply sent to {inquiry.email}.")
        return self._redirect_to_detail(request, inquiry, member_state_slug)
