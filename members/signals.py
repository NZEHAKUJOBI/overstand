"""
members/signals.py

Cache invalidation signals for MemberStateIPA.

Whenever a MemberStateIPA record is saved (from any view, management command,
admin, or shell), we clear all cache keys that reference that record so the
public-facing pages immediately reflect the new data.
"""

from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from members.models import MemberStateIPA


@receiver(post_save, sender=MemberStateIPA)
def invalidate_member_state_cache(sender, instance, **kwargs):
    """Clear all cache keys related to the saved member state."""
    slug = instance.slug
    cache.delete_many([
        f"member_state_{slug}",
        f"country_profile_{slug}",
        "home_page_data",
        "all_active_member_states",
        "member_states_statistics",
        # featured_member_states_{limit} is keyed by limit, clear common values
        "featured_member_states_3",
        "featured_member_states_6",
        "featured_member_states_12",
    ])
