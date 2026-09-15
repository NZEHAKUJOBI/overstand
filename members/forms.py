"""
Forms for IPAWAS Members App

App Name: members (not member_states)
"""

import re

from django import forms

from members.models import InvestorInquiry, MemberStateIPA

# ---------------------------------------------------------------------------
# Spam detection patterns (Option 3 — server-side content filter)
# Ordered from most common to least common for short-circuit efficiency.
# ---------------------------------------------------------------------------
_SPAM_PATTERNS = [
    re.compile(r"https?://", re.IGNORECASE),                  # URLs in body
    re.compile(r"www\.[a-z0-9\-]+\.[a-z]{2,}", re.IGNORECASE),  # bare domains
    re.compile(r"\b(click\s+here|buy\s+now|free\s+offer|limited\s+time)\b", re.IGNORECASE),
    re.compile(r"\b(casino|gambling|poker|slots)\b", re.IGNORECASE),
    re.compile(r"\b(crypto|bitcoin|ethereum|forex|trading\s+signal)\b", re.IGNORECASE),
    re.compile(r"\b(seo\s+service|backlink|rank\s+#?1|search\s+engine\s+optim)\b", re.IGNORECASE),
    re.compile(r"\b(earn\s+\$|make\s+money|passive\s+income|work\s+from\s+home)\b", re.IGNORECASE),
    re.compile(r"\b(whatsapp|telegram)\s*[:\-]?\s*\+?\d{7,}", re.IGNORECASE),  # messenger spam
    re.compile(r"[!]{3,}"),                                    # three or more exclamation marks
]


class InvestorInquiryForm(forms.ModelForm):
    """
    Investor inquiry form for IPA contact.
    Validates and cleans input before submission.

    Bot protection layers:
      1. Honeypot — hidden field that humans never fill; bots always do.
      2. Spam content filter — rejects messages matching known spam patterns.
    Rate limiting (layer 3) is applied at the view level via django-ratelimit.
    """

    # --- Option 1: Honeypot field -------------------------------------------
    # Rendered as a visually-hidden input.  Any non-empty value means a bot
    # filled it in; the submission is silently rejected.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
        label="",
    )

    member_state = forms.ModelChoiceField(
        queryset=MemberStateIPA.objects.filter(is_active=True),
        required=False,
        empty_label="General IPAWAS Inquiry (not country-specific)",
        widget=forms.Select(attrs={"class": "form-control form-select"}),
    )

    class Meta:
        model = InvestorInquiry
        fields = [
            "inquiry_type",
            "member_state",
            "full_name",
            "email",
            "phone",
            "company_name",
            "company_country",
            "sector_of_interest",
            "estimated_investment",
            "subject",
            "message",
        ]
        widgets = {
            "inquiry_type": forms.Select(
                attrs={"class": "form-control form-select", "required": True}
            ),
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Your full name", "required": True}
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "your.email@example.com",
                    "required": True,
                }
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+1 234 567 8900 (optional)"}
            ),
            "company_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Company name (optional)"}
            ),
            "company_country": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Country of origin (optional)"}
            ),
            "sector_of_interest": forms.Select(attrs={"class": "form-control form-select"}),
            "estimated_investment": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., $1M - $5M (optional)"}
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Brief subject line",
                    "required": True,
                    "maxlength": 200,
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Please provide details about your inquiry...",
                    "rows": 6,
                    "required": True,
                }
            ),
        }
        labels = {
            "inquiry_type": "Type of Inquiry",
            "member_state": "Country of Interest",
            "full_name": "Full Name",
            "email": "Email Address",
            "phone": "Phone Number",
            "company_name": "Company Name",
            "company_country": "Company Country",
            "sector_of_interest": "Sector of Interest",
            "estimated_investment": "Estimated Investment",
            "subject": "Subject",
            "message": "Your Message",
        }

    # --- Option 1: Honeypot clean -------------------------------------------
    def clean_website(self):
        """Reject the submission silently if the honeypot field was filled."""
        value = self.cleaned_data.get("website", "")
        if value:
            # Raise a non-specific error so bots get no useful feedback.
            raise forms.ValidationError("Invalid submission.")
        return value

    # --- Option 3: Spam content filter --------------------------------------
    def clean_message(self):
        """Validate message length and reject spam content."""
        message = self.cleaned_data.get("message", "")
        if len(message) < 50:
            raise forms.ValidationError(
                "Please provide a more detailed message (minimum 50 characters)."
            )
        for pattern in _SPAM_PATTERNS:
            if pattern.search(message):
                raise forms.ValidationError(
                    "Your message was flagged as spam. "
                    "Please remove any links, promotional content, or special characters."
                )
        return message

    def clean_subject(self):
        """Reject spam content in the subject line."""
        subject = self.cleaned_data.get("subject", "")
        for pattern in _SPAM_PATTERNS:
            if pattern.search(subject):
                raise forms.ValidationError(
                    "Your subject line was flagged as spam. Please use a plain subject."
                )
        return subject

    def clean_email(self):
        """Validate and normalize email."""
        email = self.cleaned_data.get("email")
        if email:
            return email.lower().strip()
        return email


