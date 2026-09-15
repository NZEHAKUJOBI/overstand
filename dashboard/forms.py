"""
Member Profile Forms - IPAWAS Platform
=======================================

Forms for editing member state profiles with integrated file uploads.
"""

from django import forms
from django.core.exceptions import ValidationError

from core.models import Sector as GlobalSector
from members.models import FDIDataPoint, IPALeadership, InvestmentIncentive, MemberStateIPA, MemberStateSector, Sector, SuccessStory


class BasicInfoForm(forms.ModelForm):
    """Form for basic IPA information and branding"""

    # File upload fields (handled separately with Cloudinary)
    logo = forms.FileField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
    # banner_image = forms.FileField(
    #     required=False, widget=forms.FileInput(attrs={"accept": "image/*"})
    # )
    hero_image = forms.FileField(
        required=False, widget=forms.FileInput(attrs={"accept": "image/*"})
    )
    card_image = forms.FileField(
        required=False, widget=forms.FileInput(attrs={"accept": "image/*"})
    )
    investment_guide_pdf = forms.FileField(
        required=False, widget=forms.FileInput(attrs={"accept": ".pdf"})
    )
    doing_business_pdf = forms.FileField(
        required=False, widget=forms.FileInput(attrs={"accept": ".pdf"})
    )

    class Meta:
        model = MemberStateIPA
        fields = [
            "ipa_full_name",
            "ipa_acronym",
            # "display_name",
            "tagline",
            "overview",
            # "why_invest",
            "contact_email",
            "contact_phone",
            "ipa_website",
            "physical_address",
            # "primary_color",
            # "secondary_color",
            "linkedin_url",
            "twitter_url",
            "facebook_url",
            "instagram_url",
            # "youtube_url",
        ]
        widgets = {
            "ipa_full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Nigerian Investment Promotion Commission",
                }
            ),
            "ipa_acronym": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., NIPC, GIPA, APIX",
                    "maxlength": "20",
                }
            ),
            "display_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Optional display name"}
            ),
            "tagline": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Gateway to West Africa",
                    "maxlength": "200",
                }
            ),
            "overview": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": "Provide a compelling overview of your country and investment opportunities...",
                }
            ),
            "why_invest": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Key reasons investors should choose your country...",
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "contact@ipa.gov"}
            ),
            "contact_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+234 xxx xxx xxxx"}
            ),
            "ipa_website": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://www.ipa.gov"}
            ),
            "physical_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Complete mailing address",
                }
            ),
            "primary_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "secondary_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "linkedin_url": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://linkedin.com/company/..."}
            ),
            "twitter_url": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://twitter.com/..."}
            ),
            "facebook_url": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://facebook.com/..."}
            ),
            "instagram_url": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://instagram.com/..."}
            ),
            "youtube_url": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://youtube.com/@..."}
            ),
        }

    def clean_tagline(self):
        tagline = self.cleaned_data.get("tagline", "")
        if tagline and len(tagline) > 200:
            raise ValidationError("Tagline must be 200 characters or less.")
        return tagline

    def clean_primary_color(self):
        color = self.cleaned_data.get("primary_color", "")
        if color and not color.startswith("#"):
            raise ValidationError("Color must be in hex format (e.g., #1b7a4c)")
        return color

    def clean_secondary_color(self):
        color = self.cleaned_data.get("secondary_color", "")
        if color and not color.startswith("#"):
            raise ValidationError("Color must be in hex format (e.g., #3cb371)")
        return color


class EconomicDataForm(forms.ModelForm):
    """Form for economic indicators and statistics"""

    class Meta:
        model = MemberStateIPA
        fields = [
            "gdp",
            "gdp_growth_rate",
            "gdp_per_capita",
            "inflation_rate",
            "population",
            "population_growth",
            "median_age",
            "urbanization_rate",
            "literacy_rate",
            "ease_of_doing_business_rank",
            "fdi_inflows",
            "corporate_tax_rate",
            "days_to_start_business",
            "total_exports",
            "total_imports",
            "key_industries",
            "trade_agreements",
            "competitiveness_score",
            "electricity_access",
            "internet_penetration",
            "paved_roads_percent",
            "number_of_airports",
        ]
        widgets = {
            "gdp": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "450.5", "step": "0.01"}
            ),
            "gdp_growth_rate": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "3.5", "step": "0.01"}
            ),
            "gdp_per_capita": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "5000", "step": "0.01"}
            ),
            "inflation_rate": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "2.5", "step": "0.01"}
            ),
            "population": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "200000000"}
            ),
            "population_growth": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "2.5", "step": "0.01"}
            ),
            "median_age": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "18.5", "step": "0.1"}
            ),
            "urbanization_rate": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "52.0", "step": "0.01"}
            ),
            "literacy_rate": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "65.0", "step": "0.01"}
            ),
            "ease_of_doing_business_rank": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "131"}
            ),
            "fdi_inflows": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "2500.00", "step": "0.01"}
            ),
            "corporate_tax_rate": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "30.0", "step": "0.01"}
            ),
            "days_to_start_business": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "30"}
            ),
            "total_exports": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "15000.00", "step": "0.01"}
            ),
            "total_imports": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "12000.00", "step": "0.01"}
            ),
            "key_industries": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Agriculture, Oil & Gas, Manufacturing, Services",
                }
            ),
            "trade_agreements": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "ECOWAS, AfCFTA, WTO"}
            ),
            "electricity_access": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "55.0", "step": "0.01"}
            ),
            "internet_penetration": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "42.0", "step": "0.01"}
            ),
            "paved_roads_percent": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "15.0", "step": "0.01"}
            ),
            "competitiveness_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "52.4",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "number_of_airports": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "26"}
            ),
        }


