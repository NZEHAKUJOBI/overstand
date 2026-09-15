"""
Geo-detection utilities for IPAWAS homepage personalization.

Uses django-ipware to extract the real client IP (handles Heroku's
X-Forwarded-For proxy headers) and geoip2 + MaxMind GeoLite2-Country.mmdb
to resolve it to a country — all in-process, zero network latency,
zero third-party data exposure.

Privacy: the IP is used only to select content and is never stored or logged.
"""
import logging
import threading

from django.conf import settings

logger = logging.getLogger(__name__)

# Mapping: ISO 3166-1 alpha-2 → alpha-3 for ECOWAS member states.
# alpha-3 matches MemberStateIPA.country_code field.
ECOWAS_ISO2_TO_ISO3 = {
    "BJ": "BEN",  # Benin
    "CV": "CPV",  # Cabo Verde
    "CI": "CIV",  # Côte d'Ivoire
    "GM": "GMB",  # Gambia
    "GH": "GHA",  # Ghana
    "GN": "GIN",  # Guinea
    "GW": "GNB",  # Guinea-Bissau
    "LR": "LBR",  # Liberia
    "ML": "MLI",  # Mali (inactive, included for completeness)
    "MR": "MRT",  # Mauritania
    "NE": "NER",  # Niger (inactive)
    "NG": "NGA",  # Nigeria
    "SN": "SEN",  # Senegal
    "SL": "SLE",  # Sierra Leone
    "TG": "TGO",  # Togo
}

# Thread-local singleton for the GeoIP2 reader.
# Opened once per dyno process — geoip2 readers are thread-safe for reads.
_geoip_local = threading.local()


def _get_geoip_reader():
    """Return a cached geoip2 Reader, opening it once per thread."""
    if not hasattr(_geoip_local, "reader"):
        import geoip2.database  # noqa: PLC0415 — lazy import

        db_path = str(settings.GEOIP_PATH / "GeoLite2-Country.mmdb")
        _geoip_local.reader = geoip2.database.Reader(db_path)
    return _geoip_local.reader


def get_visitor_country_iso2(request) -> str | None:
    """
    Return the ISO 3166-1 alpha-2 country code for the request's IP address.
    Returns None if detection fails or the IP is not routable (dev/private).
    Never raises — always degrades gracefully.
    """
    try:
        from ipware import get_client_ip  # noqa: PLC0415

        ip, is_routable = get_client_ip(request)
        if not ip or not is_routable:
            return None

        reader = _get_geoip_reader()
        response = reader.country(ip)
        return response.country.iso_code  # alpha-2, e.g. "NG"
    except Exception:
        # Log at DEBUG only — this is expected to fail in local dev
        logger.debug("Geo-detection unavailable", exc_info=False)
        return None


def get_visitor_ecowas_iso3(request) -> str | None:
    """
    Return the ISO 3166-1 alpha-3 code if the visitor is from an ECOWAS
    country, else None. This matches MemberStateIPA.country_code.

    Examples:
        Nigerian visitor  → "NGA"
        Ghanaian visitor  → "GHA"
        French visitor    → None
        Local/dev request → None
    """
    iso2 = get_visitor_country_iso2(request)
    if not iso2:
        return None
    return ECOWAS_ISO2_TO_ISO3.get(iso2.upper())
