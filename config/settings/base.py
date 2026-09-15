"""
Base Django settings - shared across all environments.

These settings are imported by dev.py and prod.py.
Do not use this file directly via DJANGO_SETTINGS_MODULE.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import Csv, config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

AUTH_USER_MODEL = "accounts.User"

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # Security & Auth
    "axes",                          # Brute-force protection (must be after auth)
    "django_otp",                    # Two-factor authentication base
    "django_otp.plugins.otp_totp",  # TOTP (Google Authenticator compatible)
    "django_celery_beat",            # Database-backed Celery Beat scheduler
    # Installed apps
    "core",
    "accounts",
    "members",
    "opportunities",
    "waiis",
    "dashboard",
    "invitations",
    "media_app",
    "knowledge_hub",
    "training",
    "onboarding",
    "feedback",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",           # Must be after AuthenticationMiddleware
    "axes.middleware.AxesMiddleware",                # Must be after AuthenticationMiddleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "core.context_processors.social_urls",
                "core.context_processors.seo",
                "core.context_processors.dashboard_badges",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database - configurable via environment variables
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": config("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        "USER": config("DB_USER", default=""),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default=""),
        "PORT": config("DB_PORT", default=""),
    }
}


# DATABASES = {
#     "default": dj_database_url.config(
#         default=config(
#             "DATABASE_URL",
#             default="postgres://postgres:postgres@localhost:5433/new_ipawas",
#         )
#     )
# }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",          # Must be first for brute-force lockout
    "django.contrib.auth.backends.ModelBackend",
]

# Login/Logout URLs
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "home"  # Fallback only — custom _redirect_to_dashboard() handles real routing
LOGOUT_REDIRECT_URL = "home"

# Session Configuration
SESSION_COOKIE_AGE = 3600  # 1 hour — increased from 30 min so staff aren't logged out mid-task
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only in production
SESSION_COOKIE_SAMESITE = "Lax"

# CSRF Configuration
CSRF_COOKIE_SECURE = not DEBUG
# Must be False so JavaScript can read the csrftoken cookie for AJAX requests.
# HttpOnly offers no meaningful CSRF defence — CSRF exploits credentials, not steals them.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

# ============================================================================
# INTERNATIONALIZATION (i18n) CONFIGURATION
# ============================================================================

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("fr", "Français"),
    ("pt", "Português"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

LANGUAGE_COOKIE_NAME = "django_language"
LANGUAGE_COOKIE_AGE = 365 * 24 * 60 * 60
LANGUAGE_COOKIE_PATH = "/"
LANGUAGE_COOKIE_SECURE = not DEBUG
LANGUAGE_COOKIE_HTTPONLY = False
LANGUAGE_COOKIE_SAMESITE = "Lax"

# ============================================================================
# STATIC & MEDIA FILES
# ============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Geo-IP database path (MaxMind GeoLite2-Country.mmdb)
GEOIP_PATH = BASE_DIR / "geoip"

# Static file storage - WhiteNoise (non-manifest for debugging)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_MAX_AGE = 31536000  # 1 year cache for hashed static files

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# (duplicate block removed — see AUTHENTICATION_BACKENDS defined above)

# AWS S3 Configuration (if using)
USE_S3 = config("USE_S3", default=False)

if USE_S3:
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_FILE_OVERWRITE = False

    # Update STORAGES to use S3 for media files
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Site Framework
SITE_ID = 1

# Crispy Forms (Bootstrap 5)
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ============================================================================
# EMAIL CONFIGURATION (MAILJET)
# ============================================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Mailjet SMTP Settings
EMAIL_HOST = "in-v3.mailjet.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("MAILJET_API_KEY", default="")
EMAIL_HOST_PASSWORD = config("MAILJET_SECRET_KEY", default="")

# Mailjet API Configuration
SITE_URL = config("SITE_URL", default="")
MAILJET_API_KEY = config("MAILJET_API_KEY", default="")
MAILJET_SECRET_KEY = config("MAILJET_SECRET_KEY", default="")
MAILJET_SENDER_EMAIL = config("MAILJET_SENDER_EMAIL", default="noreply@ipawas.org")
MAILJET_SENDER_NAME = config("MAILJET_SENDER_NAME", default="IPAWAS Platform")
MAILJET_NEWSLETTER_LIST_ID = config("MAILJET_NEWSLETTER_LIST_ID", default="", cast=str)

# Social media URLs (set real URLs in environment)
SOCIAL_LINKEDIN = config("SOCIAL_LINKEDIN", default="")
SOCIAL_TWITTER = config("SOCIAL_TWITTER", default="")
SOCIAL_FACEBOOK = config("SOCIAL_FACEBOOK", default="")
SOCIAL_YOUTUBE = config("SOCIAL_YOUTUBE", default="")
SOCIAL_INSTAGRAM = config("SOCIAL_INSTAGRAM", default="")

# Default FROM email
DEFAULT_FROM_EMAIL = MAILJET_SENDER_EMAIL
SERVER_EMAIL = MAILJET_SENDER_EMAIL

# Recipient for contact form submissions
CONTACT_EMAIL = config("CONTACT_EMAIL", default="infodesk@ipawas.org")

# ============================================================================
# CELERY CONFIGURATION (Async Tasks)
# ============================================================================

# REDIS_URL is automatically injected by the Heroku Redis add-on.
# Locally it falls back to a localhost Redis instance (optional).
_REDIS_URL = config("REDIS_URL", default=None)

# Heroku Redis uses TLS (rediss://).  Celery requires ssl_cert_reqs be
# specified explicitly on TLS URLs — append it if the URL starts with rediss://.
def _celery_redis_url(url: str) -> str:
    """Return url with ssl_cert_reqs appended for rediss:// schemes."""
    if url and url.startswith("rediss://") and "ssl_cert_reqs" not in url:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}ssl_cert_reqs=CERT_NONE"
    return url

