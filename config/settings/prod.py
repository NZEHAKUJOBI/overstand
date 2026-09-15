"""
Production settings - security-hardened configuration.
"""

import dj_database_url
from decouple import Csv, config

from .base import *  # noqa: F401 F403

DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF trusted origins for Docker/reverse proxy
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="https://example.com", cast=Csv())

# Production database — reads DATABASE_URL set by Heroku.
# Fail loudly if not set: a missing DB URL must never silently fall back to SQLite in prod.
DATABASE_URL = config("DATABASE_URL")  # raises UndefinedValueError if missing
DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Email: inherits Mailjet SMTP settings from base.py.
# All email (password reset, invitations, etc.) uses MailjetService which
# calls mailjet_rest.Client directly with MAILJET_API_KEY / MAILJET_SECRET_KEY.

# Logging — full tracebacks go to Heroku stdout
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        # Full Django request tracebacks (500 errors)
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        # Security warnings, DB errors, etc.
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
