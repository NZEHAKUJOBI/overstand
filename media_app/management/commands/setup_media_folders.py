"""
Management command to create system folders for all member states.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from media_app.services import FolderService
from members.models import MemberStateIPA


class Command(BaseCommand):
    help = "Create system media folders for all active member states"

    def add_arguments(self, parser):
        parser.add_argument(
            "--member-state",
            type=str,
            help="Slug of specific member state (optional)",
        )

    def handle(self, *args, **options):
        member_state_slug = options.get("member_state")

        if member_state_slug:
            # Setup for specific member state
            try:
                member_state = MemberStateIPA.objects.get(slug=member_state_slug)
                self.setup_folders(member_state)
            except MemberStateIPA.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Member state with slug "{member_state_slug}" not found')
                )
        else:
            # Setup for all active member states
            member_states = MemberStateIPA.objects.filter(is_active=True)

            self.stdout.write(
                f"Setting up media folders for {member_states.count()} member states..."
            )

            for member_state in member_states:
                self.setup_folders(member_state)

            self.stdout.write(self.style.SUCCESS("\nAll system folders created successfully!"))

    @transaction.atomic
    def setup_folders(self, member_state):
        """Setup folders for a single member state"""
        try:
            root, created_folders = FolderService.ensure_system_folders(member_state)

            if created_folders:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {member_state.country_name}: Created {len(created_folders)} system folders"
                    )
                )
            else:
                self.stdout.write(f"  {member_state.country_name}: System folders already exist")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ {member_state.country_name}: Error - {str(e)}"))
