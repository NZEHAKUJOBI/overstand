"""
Celery tasks for the core app — homepage cache management.
"""
import logging

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache keys used by the homepage view
HOMEPAGE_BASE_KEY = "homepage_base_context"
HOMEPAGE_OPP_KEY_PREFIX = "homepage_opps_"

# ECOWAS ISO3 codes + the global fallback key
ECOWAS_ISO3_CODES = [
    "BEN", "CPV", "CIV", "GMB", "GHA", "GIN",
    "GNB", "LBR", "NGA", "SEN", "SLE", "TGO",
]


@shared_task(name="core.tasks.invalidate_homepage_cache")
def invalidate_homepage_cache():
    """
    Delete all homepage cache keys so the next request rebuilds them fresh.
    Called after significant content changes (new opportunity published, etc.).
    """
    keys = [HOMEPAGE_BASE_KEY] + [
        f"{HOMEPAGE_OPP_KEY_PREFIX}{iso3}" for iso3 in ECOWAS_ISO3_CODES
    ] + [f"{HOMEPAGE_OPP_KEY_PREFIX}global"]

    cache.delete_many(keys)
    logger.info("Homepage cache invalidated (%d keys)", len(keys))


@shared_task(name="core.tasks.warm_homepage_cache")
def warm_homepage_cache():
    """
    Pre-warm the homepage cache every 14 minutes so the TTL never expires
    under a real user request. This prevents the cold-cache penalty hitting
    the first visitor after expiry.

    Runs slightly before the 15-minute TTL so there is always a warm entry.
    """
    try:
        # Import here to avoid circular imports at module load time
        from django.test import RequestFactory
        from core.views.home import index as home_view

        factory = RequestFactory()
        # Simulate a generic (non-ECOWAS) request to warm the global cache
        fake_request = factory.get("/")
        fake_request.LANGUAGE_CODE = "en"
        home_view(fake_request)
        logger.info("Homepage cache warmed successfully")
    except Exception:
        # Never let a warm-up failure bubble up — it is non-critical
        logger.warning("Homepage cache warm-up failed", exc_info=True)