class SEOSettingsForm(forms.ModelForm):
    """Form for SEO and meta settings"""

    # Additional SEO fields (store in JSONField if needed)
    meta_title = forms.CharField(
        required=False,
        max_length=60,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Invest in Nigeria - IPAWAS",
                "maxlength": "60",
            }
        ),
    )

    meta_description = forms.CharField(
        required=False,
        max_length=160,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "maxlength": "160",
                "placeholder": "Discover investment opportunities...",
            }
        ),
    )

    meta_keywords = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "investment, opportunities, business, africa",
            }
        ),
    )

    og_title = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Investment Opportunities in Nigeria"}
        ),
    )

    og_description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Explore world-class investment opportunities...",
            }
        ),
    )

    og_image = forms.FileField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))

    class Meta:
        model = MemberStateIPA
        fields = ["slug", "meta_title", "meta_description", "meta_keywords", "og_title", "og_description"]
        widgets = {
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "nigeria"})
        }


_FC = "form-control"
_FS = "form-select"


class IncentiveForm(forms.ModelForm):
    """Form for investment incentives."""

    document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            "class": _FC,
            "accept": ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx",
        }),
        help_text="Optional supporting document — PDF, Word, Excel, or PowerPoint. Maximum 20 MB.",
    )

    def __init__(self, *args, member_state=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Prefer sectors the member state has configured as Priority Sectors.
        # Fall back to every global sector when the member state hasn't added
        # any yet (or when no member_state is passed, e.g. Django admin) —
        # this field must never render with zero selectable options.
        queryset = GlobalSector.objects.all().order_by("name")
        if member_state is not None:
            scoped = queryset.filter(member_states__member_state=member_state)
            if scoped.exists():
                queryset = scoped
        # CRITICAL: assign the widget before the queryset. ModelMultipleChoiceField's
        # queryset setter copies resolved choices onto self.widget at assignment time
        # (see ModelChoiceField._set_queryset) — swapping the widget afterwards leaves
        # the new instance with no choices at all, so the checkboxes render empty
        # regardless of what the queryset contains.
        self.fields["applicable_sectors"].widget = forms.CheckboxSelectMultiple()
        self.fields["applicable_sectors"].queryset = queryset
        self.fields["applicable_sectors"].required = False

    def clean_document(self):
        file = self.cleaned_data.get("document")
        if file:
            max_bytes = 20 * 1024 * 1024  # 20 MB
            if file.size > max_bytes:
                raise ValidationError("File is too large. The maximum allowed size is 20 MB.")
            allowed_mimes = {
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            }
            if file.content_type not in allowed_mimes:
                raise ValidationError(
                    "Unsupported file type. Allowed formats: PDF, Word (.doc/.docx), "
                    "Excel (.xls/.xlsx), PowerPoint (.ppt/.pptx)."
                )
        return file

    class Meta:
        model = InvestmentIncentive
        fields = [
            "title", "incentive_type", "description", "duration",
            "eligibility_criteria", "applicable_sectors",
            "benefit_amount", "is_active", "display_order",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., 5-Year Corporate Tax Holiday"}),
            "incentive_type": forms.Select(attrs={"class": _FS}),
            "description": forms.Textarea(attrs={"class": _FC, "rows": 5, "placeholder": "Detailed description of the incentive…"}),
            "duration": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., 5–10 years, Ongoing"}),
            "eligibility_criteria": forms.Textarea(attrs={"class": _FC, "rows": 4, "placeholder": "Who qualifies for this incentive…"}),
            "benefit_amount": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., 100% tax exemption"}),
            "display_order": forms.NumberInput(attrs={"class": _FC}),
        }


class SuccessStoryForm(forms.ModelForm):
    """Form for investment success stories."""

    # image is handled via request.FILES in the view
    image = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )

    class Meta:
        model = SuccessStory
        fields = [
            "title", "company_name", "company_origin", "sector",
            "investment_amount", "investment_amount_display", "jobs_created",
            "year", "summary", "full_story", "impact",
            "published", "featured", "display_order",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., Tullow Oil Transforms Ghana's Energy Sector"}),
            "company_name": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., Tullow Oil PLC"}),
            "company_origin": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., United Kingdom"}),
            "sector": forms.Select(attrs={"class": _FS}),
            "investment_amount": forms.NumberInput(attrs={"class": _FC, "placeholder": "50000000", "step": "0.01"}),
            "investment_amount_display": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., $50M, $2.5B"}),
            "jobs_created": forms.NumberInput(attrs={"class": _FC, "placeholder": "e.g., 1200"}),
            "year": forms.NumberInput(attrs={"class": _FC, "placeholder": "e.g., 2022"}),
            "summary": forms.Textarea(attrs={"class": _FC, "rows": 3, "placeholder": "2–3 sentence summary shown on the public profile card…"}),
            "full_story": forms.Textarea(attrs={"class": _FC, "rows": 6, "placeholder": "Full narrative of the investment journey…"}),
            "impact": forms.Textarea(attrs={"class": _FC, "rows": 4, "placeholder": "Economic, social, or environmental impact…"}),
            "display_order": forms.NumberInput(attrs={"class": _FC}),
        }


