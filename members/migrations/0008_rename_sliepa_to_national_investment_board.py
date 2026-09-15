"""
Data migration: rename Sierra Leone's IPA from SLIEPA to National Investment Board.

Sierra Leone Investment and Export Promotion Agency (SLIEPA) no longer exists;
it has been replaced by the National Investment Board (NIB-SL).
"""

from django.db import migrations


def rename_sliepa_to_nib(apps, schema_editor):
    MemberStateIPA = apps.get_model("members", "MemberStateIPA")
    updated = MemberStateIPA.objects.filter(slug="sierra-leone").update(
        ipa_full_name="National Investment Board",
        ipa_acronym="NIB-SL",
        contact_email="info@nib.gov.sl",
        ipa_website="https://www.nib.gov.sl",
    )
    if updated:
        print(
            "  Updated Sierra Leone IPA record: "
            "SLIEPA → National Investment Board (NIB-SL)"
        )


def reverse_rename(apps, schema_editor):
    MemberStateIPA = apps.get_model("members", "MemberStateIPA")
    MemberStateIPA.objects.filter(slug="sierra-leone").update(
        ipa_full_name="Sierra Leone Investment and Export Promotion Agency",
        ipa_acronym="SLIEPA",
        contact_email="info@sliepa.gov.sl",
        ipa_website="https://www.sliepa.gov.sl",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0007_rename_apip_to_guinea_development_board"),
    ]

    operations = [
        migrations.RunPython(rename_sliepa_to_nib, reverse_code=reverse_rename),
    ]
