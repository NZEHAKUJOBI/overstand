"""
IPA Media Center Dashboard Views
IPA staff can: create/edit/delete draft press releases, submit for HQ review,
nominate uploaded media files for the public gallery.
"""
import logging
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from dashboard.mixins import IPAStaffRequiredMixin, MemberStateAccessMixin
from knowledge_hub.models import MediaCenterSubmission, PressRelease
from media_app.models import MediaFile

logger = logging.getLogger(__name__)


class IPAMediaCenterOverviewView(IPAStaffRequiredMixin, MemberStateAccessMixin, TemplateView):
    template_name = "dashboard/members/media_center/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ms = self.request.member_state
        prs = PressRelease.objects.filter(member_state=ms)
        subs = MediaCenterSubmission.objects.filter(member_state=ms)
        context["pr_draft_count"] = prs.filter(status="draft").count()
        context["pr_pending_count"] = prs.filter(status="pending_review").count()
        context["pr_approved_count"] = prs.filter(status="approved").count()
        context["pr_rejected_count"] = prs.filter(status="rejected").count()
        context["media_pending_count"] = subs.filter(status="pending").count()
        context["media_approved_count"] = subs.filter(status="approved").count()
        context["media_rejected_count"] = subs.filter(status="rejected").count()
        context["recent_prs"] = prs.order_by("-created_at")[:5]
        context["recent_submissions"] = subs.order_by("-submitted_at")[:5]
        return context


class IPAPressReleaseListView(IPAStaffRequiredMixin, MemberStateAccessMixin, ListView):
    model = PressRelease
    template_name = "dashboard/members/media_center/press_release_list.html"
    context_object_name = "press_releases"
    paginate_by = 20

    def get_queryset(self):
        qs = PressRelease.objects.filter(member_state=self.request.member_state).order_by("-created_at")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ms = self.request.member_state
        prs = PressRelease.objects.filter(member_state=ms)
        context["status_counts"] = {
            "all": prs.count(),
            "draft": prs.filter(status="draft").count(),
            "pending_review": prs.filter(status="pending_review").count(),
            "approved": prs.filter(status="approved").count(),
            "rejected": prs.filter(status="rejected").count(),
        }
        context["current_status"] = self.request.GET.get("status", "")
        return context