_broker_url = _REDIS_URL or "redis://localhost:6379/0"
CELERY_BROKER_URL = _celery_redis_url(_broker_url)
# Store task results in Redis (same instance) — avoids needing django-celery-results
CELERY_RESULT_BACKEND = _celery_redis_url(_broker_url)
CELERY_CACHE_BACKEND = "django-cache"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule (Periodic Tasks)
CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-invitations": {
        "task": "invitations.tasks.cleanup_expired_invitations",
        "schedule": timedelta(hours=6),
    },
    "send-opportunity-expiry-reminders": {
        "task": "opportunities.tasks.send_expiry_reminders",
        "schedule": timedelta(days=1),
    },
    # Homepage cache warm-up — runs every 14 min, just before the 15-min TTL
    "warm-homepage-cache": {
        "task": "core.tasks.warm_homepage_cache",
        "schedule": timedelta(minutes=14),
    },
}

# ============================================================================
# INVITATION SYSTEM CONFIGURATION
# ============================================================================

INVITATION_EXPIRY_DAYS = config("INVITATION_EXPIRY_DAYS", default=7)
INVITATION_REMINDER_DAYS = config("INVITATION_REMINDER_DAYS", default=2)

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Django Axes (Brute-force protection)
AXES_FAILURE_LIMIT = 5                           # Lock after 5 failed attempts
AXES_COOLOFF_TIME = timedelta(minutes=30)        # Lockout duration
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]  # Lock user+IP pair (replaces deprecated AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP)
AXES_RESET_ON_SUCCESS = True                     # Reset counter on successful login
AXES_LOCKOUT_TEMPLATE = None                     # Use default 403 response
AXES_ENABLE_ADMIN = True                         # Allow unlock from admin panel

# Two-Factor Authentication
OTP_TOTP_ISSUER = "IPAWAS Platform"

# Support / Contact Email
SUPPORT_EMAIL = config("SUPPORT_EMAIL", default="support@ipawas.org")
CONTACT_EMAIL = config("CONTACT_EMAIL", default="infodesk@ipawas.org")

# Trusted proxy — Heroku terminates SSL and sets X-Forwarded-For
# Must be set to 1 so Django correctly identifies the real client IP
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "ipawas.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / "logs", exist_ok=True)

# ============================================================================
# SENTRY CONFIGURATION (Error Tracking)
# ============================================================================

SENTRY_DSN = config("SENTRY_DSN", default="")

if SENTRY_DSN and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production" if not DEBUG else "development",
    )

# ============================================================================
# CACHING CONFIGURATION
# ============================================================================

# Use Redis when REDIS_URL is available (Heroku Redis add-on sets this
# automatically). Fall back to in-process LocMemCache so the app still runs
# without a Redis instance (development / add-on not yet provisioned).
#
# Heroku Redis uses TLS (rediss://) with a self-signed cert.  redis-py by
# default requires a valid cert (CERT_REQUIRED).  We must pass
# ssl_cert_reqs=None (equivalent to CERT_NONE) in OPTIONS so that Django's
# RedisCache backend can connect — the same fix already applied to Celery.
_cache_redis_url = _celery_redis_url(_REDIS_URL) if _REDIS_URL else None

if _cache_redis_url:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _cache_redis_url,
            "KEY_PREFIX": "ipawas",
            "TIMEOUT": 300,  # 5 minutes default
            "OPTIONS": {
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            },
        }
    }
else:
    # No Redis available — use a fast in-memory cache per process.
    # Cache is lost on dyno restart and is not shared between dynos,
    # but prevents any crash when Redis isn't provisioned.
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "ipawas-locmem",
        }
    }

# ============================================================================
# DASHBOARD CONFIGURATION
# ============================================================================

# Dashboard Settings
DASHBOARD_ITEMS_PER_PAGE = 25
DASHBOARD_RECENT_ACTIVITIES_LIMIT = 10
DASHBOARD_NOTIFICATION_RETENTION_DAYS = 90

# File Upload Limits
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"]
ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

# Allow large file uploads (PDFs, images) — Django default is 2.5MB in memory
# Files above FILE_UPLOAD_MAX_MEMORY_SIZE are spooled to disk (not rejected)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB in memory before spooling to disk
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB max POST body size

# Activity Log Retention
ACTIVITY_LOG_RETENTION_DAYS = 365  # Keep for 1 year

# Cloudinary Configuration
# Defaults prevent a startup crash when vars are not yet set in the environment.
# Set CLOUDINARY_CLOUD_NAME / API_KEY / API_SECRET in Heroku config vars or .env.
CLOUDINARY_CLOUD_NAME = config("CLOUDINARY_CLOUD_NAME", default="")
CLOUDINARY_API_KEY = config("CLOUDINARY_API_KEY", default="")
CLOUDINARY_API_SECRET = config("CLOUDINARY_API_SECRET", default="")
