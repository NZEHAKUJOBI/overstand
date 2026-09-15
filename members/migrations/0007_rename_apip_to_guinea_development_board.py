"""
Data migration: rename Guinea's IPA from APIP-Guinée to Guinea Development Board.

APIP-Guinée (Agence de Promotion des Investissements Privés) no longer exists;
it has been replaced by the Guinea Development Board (GDB).
"""

from django.db import migrations


def rename_apip_to_gdb(apps, schema_editor):
    MemberStateIPA = apps.get_model("members", "MemberStateIPA")
    updated = MemberStateIPA.objects.filter(slug="guinea").update(
        ipa_full_name="Guinea Development Board",
        ipa_acronym="GDB",
    )
    if updated:
        print(f"  Updated Guinea IPA record: APIP-Guinée → Guinea Development Board (GDB)")


def reverse_rename(apps, schema_editor):
    MemberStateIPA = apps.get_model("members", "MemberStateIPA")
    MemberStateIPA.objects.filter(slug="guinea").update(
        ipa_full_name="Agence de Promotion des Investissements Privés",
        ipa_acronym="APIP-Guinée",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0006_add_email_index_to_investor_inquiry"),
    ]

    operations = [
        migrations.RunPython(rename_apip_to_gdb, reverse_code=reverse_rename),
    ]