class MemberStateFilterForm(forms.Form):
    """
    Form for filtering member states on hub page.
    """

    LANGUAGE_CHOICES = [
        ("", "All Languages"),
        ("english", "English"),
        ("french", "French"),
        ("portuguese", "Portuguese"),
    ]

    REGION_CHOICES = [
        ("", "All Regions"),
        ("west_coast", "West Coast"),
        ("sahel", "Sahel"),
        ("gulf_of_guinea", "Gulf of Guinea"),
    ]

    GDP_CHOICES = [
        ("", "All GDP Sizes"),
        ("large", "Large (>$50B)"),
        ("medium", "Medium ($20-50B)"),
        ("small", "Small (<$20B)"),
    ]

    POPULATION_CHOICES = [
        ("", "All Population Sizes"),
        ("large", "Large (>50M)"),
        ("medium", "Medium (10-50M)"),
        ("small", "Small (<10M)"),
    ]

    SORT_CHOICES = [
        ("country_name", "Country Name (A-Z)"),
        ("-country_name", "Country Name (Z-A)"),
        ("-population", "Population (Largest First)"),
        ("population", "Population (Smallest First)"),
        ("-gdp", "GDP (Largest First)"),
        ("gdp", "GDP (Smallest First)"),
        ("display_order", "Display Order"),
    ]

    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control form-select", "id": "filter-language"}),
    )

    region = forms.ChoiceField(
        choices=REGION_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control form-select", "id": "filter-region"}),
    )

    gdp_range = forms.ChoiceField(
        choices=GDP_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control form-select", "id": "filter-gdp"}),
    )

    population_range = forms.ChoiceField(
        choices=POPULATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control form-select", "id": "filter-population"}),
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search by country name or IPA...",
                "id": "filter-search",
            }
        ),
    )

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial="country_name",
        widget=forms.Select(attrs={"class": "form-control form-select", "id": "sort-select"}),
    )


class CountryComparisonForm(forms.Form):
    """
    Form for selecting countries to compare.
    """

    countries = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="Select 2-4 countries to compare",
    )

    def __init__(self, *args, **kwargs):
        """Initialize with active member states"""
        super().__init__(*args, **kwargs)

        from members.models import MemberStateIPA

        member_states = MemberStateIPA.objects.filter(is_active=True).order_by("country_name")

        self.fields["countries"].choices = [
            (state.slug, f"{state.flag_emoji} {state.country_name}") for state in member_states
        ]

    def clean_countries(self):
        """Validate country selection"""
        countries = self.cleaned_data.get("countries")

        if len(countries) < 2:
            raise forms.ValidationError("Please select at least 2 countries to compare.")

        if len(countries) > 4:
            raise forms.ValidationError("You can compare maximum 4 countries at once.")

        return countries
