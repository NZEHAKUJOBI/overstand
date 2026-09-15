"""
management command: clear_cache
================================
Clears Redis cache entries for one or all member states.

Usage:
    # Clear a specific member state (e.g. after manual DB edit)
    heroku run python manage.py clear_cache --slug ghana

    # Clear all member-state cache entries + global caches
    heroku run python manage.py clear_cache --all

    # Dry-run: show which keys would be deleted without deleting
    heroku run python manage.py clear_cache --all --dry-run
"""

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from members.models import MemberStateIPA


GLOBAL_KEYS = [
    "home_page_data",
    "all_active_member_states",
    "member_states_statistics",
    "featured_member_states_3",
    "featured_member_states_6",
    "featured_member_states_12",
]


def _keys_for_slug(slug: str) -> list[str]:
    return [
        f"member_state_{slug}",
        f"country_profile_{slug}",
    ]


class Command(BaseCommand):
    help = "Clear Redis cache for one or all member states."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--slug",
            metavar="SLUG",
            help="Clear cache for a single member state (e.g. --slug ghana)",
        )
        group.add_argument(
            "--all",
            action="store_true",
            help="Clear cache for ALL member states plus global cache keys",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the keys that would be deleted without actually deleting them",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        keys_to_delete: list[str] = []

        if options["slug"]:
            slug = options["slug"].strip().lower()
            if not MemberStateIPA.objects.filter(slug=slug).exists():
                raise CommandError(f"No MemberStateIPA found with slug '{slug}'.")
            keys_to_delete = _keys_for_slug(slug) + GLOBAL_KEYS

        else:  # --all
            slugs = list(MemberStateIPA.objects.values_list("slug", flat=True))
            for slug in slugs:
                keys_to_delete.extend(_keys_for_slug(slug))
            keys_to_delete.extend(GLOBAL_KEYS)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_keys: list[str] = []
        for k in keys_to_delete:
            if k not in seen:
                seen.add(k)
                unique_keys.append(k)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no keys deleted."))
            for k in unique_keys:
                self.stdout.write(f"  would delete: {k}")
            return

        cache.delete_many(unique_keys)
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {len(unique_keys)} cache key(s):"),
        )
        for k in unique_keys:
            self.stdout.write(f"  {k}")