class IPAPressReleaseCreateView(IPAStaffRequiredMixin, MemberStateAccessMixin, CreateView):
    model = PressRelease
    template_name = "dashboard/members/media_center/press_release_form.html"
    fields = ["title", "summary", "content", "release_date", "location", "contact_name", "contact_email", "contact_phone"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        context["available_media"] = MediaFile.objects.filter(
            member_state=self.request.member_state, file_type="document", is_deleted=False
        ).order_by("-uploaded_at")[:30]
        return context

    def form_valid(self, form):
        form.instance.member_state = self.request.member_state
        form.instance.created_by = self.request.user
        form.instance.status = "draft"
        pdf_id = self.request.POST.get("pdf_file_id")
        if pdf_id:
            try:
                form.instance.pdf_file = MediaFile.objects.get(pk=pdf_id, member_state=self.request.member_state)
            except MediaFile.DoesNotExist:
                pass
        response = super().form_valid(form)
        action = self.request.POST.get("action")
        if action == "submit":
            self.object.status = "pending_review"
            self.object.submitted_at = timezone.now()
            self.object.save(update_fields=["status", "submitted_at"])
            messages.success(self.request, f'Press release "{self.object.title}" submitted for HQ review.')
        else:
            messages.success(self.request, f'Press release "{self.object.title}" saved as draft.')
        return response

    def get_success_url(self):
        return reverse("dashboard:country:media_center:pr_list", kwargs={"member_state_slug": self.request.member_state.slug})


class IPAPressReleaseUpdateView(IPAStaffRequiredMixin, MemberStateAccessMixin, UpdateView):
    model = PressRelease
    template_name = "dashboard/members/media_center/press_release_form.html"
    fields = ["title", "summary", "content", "release_date", "location", "contact_name", "contact_email", "contact_phone"]

    def get_queryset(self):
        return PressRelease.objects.filter(member_state=self.request.member_state, status__in=["draft", "rejected"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        context["available_media"] = MediaFile.objects.filter(
            member_state=self.request.member_state, file_type="document", is_deleted=False
        ).order_by("-uploaded_at")[:30]
        return context

    def form_valid(self, form):
        pdf_id = self.request.POST.get("pdf_file_id")
        if pdf_id:
            try:
                form.instance.pdf_file = MediaFile.objects.get(pk=pdf_id, member_state=self.request.member_state)
            except MediaFile.DoesNotExist:
                pass
        response = super().form_valid(form)
        action = self.request.POST.get("action")
        if action == "submit":
            self.object.status = "pending_review"
            self.object.submitted_at = timezone.now()
            self.object.rejection_reason = ""
            self.object.save(update_fields=["status", "submitted_at", "rejection_reason"])
            messages.success(self.request, f'Press release "{self.object.title}" submitted for HQ review.')
        else:
            messages.success(self.request, f'Press release "{self.object.title}" updated.')
        return response

    def get_success_url(self):
        return reverse("dashboard:country:media_center:pr_list", kwargs={"member_state_slug": self.request.member_state.slug})


class IPAPressReleaseDeleteView(IPAStaffRequiredMixin, MemberStateAccessMixin, DeleteView):
    model = PressRelease
    template_name = "dashboard/members/media_center/press_release_confirm_delete.html"

    def get_queryset(self):
        return PressRelease.objects.filter(member_state=self.request.member_state, status__in=["draft", "rejected"])

    def form_valid(self, form):
        title = self.object.title
        messages.success(self.request, f'Press release "{title}" deleted.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:country:media_center:pr_list", kwargs={"member_state_slug": self.request.member_state.slug})


class IPAMediaSubmissionListView(IPAStaffRequiredMixin, MemberStateAccessMixin, ListView):
    model = MediaCenterSubmission
    template_name = "dashboard/members/media_center/media_submissions.html"
    context_object_name = "submissions"
    paginate_by = 20

    def get_queryset(self):
        qs = MediaCenterSubmission.objects.filter(member_state=self.request.member_state).select_related("media_file", "approved_by").order_by("-submitted_at")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        stype = self.request.GET.get("type")
        if stype:
            qs = qs.filter(submission_type=stype)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ms = self.request.member_state
        subs = MediaCenterSubmission.objects.filter(member_state=ms)
        context["status_counts"] = {
            "all": subs.count(),
            "pending": subs.filter(status="pending").count(),
            "approved": subs.filter(status="approved").count(),
            "rejected": subs.filter(status="rejected").count(),
        }
        submitted_file_ids = MediaCenterSubmission.objects.filter(member_state=ms).values_list("media_file_id", flat=True)
        context["available_photos"] = MediaFile.objects.filter(
            member_state=ms, file_type="image", is_deleted=False
        ).exclude(pk__in=submitted_file_ids).order_by("-uploaded_at")[:50]
        context["available_videos"] = MediaFile.objects.filter(
            member_state=ms, file_type="video", is_deleted=False
        ).exclude(pk__in=submitted_file_ids).order_by("-uploaded_at")[:20]
        context["current_status"] = self.request.GET.get("status", "")
        context["current_type"] = self.request.GET.get("type", "")
        return context


class IPAMediaSubmitView(IPAStaffRequiredMixin, MemberStateAccessMixin, View):
    """Submit one or more media files for HQ review."""

    def post(self, request, *args, **kwargs):
        ms = request.member_state
        file_ids = request.POST.getlist("file_ids[]")
        captions = request.POST.getlist("captions[]")
        created = 0
        for i, file_id in enumerate(file_ids):
            try:
                mf = MediaFile.objects.get(pk=file_id, member_state=ms, is_deleted=False)
                if MediaCenterSubmission.objects.filter(media_file=mf).exists():
                    continue
                caption = captions[i] if i < len(captions) else ""
                MediaCenterSubmission.objects.create(
                    media_file=mf,
                    member_state=ms,
                    submission_type="photo" if mf.file_type == "image" else "video",
                    caption=caption,
                    submitted_by=request.user,
                )
                created += 1
            except MediaFile.DoesNotExist:
                continue
        if created:
            messages.success(request, f"{created} file(s) submitted for HQ review.")
        else:
            messages.warning(request, "No new files submitted (already submitted or not found).")
        return redirect(reverse("dashboard:country:media_center:media_list", kwargs={"member_state_slug": ms.slug}))


class IPAMediaWithdrawView(IPAStaffRequiredMixin, MemberStateAccessMixin, View):
    """Withdraw a pending media submission."""

    def post(self, request, pk, *args, **kwargs):
        ms = request.member_state
        sub = get_object_or_404(MediaCenterSubmission, pk=pk, member_state=ms, status="pending")
        sub.delete()
        messages.success(request, "Submission withdrawn.")
        return redirect(reverse("dashboard:country:media_center:media_list", kwargs={"member_state_slug": ms.slug}))
