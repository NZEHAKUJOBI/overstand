"""
HQ Media Center Dashboard Views
HQ admins can: create press releases directly, review and approve/reject IPA submissions.
"""
import logging
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from dashboard.mixins import IPAWASAdminRequiredMixin
from knowledge_hub.models import MediaCenterSubmission, MediaKitItem, PressRelease
from media_app.models import MediaFile
from members.models import MemberStateIPA

logger = logging.getLogger(__name__)


class HQMediaCenterOverviewView(IPAWASAdminRequiredMixin, TemplateView):
    template_name = "dashboard/hq_admin/media_center/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_prs"] = PressRelease.objects.filter(status="pending_review").select_related("member_state", "created_by").order_by("-submitted_at")[:10]
        context["pending_media"] = MediaCenterSubmission.objects.filter(status="pending").select_related("media_file", "member_state", "submitted_by").order_by("-submitted_at")[:10]
        context["pr_counts"] = {
            "pending": PressRelease.objects.filter(status="pending_review").count(),
            "approved": PressRelease.objects.filter(status="approved").count(),
            "draft": PressRelease.objects.filter(status="draft").count(),
        }
        context["media_counts"] = {
            "pending": MediaCenterSubmission.objects.filter(status="pending").count(),
            "approved": MediaCenterSubmission.objects.filter(status="approved").count(),
        }
        context["total_pending"] = context["pr_counts"]["pending"] + context["media_counts"]["pending"]
        return context


class HQPressReleaseListView(IPAWASAdminRequiredMixin, ListView):
    model = PressRelease
    template_name = "dashboard/hq_admin/media_center/press_release_list.html"
    context_object_name = "press_releases"
    paginate_by = 25

    def get_queryset(self):
        qs = PressRelease.objects.select_related("member_state", "created_by").order_by("-created_at")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        ipa = self.request.GET.get("ipa")
        if ipa:
            qs = qs.filter(member_state__slug=ipa)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(summary__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_counts"] = {
            "all": PressRelease.objects.count(),
            "pending_review": PressRelease.objects.filter(status="pending_review").count(),
            "approved": PressRelease.objects.filter(status="approved").count(),
            "draft": PressRelease.objects.filter(status="draft").count(),
            "rejected": PressRelease.objects.filter(status="rejected").count(),
        }
        context["member_states"] = MemberStateIPA.objects.filter(is_active=True).order_by("country_name")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_ipa"] = self.request.GET.get("ipa", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class HQPressReleaseCreateView(IPAWASAdminRequiredMixin, CreateView):
    model = PressRelease
    template_name = "dashboard/hq_admin/media_center/press_release_form.html"
    fields = ["title", "summary", "content", "release_date", "location", "contact_name", "contact_email", "contact_phone"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = "approved"
        form.instance.approved_by = self.request.user
        form.instance.approved_at = timezone.now()
        form.instance.member_state = None
        response = super().form_valid(form)
        messages.success(self.request, f'Press release "{self.object.title}" published.')
        return response

    def get_success_url(self):
        return reverse("dashboard:hq:media_center:pr_list")


class HQPressReleaseUpdateView(IPAWASAdminRequiredMixin, UpdateView):
    model = PressRelease
    template_name = "dashboard/hq_admin/media_center/press_release_form.html"
    fields = ["title", "summary", "content", "release_date", "location", "contact_name", "contact_email", "contact_phone", "status"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        if form.instance.status == "approved" and not form.instance.approved_by:
            form.instance.approved_by = self.request.user
            form.instance.approved_at = timezone.now()
        response = super().form_valid(form)
        messages.success(self.request, f'Press release "{self.object.title}" updated.')
        return response

    def get_success_url(self):
        return reverse("dashboard:hq:media_center:pr_list")


class HQPressReleaseDeleteView(IPAWASAdminRequiredMixin, DeleteView):
    model = PressRelease
    template_name = "dashboard/hq_admin/media_center/press_release_confirm_delete.html"

    def form_valid(self, form):
        messages.success(self.request, f'Press release "{self.object.title}" deleted.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:hq:media_center:pr_list")


class HQPressReleaseApproveView(IPAWASAdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        pr = get_object_or_404(PressRelease, pk=pk, status="pending_review")
        pr.status = "approved"
        pr.approved_by = request.user
        pr.approved_at = timezone.now()
        pr.save(update_fields=["status", "approved_by", "approved_at", "published"])
        messages.success(request, f'Press release "{pr.title}" approved and published.')
        return redirect(reverse("dashboard:hq:media_center:overview"))


class HQPressReleaseRejectView(IPAWASAdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        pr = get_object_or_404(PressRelease, pk=pk, status="pending_review")
        reason = request.POST.get("rejection_reason", "").strip()
        if not reason:
            messages.error(request, "Please provide a rejection reason.")
            return redirect(reverse("dashboard:hq:media_center:overview"))
        pr.status = "rejected"
        pr.rejection_reason = reason
        pr.save(update_fields=["status", "rejection_reason", "published"])
        messages.warning(request, f'Press release "{pr.title}" rejected.')
        return redirect(reverse("dashboard:hq:media_center:overview"))


class HQMediaSubmissionListView(IPAWASAdminRequiredMixin, ListView):
    model = MediaCenterSubmission
    template_name = "dashboard/hq_admin/media_center/media_submissions.html"
    context_object_name = "submissions"
    paginate_by = 24

    def get_queryset(self):
        qs = MediaCenterSubmission.objects.select_related("media_file", "member_state", "submitted_by").order_by("-submitted_at")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        stype = self.request.GET.get("type")
        if stype:
            qs = qs.filter(submission_type=stype)
        ipa = self.request.GET.get("ipa")
        if ipa:
            qs = qs.filter(member_state__slug=ipa)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subs = MediaCenterSubmission.objects
        context["status_counts"] = {
            "all": subs.count(),
            "pending": subs.filter(status="pending").count(),
            "approved": subs.filter(status="approved").count(),
            "rejected": subs.filter(status="rejected").count(),
        }
        context["member_states"] = MemberStateIPA.objects.filter(is_active=True).order_by("country_name")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_type"] = self.request.GET.get("type", "")
        context["current_ipa"] = self.request.GET.get("ipa", "")
        return context


class HQMediaApproveView(IPAWASAdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        sub = get_object_or_404(MediaCenterSubmission, pk=pk, status="pending")
        sub.status = "approved"
        sub.approved_by = request.user
        sub.approved_at = timezone.now()
        sub.save(update_fields=["status", "approved_by", "approved_at"])
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        messages.success(request, f'Media "{sub.media_file.name}" approved and now live.')
        return redirect(reverse("dashboard:hq:media_center:media_list"))


class HQMediaRejectView(IPAWASAdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        sub = get_object_or_404(MediaCenterSubmission, pk=pk, status="pending")
        reason = request.POST.get("rejection_reason", "").strip()
        sub.status = "rejected"
        sub.rejection_reason = reason
        sub.save(update_fields=["status", "rejection_reason"])
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        messages.warning(request, f'Media "{sub.media_file.name}" rejected.')
        return redirect(reverse("dashboard:hq:media_center:media_list"))


class HQMediaKitListView(IPAWASAdminRequiredMixin, ListView):
    model = MediaKitItem
    template_name = "dashboard/hq_admin/media_center/media_kit.html"
    context_object_name = "items"
    paginate_by = 20

    def get_queryset(self):
        return MediaKitItem.objects.select_related("primary_file").order_by("display_order", "name")
