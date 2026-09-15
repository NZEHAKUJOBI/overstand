"""IPA Leadership Edit View"""

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import UpdateView

from dashboard.forms import LeadershipForm
from dashboard.mixins import CanEditProfileMixin
from media_app.services.cloudinary_service import CloudinaryService
from members.models import IPALeadership


class LeadershipEditView(CanEditProfileMixin, UpdateView):
    model = IPALeadership
    form_class = LeadershipForm
    template_name = "dashboard/members/leadership/form.html"

    def get_object(self):
        member_state = self.request.user.ipa_profile.member_state
        # Get existing or create a blank instance
        obj, _ = IPALeadership.objects.get_or_create(member_state=member_state)
        return obj

    def get_success_url(self):
        return reverse(
            "dashboard:country:leadership",
            kwargs={"member_state_slug": self.request.user.ipa_profile.member_state.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_state"] = self.request.user.ipa_profile.member_state
        return context

    def form_valid(self, form):
        leadership = form.save(commit=False)

        photo_file = self.request.FILES.get("official_photograph")
        if photo_file:
            allowed = getattr(settings, "ALLOWED_IMAGE_TYPES", ["image/jpeg", "image/png", "image/gif", "image/webp"])
            if photo_file.content_type not in allowed:
                messages.error(self.request, "Official photograph: invalid file type. Allowed: JPEG, PNG, GIF, WebP.")
            else:
                folder = f"ipawas/{leadership.member_state.slug}/leadership"
                result = CloudinaryService.upload_file(photo_file, folder, resource_type="image")
                if result["success"]:
                    leadership.official_photograph = result["data"]["secure_url"]
                    messages.success(self.request, "Photo uploaded successfully.")
                else:
                    messages.warning(self.request, f"Photo upload failed: {result.get('error')}")

        leadership.save()
        messages.success(self.request, "Leadership profile updated successfully.")
        return redirect(self.get_success_url())
