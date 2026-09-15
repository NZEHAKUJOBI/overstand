from django import forms

from .models import Feedback

_FC = "form-control"
_FS = "form-select"


class FeedbackSubmitForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["category", "title", "body"]
        widgets = {
            "category": forms.Select(attrs={"class": _FS}),
            "title": forms.TextInput(attrs={"class": _FC, "placeholder": "Brief summary of your idea or observation"}),
            "body": forms.Textarea(attrs={"class": _FC, "rows": 6, "placeholder": "Describe in detail — what you experienced, what you'd like to see, or what you're suggesting"}),
        }
        labels = {
            "category": "Type",
            "title": "Title",
            "body": "Details",
        }


class FeedbackResponseForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["status", "admin_response"]
        widgets = {
            "status": forms.Select(attrs={"class": _FS}),
            "admin_response": forms.Textarea(attrs={"class": _FC, "rows": 5, "placeholder": "Write a response to the submitter (optional)"}),
        }
        labels = {
            "status": "Update Status",
            "admin_response": "Response to Submitter",
        }
