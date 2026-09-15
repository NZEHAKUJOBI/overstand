from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("members", "0009_add_document_to_investmentincentive"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Feedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("idea", "Idea"), ("suggestion", "Suggestion"), ("observation", "Observation"), ("bug_report", "Bug Report")], max_length=20)),
                ("title", models.CharField(max_length=200)),
                ("body", models.TextField()),
                ("status", models.CharField(choices=[("new", "New"), ("under_review", "Under Review"), ("acknowledged", "Acknowledged"), ("implemented", "Implemented"), ("declined", "Declined")], default="new", max_length=20)),
                ("admin_response", models.TextField(blank=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("member_state", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feedback", to="members.memberStateipa")),
                ("responded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="feedback_responses", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feedback_submissions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Feedback",
                "verbose_name_plural": "Feedback",
                "ordering": ["-created_at"],
            },
        ),
    ]
