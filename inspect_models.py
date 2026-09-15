"""
IPAWAS Model Field Inspector

This script shows you ALL available fields in your models.
Use this to verify what fields exist before populating data.

Usage: python inspect_models.py
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from members.models import (
    FDIDataPoint,
    InvestmentIncentive,
    InvestorInquiry,
    IPAStaff,
    MemberStateIPA,
    MemberStateSector,
    Sector,
    SuccessStory,
)
from opportunities.models import InvestmentOpportunity

try:
    from dashboard.models import IPADashboardActivity, IPANotification
except ImportError:
    IPADashboardActivity = None
    IPANotification = None

try:
    from invitations.models import Invitation
except ImportError:
    Invitation = None

try:
    from accounts.models import IPAUser
except ImportError:
    IPAUser = None


def inspect_model(model):
    """Show all fields for a model"""
    print(f"\n{'='*70}")
    print(f"MODEL: {model.__name__}")
    print(f"{'='*70}")

    fields = model._meta.get_fields()

    # Regular fields
    print("\n📝 REGULAR FIELDS:")
    for field in fields:
        if hasattr(field, "get_internal_type"):
            field_type = field.get_internal_type()
            null_blank = []
            if getattr(field, "null", False):
                null_blank.append("null=True")
            if getattr(field, "blank", False):
                null_blank.append("blank=True")

            # Check if it's a choice field
            if hasattr(field, "choices") and field.choices:
                print(
                    f"  • {field.name} ({field_type}) - CHOICES: {[c[0] for c in field.choices[:3]]}..."
                )
            else:
                status = f" [{', '.join(null_blank)}]" if null_blank else ""
                print(f"  • {field.name} ({field_type}){status}")

    # Relations
    print("\n🔗 RELATIONSHIPS:")
    for field in fields:
        if hasattr(field, "related_model") and not hasattr(field, "get_internal_type"):
            rel_type = type(field).__name__
            print(f"  • {field.name} ({rel_type}) → {field.related_model.__name__}")


def main():
    print("=" * 70)
    print("IPAWAS MODEL STRUCTURE INSPECTOR")
    print("=" * 70)
    print("\nThis shows ALL fields available in each model.")
    print("Use this to verify what fields you can populate.\n")

    # Core models
    models_to_inspect = [
        ("Core Models", [MemberStateIPA, Sector, MemberStateSector]),
        ("Investment Models", [InvestmentOpportunity, InvestmentIncentive, SuccessStory]),
        ("Inquiry & Staff", [InvestorInquiry, IPAStaff]),
        ("Data Models", [FDIDataPoint]),
    ]

    # Add optional models
    if IPADashboardActivity:
        models_to_inspect.append(("Dashboard Models", [IPADashboardActivity, IPANotification]))
    if Invitation:
        models_to_inspect.append(("Invitation Model", [Invitation]))
    if IPAUser:
        models_to_inspect.append(("User Model", [IPAUser]))

    for category, models in models_to_inspect:
        print(f"\n\n{'#'*70}")
        print(f"# {category.upper()}")
        print(f"{'#'*70}")

        for model in models:
            if model:
                inspect_model(model)

    print("\n\n" + "=" * 70)
    print("✅ INSPECTION COMPLETE")
    print("=" * 70)
    print("\nNow you know exactly what fields are available!")
    print("Use these field names when creating data.")


if __name__ == "__main__":
    main()
