from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin

from dashboard.mixins import IPAStaffRequiredMixin, IPAWASAdminRequiredMixin
from .forms import FeedbackResponseForm, FeedbackSubmitForm
from .models import Feedback


# ── IPA Staff views ──────────────────────────────────────────────────────────

class FeedbackListView(IPAStaffRequiredMixin, ListView):
    model = Feedback
    template_name = "dashboard/members/feedback/list.html"
    context_object_name = "submissions"

    def get_queryset(self):
        return Feedback.objects.filter(user=self.request.user).select_related("member_state")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context


class FeedbackSubmitView(IPAStaffRequiredMixin, CreateView):
    model = Feedback
    form_class = FeedbackSubmitForm
    template_name = "dashboard/members/feedback/submit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.user = self.request.user
        feedback.member_state = self.request.user.ipa_profile.member_state
        feedback.save()
        messages.success(self.request, "Your feedback has been submitted. Thank you!")
        return redirect(
            reverse("dashboard:country:feedback_list",
                    kwargs={"member_state_slug": feedback.member_state.slug})
        )


class FeedbackDetailView(IPAStaffRequiredMixin, DetailView):
    model = Feedback
    template_name = "dashboard/members/feedback/detail.html"
    context_object_name = "submission"

    def get_queryset(self):
        return Feedback.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context


# ── HQ Admin views ───────────────────────────────────────────────────────────

class HQFeedbackListView(IPAWASAdminRequiredMixin, ListView):
    model = Feedback
    template_name = "dashboard/hq_admin/feedback/list.html"
    context_object_name = "submissions"
    paginate_by = 25

    def get_queryset(self):
        qs = Feedback.objects.select_related("user", "member_state").order_by("-created_at")
        category = self.request.GET.get("category")
        status = self.request.GET.get("status")
        country = self.request.GET.get("country")
        if category:
            qs = qs.filter(category=category)
        if status:
            qs = qs.filter(status=status)
        if country:
            qs = qs.filter(member_state__slug=country)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from members.models import MemberStateIPA
        context["member_states"] = MemberStateIPA.objects.order_by("country_name")
        context["category_choices"] = Feedback.CATEGORY_CHOICES
        context["status_choices"] = Feedback.STATUS_CHOICES
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_country"] = self.request.GET.get("country", "")
        context["unreviewed_count"] = Feedback.objects.filter(status="new").count()
        return context


class HQFeedbackDetailView(IPAWASAdminRequiredMixin, View):
    template_name = "dashboard/hq_admin/feedback/detail.html"

    def get_object(self):
        return get_object_or_404(Feedback.objects.select_related("user", "member_state", "responded_by"), pk=self.kwargs["pk"])

    def get(self, request, pk):
        from django.shortcuts import render
        submission = self.get_object()
        form = FeedbackResponseForm(instance=submission)
        return render(request, self.template_name, {"submission": submission, "form": form})

    def post(self, request, pk):
        submission = self.get_object()
        form = FeedbackResponseForm(request.POST, instance=submission)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.admin_response and not submission.responded_at:
                obj.responded_by = request.user
                obj.responded_at = timezone.now()
            obj.save()
            messages.success(request, "Response saved.")
            return redirect("dashboard:hq:feedback_detail", pk=pk)
        from django.shortcuts import render
        return render(request, self.template_name, {"submission": submission, "form": form})
