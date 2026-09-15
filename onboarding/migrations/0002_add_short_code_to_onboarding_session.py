import onboarding.models
from django.db import migrations, models


def populate_short_codes(apps, schema_editor):
    OnboardingSession = apps.get_model("onboarding", "OnboardingSession")
    for session in OnboardingSession.objects.filter(short_code=""):
        session.short_code = onboarding.models._generate_short_code()
        session.save(update_fields=["short_code"])


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0001_initial"),
    ]

    operations = [
        # Step 1: add nullable, no unique yet
        migrations.AddField(
            model_name="onboardingsession",
            name="short_code",
            field=models.CharField(
                default="",
                editable=False,
                help_text="6-char short code for the friendly /join/<code>/ URL.",
                max_length=8,
            ),
            preserve_default=False,
        ),
        # Step 2: fill in short codes for any existing rows
        migrations.RunPython(populate_short_codes, migrations.RunPython.noop),
        # Step 3: add unique constraint now that all rows have a value
        migrations.AlterField(
            model_name="onboardingsession",
            name="short_code",
            field=models.CharField(
                default=onboarding.models._generate_short_code,
                editable=False,
                help_text="6-char short code for the friendly /join/<code>/ URL.",
                max_length=8,
                unique=True,
            ),
        ),
    ]
