"""
Forms for Investment Opportunities and Investor Services
CORRECTED to work with existing InvestorInquiry model structure

Place this in: opportunities/forms.py or investor_services/forms.py
"""

from django import forms

from core.models import Sector
from members.models import InvestorInquiry, MemberStateIPA


class InvestorInquiryForm(forms.ModelForm):
    """
    Form for investor inquiries - works with existing InvestorInquiry model.
    Used in Express Interest modal and other inquiry forms.
    """

    # Additional fields not in model but useful for UI
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Your first name"}),
    )

    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Your last name"}),
    )

    class Meta:
        model = InvestorInquiry
        fields = [
            "member_state",
            "inquiry_type",
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
            "member_state": forms.Select(attrs={"class": "form-select", "required": True}),
            "inquiry_type": forms.Select(attrs={"class": "form-select", "required": True}),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "your.email@example.com",
                    "required": True,
                }
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+1 234 567 8900"}
            ),
            "company_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Your company name"}
            ),
            "company_country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Country where your company is based",
                }
            ),
            "sector_of_interest": forms.Select(attrs={"class": "form-select"}),
            "estimated_investment": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., $1M - $5M, Under $500K"}
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Subject of your inquiry",
                    "required": True,
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Please describe your inquiry in detail...",
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set querysets for foreign keys
        self.fields["member_state"].queryset = MemberStateIPA.objects.filter(
            is_active=True
        ).order_by("country_name")

        self.fields["sector_of_interest"].queryset = Sector.objects.filter(is_active=True).order_by(
            "name"
        )

        self.fields["sector_of_interest"].required = False

    def save(self, commit=True):
        inquiry = super().save(commit=False)

        # Combine first_name and last_name into full_name
        first_name = self.cleaned_data.get("first_name", "")
        last_name = self.cleaned_data.get("last_name", "")
        inquiry.full_name = f"{first_name} {last_name}".strip()

        if commit:
            inquiry.save()

        return inquiry


class AdvisoryRequestForm(forms.Form):
    """
    Form for investment advisory service requests.
    Creates InvestorInquiry with inquiry_type='other' or 'general'.
    """

    # Personal Information
    first_name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    last_name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "required": True})
    )

    phone = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    country = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    # Company Information
    company_name = forms.CharField(
        max_length=200, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    company_website = forms.URLField(
        required=False, widget=forms.URLInput(attrs={"class": "form-control"})
    )

    role = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "e.g., CEO, Investment Manager"}
        ),
    )

    # Investment Details
    investment_capacity = forms.ChoiceField(
        choices=[
            ("", "Select range..."),
            ("under_1m", "Under $1M"),
            ("1m_5m", "$1M - $5M"),
            ("5m_10m", "$5M - $10M"),
            ("10m_25m", "$10M - $25M"),
            ("over_25m", "Over $25M"),
        ],
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
    )

    decision_timeline = forms.ChoiceField(
        choices=[
            ("", "Select timeline..."),
            ("under_3m", "Under 3 months"),
            ("3_6m", "3-6 months"),
            ("6_12m", "6-12 months"),
            ("over_12m", "Over 12 months"),
        ],
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
    )

    # Advisory specifics
    advisory_type = forms.ChoiceField(
        choices=[
            ("", "Select advisory type..."),
            ("opportunity_id", "Opportunity Identification"),
            ("feasibility", "Feasibility Assessment"),
            ("partner_match", "Partner Matchmaking"),
            ("due_diligence", "Due Diligence Support"),
            ("site_selection", "Site Selection"),
            ("regulatory", "Regulatory Navigation"),
            ("comprehensive", "Comprehensive Advisory Package"),
        ],
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
    )

    preferred_countries = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple, choices=[]  # Set in __init__
    )

    preferred_sectors = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple, choices=[]  # Set in __init__
    )

    project_description = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 5, "required": True, "maxlength": 1000}
        ),
    )

    message = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set country choices
        countries = MemberStateIPA.objects.filter(is_active=True).order_by("country_name")
        self.fields["preferred_countries"].choices = [
            (country.slug, country.country_name) for country in countries
        ]

        # Set sector choices
        sectors = Sector.objects.filter(is_active=True).order_by("name")
        self.fields["preferred_sectors"].choices = [
            (sector.slug, sector.name) for sector in sectors
        ]


class SiteVisitRequestForm(forms.Form):
    """
    Form for site visit coordination requests.
    Creates InvestorInquiry with inquiry_type='site_visit'.
    """

    # Personal Information
    first_name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    last_name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "required": True})
    )

    phone = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    country = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    # Company Information
    company_name = forms.CharField(
        max_length=200, widget=forms.TextInput(attrs={"class": "form-control", "required": True})
    )

    role = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))

    # Visit Details
    visit_purpose = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=[
            ("facility_inspection", "Facility Inspection"),
            ("meet_ipa", "Meet IPA Officials"),
            ("meet_partners", "Meet Potential Partners"),
            ("infrastructure", "Infrastructure Assessment"),
            ("market_research", "Market Research"),
            ("meet_government", "Meet Government Officials"),
        ],
    )

    preferred_date_from = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )

    preferred_date_to = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )

    duration_days = forms.IntegerField(
        min_value=1, max_value=30, widget=forms.NumberInput(attrs={"class": "form-control"})
    )

    number_of_people = forms.IntegerField(
        min_value=1, max_value=20, widget=forms.NumberInput(attrs={"class": "form-control"})
    )

    countries_to_visit = forms.MultipleChoiceField(
        required=True, widget=forms.CheckboxSelectMultiple, choices=[]  # Set in __init__
    )

    sectors_of_interest = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple, choices=[]  # Set in __init__
    )

    specific_facilities = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )

    special_requirements = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set country choices
        countries = MemberStateIPA.objects.filter(is_active=True).order_by("country_name")
        self.fields["countries_to_visit"].choices = [
            (country.slug, country.country_name) for country in countries
        ]

        # Set sector choices
        sectors = Sector.objects.filter(is_active=True).order_by("name")
        self.fields["sectors_of_interest"].choices = [
            (sector.slug, sector.name) for sector in sectors
        ]