class LeadershipForm(forms.ModelForm):
    """Form for IPA head-of-agency profile."""

    official_photograph = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )

    class Meta:
        model = IPALeadership
        fields = [
            "full_name", "official_title", "biography",
            "appointment_date", "direct_email", "last_verified",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., Dr. Hinga Sandi"}),
            "official_title": forms.Select(attrs={"class": _FS}),
            "biography": forms.Textarea(attrs={"class": _FC, "rows": 5, "placeholder": "Professional background, education, and vision (200–500 words recommended)…"}),
            "direct_email": forms.EmailInput(attrs={"class": _FC, "placeholder": "e.g., ceo@ipa.gov"}),
            "appointment_date": forms.DateInput(attrs={"class": _FC, "type": "date"}),
            "last_verified": forms.DateInput(attrs={"class": _FC, "type": "date"}),
        }


class FDIDataPointForm(forms.ModelForm):
    """Form for time-series FDI / economic data points."""

    class Meta:
        model = FDIDataPoint
        fields = [
            "data_type", "year", "value", "value_display",
            "data_source", "notes", "validation_status",
        ]
        widgets = {
            "data_type": forms.Select(attrs={"class": _FS}),
            "year": forms.NumberInput(attrs={"class": _FC, "placeholder": "e.g., 2023"}),
            "value": forms.NumberInput(attrs={"class": _FC, "placeholder": "e.g., 4200.00", "step": "0.01"}),
            "value_display": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., $4.2B"}),
            "data_source": forms.TextInput(attrs={"class": _FC, "placeholder": "e.g., UNCTAD World Investment Report 2024"}),
            "notes": forms.Textarea(attrs={"class": _FC, "rows": 3, "placeholder": "Any caveats or methodology notes…"}),
            "validation_status": forms.Select(attrs={"class": _FS}),
        }


# Alias for backwards compatibility with views that import InvestmentIncentiveForm
InvestmentIncentiveForm = IncentiveForm


class SectorAddForm(forms.Form):
    """
    Free-text sector creation form.
    Typed name is matched against core.Sector (get_or_create) so member
    states can invent new sector names without needing admin access to the
    global Sector table.
    """

    sector_name = forms.CharField(
        max_length=100,
        label="Sector Name",
        widget=forms.TextInput(attrs={
            "class": _FC + " form-control-lg",
            "placeholder": "e.g., Agriculture & Agribusiness",
            "autocomplete": "off",
            "list": "sector-suggestions",
        }),
        help_text="Type any sector name. Existing names will be suggested as you type.",
    )
    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.Textarea(attrs={
            "class": _FC,
            "rows": 5,
            "placeholder": "Describe this sector and why it matters for investment in your country…",
        }),
        help_text="Country-specific description shown on your profile.",
    )
    investment_potential = forms.CharField(
        required=False,
        label="Investment Potential",
        widget=forms.TextInput(attrs={
            "class": _FC,
            "placeholder": "e.g., High — $2B pipeline over 5 years",
        }),
        help_text="Brief note on investment opportunity in this sector.",
    )
    is_priority = forms.BooleanField(
        required=False,
        label="Mark as a priority sector",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Priority sectors are highlighted on your country profile.",
    )

    def clean_sector_name(self):
        return self.cleaned_data["sector_name"].strip()


class SectorEditForm(forms.ModelForm):
    """Edit the per-country details of a linked sector (name is immutable)."""

    class Meta:
        model = MemberStateSector
        fields = ["description", "investment_potential", "is_priority"]
        widgets = {
            "description": forms.Textarea(attrs={
                "class": _FC,
                "rows": 5,
                "placeholder": "Country-specific description for this sector…",
            }),
            "investment_potential": forms.TextInput(attrs={
                "class": _FC,
                "placeholder": "e.g., High — $2B pipeline over 5 years",
            }),
            "is_priority": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            "description": "Country-specific description shown on your profile.",
            "investment_potential": "Brief note on investment opportunity in this sector.",
            "is_priority": "Priority sectors are highlighted on your country profile.",
        }
