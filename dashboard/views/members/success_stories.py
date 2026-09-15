"""Success Stories CRUD Views"""

from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dashboard.forms import SuccessStoryForm
from dashboard.mixins import CanEditProfileMixin, IPAStaffRequiredMixin
from media_app.services.cloudinary_service import CloudinaryService
from members.models import SuccessStory


class SuccessStoryListView(IPAStaffRequiredMixin, ListView):
    model = SuccessStory
    template_name = "dashboard/members/success_stories/list.html"
    context_object_name = "stories"

    def get_queryset(self):
        return SuccessStory.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        ).select_related("sector").order_by("display_order", "-year")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context


class SuccessStoryCreateView(CanEditProfileMixin, CreateView):
    model = SuccessStory
    form_class = SuccessStoryForm
    template_name = "dashboard/members/success_stories/form.html"

    def get_success_url(self):
        return reverse(
            "dashboard:country:success_stories",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        story = form.save(commit=False)
        story.member_state = self.request.user.ipa_profile.member_state

        # Handle image upload
        image_file = self.request.FILES.get("image")
        if image_file:
            allowed = getattr(settings, "ALLOWED_IMAGE_TYPES", ["image/jpeg", "image/png", "image/gif", "image/webp"])
            if image_file.content_type not in allowed:
                messages.error(self.request, "Image: invalid file type. Allowed: JPEG, PNG, GIF, WebP.")
            else:
                folder = f"ipawas/{story.member_state.slug}/success-stories"
                result = CloudinaryService.upload_file(image_file, folder, resource_type="image")
                if result["success"]:
                    story.image = result["data"]["secure_url"]
                else:
                    messages.warning(self.request, f"Image upload failed: {result.get('error')}")

        story.save()
        messages.success(self.request, "Success story created successfully.")
        return self._redirect()

    def _redirect(self):
        from django.shortcuts import redirect
        return redirect(self.get_success_url())


class SuccessStoryEditView(CanEditProfileMixin, UpdateView):
    model = SuccessStory
    form_class = SuccessStoryForm
    template_name = "dashboard/members/success_stories/form.html"

    def get_queryset(self):
        return SuccessStory.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        )

    def get_success_url(self):
        return reverse(
            "dashboard:country:success_stories",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        story = form.save(commit=False)

        image_file = self.request.FILES.get("image")
        if image_file:
            allowed = getattr(settings, "ALLOWED_IMAGE_TYPES", ["image/jpeg", "image/png", "image/gif", "image/webp"])
            if image_file.content_type not in allowed:
                messages.error(self.request, "Image: invalid file type. Allowed: JPEG, PNG, GIF, WebP.")
            else:
                folder = f"ipawas/{story.member_state.slug}/success-stories"
                result = CloudinaryService.upload_file(image_file, folder, resource_type="image")
                if result["success"]:
                    story.image = result["data"]["secure_url"]
                else:
                    messages.warning(self.request, f"Image upload failed: {result.get('error')}")

        story.save()
        messages.success(self.request, "Success story updated successfully.")
        from django.shortcuts import redirect
        return redirect(self.get_success_url())


class SuccessStoryDeleteView(CanEditProfileMixin, DeleteView):
    model = SuccessStory
    template_name = "dashboard/members/success_stories/confirm_delete.html"

    def get_queryset(self):
        return SuccessStory.objects.filter(
            member_state=self.request.user.ipa_profile.member_state
        )

    def get_success_url(self):
        return reverse(
            "dashboard:country:success_stories",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        messages.success(self.request, "Success story deleted.")
        return super().form_valid(form)
