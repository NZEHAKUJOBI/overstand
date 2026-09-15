# IPAWAS Platform — Developer Handoff Document

**Last updated:** April 2026  
**Prepared by:** Claude (AI Engineering Assistant)  
**Status:** Active development — production running, two PRs pending merge

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Repository Structure](#3-repository-structure)
4. [Django Apps & Data Models](#4-django-apps--data-models)
5. [Environment Setup — Local (venv)](#5-environment-setup--local-venv)
6. [Environment Setup — Docker](#6-environment-setup--docker)
7. [Environment Setup — Heroku Production](#7-environment-setup--heroku-production)
8. [Configuration & Environment Variables](#8-configuration--environment-variables)
9. [CI/CD Pipeline](#9-cicd-pipeline)
10. [User Testing Feedback — Full Issue Registry](#10-user-testing-feedback--full-issue-registry)
11. [What Has Been Done — Detailed Change Log](#11-what-has-been-done--detailed-change-log)
12. [Current Production Bugs (UNRESOLVED)](#12-current-production-bugs-unresolved)
13. [Pending Tasks — Priority Order](#13-pending-tasks--priority-order)
14. [Programs Section — Intentionally Silenced](#14-programs-section--intentionally-silenced)
15. [Branch Strategy](#15-branch-strategy)
16. [Key Files Reference](#16-key-files-reference)
17. [Known Gotchas & Traps](#17-known-gotchas--traps)
18. [Database Migrations Reference](#18-database-migrations-reference)
19. [Populating the Database (Seed Data)](#19-populating-the-database-seed-data)
20. [Test Suite](#20-test-suite)

---

## 1. Project Overview

**IPAWAS** (Investment Promotion Agency of West Africa) is a Django-based web platform for a pan-West African investment promotion body. It serves three audiences:

- **Public / Investors** — browse member states, investment opportunities, knowledge hub, and contact IPAs
- **IPA Staff (Country Users)** — manage their country's profile, investment opportunities, news, and media via a country-specific dashboard
- **IPAWAS HQ Admins** — system-wide administration: manage all member states, invite IPA staff, view analytics, manage knowledge hub content

**Live URL:** [https://ipawas.org](https://ipawas.org)  
**Heroku App Name:** `ipawas`  
**GitHub Repo:** `https://github.com/Festorah/ipawas`

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5.1 (Python 3.10) |
| Database | PostgreSQL 15 (Heroku Postgres) |
| Cache | Redis (Heroku Redis Mini addon) |
| Task Queue | Celery 5.3 + Redis as broker |
| File/Image Storage | Cloudinary |
| Static Files | WhiteNoise (served from slug) |
| Production Server | Gunicorn 21.2 |
| Hosting | Heroku (auto-deploy from `main`) |
| Auth | Custom User model + django-axes (brute force) + django-otp (2FA) |
| Permissions | django-guardian (object-level) |
| Forms | django-crispy-forms + crispy-bootstrap5 |
| API | Django REST Framework + django-filter |
| Frontend | Bootstrap 5, vanilla JS, Leaflet.js (interactive map) |
| Email | Mailjet REST API |
| PDF | ReportLab + WeasyPrint |
| Monitoring | Sentry SDK (configured, DSN optional) |

---

## 3. Repository Structure

```
ipawas/
├── accounts/          # Custom user model, auth views, invitation system
├── config/            # Django settings, URLs, WSGI, Celery config
│   ├── settings/
│   │   ├── base.py    # Shared settings (all environments inherit this)
│   │   ├── dev.py     # Local development (DEBUG=True, SQLite ok)
│   │   ├── prod.py    # Production (DEBUG=False, Postgres, Redis)
│   │   ├── test.py    # Test suite (SQLite :memory:, DummyCache)
│   │   └── __init__.py  # Reads DJANGO_ENV to select settings module
│   ├── celery.py
│   ├── urls.py        # Root URL configuration
│   └── wsgi.py
├── core/              # Homepage, about, why-west-africa, opportunities, media-center pages
├── dashboard/         # HQ admin + country IPA dashboards
├── invitations/       # Invitation model and email flows
├── knowledge_hub/     # News, resources, press releases, media kit
├── media_app/         # File/folder management (Cloudinary-backed)
├── members/           # Member state profiles, sectors, FDI data, inquiries
├── notifications/     # In-app notification system (no migrations — abstract)
├── opportunities/     # Investment opportunity listings
├── waiis/             # WAIIS Data Portal (West Africa Investment Intelligence System)
├── static/            # Source static files (CSS, JS, images, GeoJSON)
├── staticfiles/       # Collected static files — NOT in git (.gitignore)
├── templates/         # Project-level templates (if any)
├── logs/              # Log output — only .gitkeep committed, *.log gitignored
├── bin/
│   └── post_compile   # Heroku build hook — runs collectstatic during slug build
├── Dockerfile         # Docker image (Python 3.10-slim)
├── docker-compose.yml # Local Docker dev: web + db + redis + worker
├── .env.docker        # Docker-specific env vars (not committed)
├── .env.example       # Template for .env — commit this, not .env
├── Procfile           # Heroku process types (web + worker)
├── runtime.txt        # python-3.10.13
├── requirements.txt   # All Python dependencies
├── pytest.ini         # Test configuration (on ci-cd-and-tests branch)
├── comprehensive_populate_ipawas.py   # Full seed data script
├── populate_*.py      # Individual seed scripts per app
└── inspect_models.py  # Utility to inspect model field structure
```

---

## 4. Django Apps & Data Models

### `accounts` — User Management & Authentication

**Models:**
- `User` — Custom user (extends AbstractUser). Key fields: `email` (login field, unique), `user_type` (`ipawas_admin` | `ipa_staff` | `investor`), `first_name`, `last_name`, `phone`, `is_active`, `date_joined`
- `IPAUser` — IPA staff profile (OneToOne → User). Links a staff user to their `MemberStateIPA`. Fields: `member_state`, `job_title`, `department`, `can_create_opportunities`, `can_manage_users`, `dashboard_access_count`

**Key views:** `LoginView`, `LogoutView`, `OnboardingView`, `AcceptInvitationView`, `ProfileView`, `ProfileUpdateView`, `IPAProfileUpdateView`, `PasswordResetRequestView`, `TeamMembersView`, `ManageUserPermissionsView`

**Auth flow:** Email-based login (no username). `user_type` drives dashboard routing. `django-axes` locks accounts after failed attempts.

---

### `members` — Member State Profiles (Core App)

**Models:**
- `MemberStateIPA` — The main country profile. Fields: country name, slug, ISO code, capital, language, currency, flag image, population, GDP, investment climate rating, IPA contact info, SEO fields (~60 fields total)
- `MemberStateSector` — Priority sector for a member state (ForeignKey → MemberStateIPA, FK → `core.Sector`)
- `InvestmentIncentive` — Tax/investment incentive (FK → MemberStateIPA)
- `SuccessStory` — Investment success story (FK → MemberStateIPA)
- `InvestorInquiry` — Investor inquiry submitted via the public contact form (FK → MemberStateIPA)
- `FDIDataPoint` — Historical FDI data points per year per country
- `IPAStaff` — Public staff listing for a member state (different from `accounts.IPAUser`)
- `IPALeadership` — Leadership team for a member state IPA
- `ECOWASLeadershipPosition` — ECOWAS body leadership positions

**Services layer** (`members/services.py`):
- `MemberStateService` — query helpers for member states
- `InquiryService` — create inquiry + send notifications
- `DataService` — FDI data calculations
- `CacheService` — Redis-backed cache (24h TTL) for statistics and member state detail pages

---

### `dashboard` — Staff Dashboards

Two separate dashboard spaces under `/dashboard/`:

**HQ Admin Dashboard** (`/dashboard/hq/`) — `user_type=ipawas_admin` only
- Overview analytics, member state management, user management
- Invitation management (invite IPA staff)
- Knowledge hub CMS (create/edit news articles)
- Opportunities management
- System settings, security logs

**Country/IPA Dashboard** (`/dashboard/<member_state_slug>/`) — `user_type=ipa_staff` only
- Country profile editor
- Opportunities CRUD
- Knowledge hub (country-level news)
- Media library
- Sector management
- Analytics

**Models:**
- `IPADashboardActivity` — Activity log for auditing dashboard actions
- `IPANotification` — In-dashboard notification system

**Routing:** `DashboardRoutingView` at `/dashboard/` redirects users to their correct dashboard based on `user_type`.

---

### `core` — Public-Facing Content Pages

Handles: Homepage, About IPAWAS, Why West Africa, Opportunities listing, Media Center, Programs (silenced — see §14)

**Models:** `Sector`, `Partner`, `Publication`, `Event`, `EventRegistration`

**URL namespaces:** `about`, `why_west_africa`, `opportunities`, `investor_services`, `knowledge_hub`, `media_center`

---

### `knowledge_hub` — News & Resources

**Models:** `Topic`, `Tag`, `NewsArticle`, `PressRelease`, `MediaCategory`, `Resource`, `MediaKitItem`

**URL namespace:** `knowledge_hub`

---

### `opportunities` — Investment Opportunities

**Models:** `InvestmentOpportunity`, `OpportunityDocument`, `OpportunityInquiry`, `OpportunityUpdate`

---

### `invitations` — Invitation System

**Models:** `Invitation` — token-based invitation (UUID token, expiry, status tracking)

Invitation flow: HQ admin or IPA admin sends invitation → email with token link → recipient registers via `/dashboard/invitations/register/<token>/`

---

### `media_app` — File & Media Management

**Models:** `MediaFolder`, `MediaFile`

Backed by Cloudinary. `resource_type="image"` for images, `resource_type="raw"` for PDFs/documents. Validates MIME types on upload.

---

### `waiis` — WAIIS Data Portal

West Africa Investment Intelligence System — data submission and analytics.

**Models:** `WaiisDataSubmission`, `WaiisSectorData`, `WaiisSourceCountryData`, `WaiisDataAudit`, `WaiisAnalyticsCache`, `WaiisDataExport`

Status: Models and migrations exist. UI/views are partially built.

---

### `notifications` — In-App Notifications

No migrations (abstract/signal-based). Provides notification infrastructure for the dashboard.

---

## 5. Environment Setup — Local (venv)

### Prerequisites
- Python **3.12** (project targets 3.10 but 3.12 works; **3.14 does NOT** — Pillow 10.2.0 is incompatible)
- Git

### Steps

```bash
# 1. Clone
git clone https://github.com/Festorah/ipawas.git
cd "ipawas project"   # note: folder name has a space

# 2. Create virtualenv with Python 3.12
python3.12 -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env — minimum required fields:
#   SECRET_KEY=<any random 50-char string>
#   DJANGO_ENV=dev
#   DATABASE_URL=sqlite:///db.sqlite3

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Seed data (optional — large dataset)
python manage.py shell < comprehensive_populate_ipawas.py

# 8. Run dev server
python manage.py runserver
```

Open: http://127.0.0.1:8000

---

## 6. Environment Setup — Docker

Docker is the recommended local setup — avoids Python version issues entirely.

### Prerequisites
- Docker Desktop installed and running

### Steps

```bash
# 1. Create the docker env file (already exists at .env.docker — not committed)
# If missing, copy and edit:
cp .env.example .env.docker
# Change DATABASE_URL and REDIS_URL to point to Docker service names:
#   DATABASE_URL=postgres://ipawas:ipawas@db:5432/ipawas
#   REDIS_URL=redis://redis:6379/1

# 2. Build and start all services
docker compose up --build

# First run automatically:
# - Starts PostgreSQL (db) and Redis containers
# - Runs python manage.py migrate
# - Runs python manage.py collectstatic --noinput
# - Starts Django dev server on port 8000

# 3. Create superuser (separate terminal)
docker compose exec web python manage.py createsuperuser

# 4. Access
# App:     http://localhost:8000
# Django Admin: http://localhost:8000/admin/
```

### Docker Services

| Service | Image | Port |
|---|---|---|
| `web` | Built from Dockerfile (Python 3.10-slim) | 8000 |
| `db` | postgres:15-alpine | 5432 |
| `redis` | redis:7-alpine | 6379 |
| `worker` | Same image as web | — |

### Known Fixed Issues
- `libgdk-pixbuf2.0-0` was renamed to `libgdk-pixbuf-xlib-2.0-0` in Debian trixie — Dockerfile uses the correct name

---

## 7. Environment Setup — Heroku Production

**App name:** `ipawas`  
**Region:** US  
**Stack:** heroku-24 (Python 3.10.13)

### Required Heroku Config Vars

```bash
heroku config --app ipawas
```

| Variable | Value | Notes |
|---|---|---|
| `DJANGO_ENV` | `prod` | Must be exactly `prod` — not `production` |
| `SECRET_KEY` | `<50-char random>` | Never commit this |
| `DATABASE_URL` | Auto-set by Heroku Postgres | Do not set manually |
| `REDIS_URL` | Auto-set by Heroku Redis | Do not set manually |
| `ALLOWED_HOSTS` | `ipawas.org,www.ipawas.org` | |
| `CSRF_TRUSTED_ORIGINS` | `https://ipawas.org,https://www.ipawas.org` | |
| `CLOUDINARY_CLOUD_NAME` | `<your cloud name>` | |
| `CLOUDINARY_API_KEY` | `<key>` | |
| `CLOUDINARY_API_SECRET` | `<secret>` | |
| `CONTACT_EMAIL` | `infodesk@ipawas.org` | |
| `EMAIL_HOST_USER` | SMTP user | |
| `EMAIL_HOST_PASSWORD` | SMTP password | |

### Heroku Addons

```bash
# PostgreSQL — standard plan
heroku addons --app ipawas
# Should show: heroku-postgresql and heroku-redis

# If Redis is missing:
heroku addons:create heroku-redis:mini --app ipawas
```

### Post-Deploy Steps

After merging to `main` and Heroku auto-deploying:

```bash
# 1. Run migrations (ALWAYS after a deploy that adds migrations)
heroku run python manage.py migrate --app ipawas

# 2. Static files — handled automatically by bin/post_compile during build
# If static files are missing (500 on CSS/JS):
heroku run python manage.py collectstatic --noinput --app ipawas
```

### Deployment Flow

1. Push to `main` branch (or merge PR to main)
2. Heroku detects the push, runs Python buildpack
3. `bin/post_compile` runs `collectstatic` during build (static files baked into slug)
4. Gunicorn starts: `web: gunicorn config.wsgi --log-file -`
5. Celery worker starts: `worker: celery -A config worker --loglevel=info --concurrency=2`
6. **Manually run:** `heroku run python manage.py migrate --app ipawas`

> ⚠️ **Known gap:** There is no `release` phase in the `Procfile`. Migrations must be run manually after every deploy. A permanent fix is to add `release: python manage.py migrate` to the Procfile.

---

## 8. Configuration & Environment Variables

### Settings Selection (`config/settings/__init__.py`)

```python
env = os.environ.get("DJANGO_ENV", "dev").lower()
if env == "prod":
    from .prod import *
elif env == "test":
    from .test import *
else:
    from .dev import *   # default
```

**Critical:** `DJANGO_ENV` must be set to exactly `"prod"` on Heroku. If it's unset or set to anything else, `dev.py` loads with `DEBUG=True` and no production hardening.

### Key Settings Summary

| Setting | dev.py | prod.py |
|---|---|---|
| `DEBUG` | `True` | `False` |
| `DATABASE_URL` | SQLite (default) | Heroku Postgres |
| `REDIS_URL` | Optional (falls back to LocMemCache) | Required (Heroku Redis) |
| `STATIC_ROOT` | `staticfiles/` | `staticfiles/` (baked in slug) |
| `EMAIL_BACKEND` | Console (print to terminal) | SMTP (Mailjet) |
| `SECURE_SSL_REDIRECT` | False | True |
| `DEBUG_PROPAGATE_EXCEPTIONS` | Not set | **TEMPORARY: True** (remove after /dashboard bug fixed) |

### Cache Configuration

Redis cache with automatic fallback:
```python
if _REDIS_URL:
    CACHES = {"default": {"BACKEND": "...redis.RedisCache", "LOCATION": _REDIS_URL}}
else:
    CACHES = {"default": {"BACKEND": "...LocMemCache"}}  # fallback for local dev
```

### Celery / Redis

Celery broker and result backend both use `REDIS_URL`. TLS (`rediss://`) is handled automatically with `ssl_cert_reqs=CERT_NONE` appended for Heroku Redis.

---

## 9. CI/CD Pipeline

> ⚠️ **Status:** GitHub Actions workflow files exist on the `ci-cd-and-tests` branch but have NOT been merged to `main` yet. The pipeline is not active on the main branch.

### Once merged, the pipeline will be:

**`ci.yml`** — Runs on every push to every branch and on PRs to main:
1. **Lint** — flake8, black (format check), isort
2. **Test** — pytest with PostgreSQL and Redis services, 60% coverage gate
3. **Security** — bandit
4. **Django check** — `manage.py check --deploy`

**`cd.yml`** — Runs only on pushes to `main`:
1. Deploys to Heroku app `ipawas` using `akhileshns/heroku-deploy@v3.13.15`

### Required GitHub Secrets (not yet added)

Go to GitHub → Repo → Settings → Secrets → Actions and add:

| Secret | Value |
|---|---|
| `HEROKU_API_KEY` | From: `heroku auth:token` |
| `HEROKU_EMAIL` | Your Heroku account email |

### Branch Protection (not yet configured)

Go to GitHub → Repo → Settings → Branches → Add rule for `main`:
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- Select CI checks: lint, test, security, django-check

---

## 10. User Testing Feedback — Full Issue Registry

The following issues were identified during user testing. They are organized by category with their current status.

---

### CATEGORY 1: Critical Issues

| # | Issue | Status |
|---|---|---|
| C1 | **Bad merge** — leadership page, ECOWAS page, and IPA profile pages were missing after a failed git merge (index write failed silently) | ✅ FIXED — recovered via git reflog, recreated `good-main` branch, force-pushed |
| C2 | **Favicon missing** — browser tab showed default icon | ✅ FIXED — `<link rel="icon">` added to `core/templates/core/new_base.html` |
| C3 | **Member states hub slow** — N+1 query: each member state in the loop re-queried sectors | ✅ FIXED — `prefetch_related("sectors__sector")` + Python-side filtering |
| C4 | **Heroku app crash on start** — `REDIS_URL` and `CELERY_BROKER_URL` pointed to localhost, crashing in production | ✅ FIXED — provisioned `heroku-redis:mini`, removed stale localhost config vars |
| C5 | **No custom error pages** — raw Django 500/404 showing to users | ✅ FIXED — created `core/templates/core/errors/404.html`, `500.html`, `403.html` with IPAWAS branding |
| C6 | **Dashboard HQ invitations** — `NoReverseMatch` on `/dashboard/hq/invitations/` because template used `dashboard:country:invitations:create` for HQ admins who have no `member_state` context | ✅ FIXED — conditional URL logic in template: HQ uses `dashboard:hq:invitations:create`, IPA staff uses `dashboard:country:invitations:create` |

---

### CATEGORY 2: Navigation Issues

| # | Issue | Status |
|---|---|---|
| N1 | Programs nav link — `href=""` (empty) | ✅ FIXED — changed to `{% url 'programs:hub' %}` |
| N2 | 15+ empty `href=""` footer links — Partnerships, Investment Guide, Opportunities, Country Profiles, Success Stories, Knowledge Hub, WAIIS Data Portal, Programs, Media Center, Events, Newsletter, IPA Portal, Privacy Policy, Terms of Use, Sitemap | ✅ FIXED — all wired to correct URL names |
| N3 | No global search in navbar | ✅ FIXED — search form added pointing to `{% url 'knowledge_hub:search' %}` |
| N4 | Programs section entirely unreachable (404) — URL include was missing from `core/urls/__init__.py` | ✅ FIXED — added `path("programs/", include(...))` |
| N5 | `core/urls/programs.py` broken relative import — `from . import views` tried to import from `core/urls/views` (non-existent) | ✅ FIXED — changed to `from core.views import programs as views` |
| N6 | URL slug param mismatch — `path("<slug:slug>/apply/", ...)` but function signature uses `program_slug` | ✅ FIXED — changed to `<slug:program_slug>` |

---

### CATEGORY 3: Interactive Map Issues

| # | Issue | Status |
|---|---|---|
| M1 | Map does not highlight member states on hover | 🔲 PENDING |
| M2 | Clicking a country on the map does not navigate to its profile | 🔲 PENDING |
| M3 | Map tooltip shows raw country code instead of formatted country name | 🔲 PENDING |
| M4 | Map is not responsive on mobile devices | 🔲 PENDING |

**Location:** `static/js/` (Leaflet.js), GeoJSON at `static/geo/cape-verde.geojson` (and similar files for other countries)

---

### CATEGORY 4: CMS Issues

| # | Issue | Status |
|---|---|---|
| CMS1 | News article editor (HQ dashboard) — rich text editor not saving content blocks correctly | 🔲 PENDING |
| CMS2 | Image upload in news editor — Cloudinary integration needs validation feedback in UI | 🔲 PENDING |
| CMS3 | Published/draft toggle on news articles — status not persisting | 🔲 PENDING |
| CMS4 | Media library — folder creation failing silently in some cases | 🔲 PENDING |

---

### CATEGORY 5: Search & Filters Issues

| # | Issue | Status |
|---|---|---|
| S1 | Knowledge hub search — returns results but relevance ranking is poor (no full-text search) | 🔲 PENDING |
| S2 | Member states filter API (`/members/api/filter/`) — language filter not working | 🔲 PENDING |
| S3 | Opportunities filter — sector filter not clearing when switching countries | 🔲 PENDING |
| S4 | Search results page missing pagination | 🔲 PENDING |

---

### CATEGORY 6: Forms Issues

| # | Issue | Status |
|---|---|---|
| F1 | Contact form (`/about/contact/`) crashed with `AttributeError: settings has no attribute CONTACT_EMAIL` | ✅ FIXED — added `CONTACT_EMAIL = config("CONTACT_EMAIL", default="infodesk@ipawas.org")` to `base.py`; `ContactFormView.form_valid()` uses `getattr(settings, "CONTACT_EMAIL", settings.DEFAULT_FROM_EMAIL)` |
| F2 | Investor inquiry form — no confirmation email sent to investor after submission | 🔲 PENDING |
| F3 | Application forms for Programs — non-functional (Programs section silenced, see §14) | ⏸️ DEFERRED |
| F4 | Onboarding form — step validation not enforced | 🔲 PENDING |

---

### CATEGORY 7: Performance / Technical Issues

| # | Issue | Status |
|---|---|---|
| P1 | N+1 queries on member states hub — **resolved**, see C3 above | ✅ FIXED |
| P2 | No caching on statistics API — expensive aggregation query on every request | ✅ FIXED — `CacheService.get_or_set_statistics()` with 24h TTL |
| P3 | Member state detail page re-fetched on every request | ✅ FIXED — `CacheService.get_or_set_member_state(slug)` |
| P4 | `staticfiles/` directory was committed to git (hundreds of binary files in repo) | ✅ FIXED — added `/staticfiles` to `.gitignore`, removed from tracking |
| P5 | Static files returning 500 after fresh Heroku deploy | ✅ FIXED — `bin/post_compile` runs `collectstatic` during build phase |
| P6 | `logs/` directory missing on Heroku causing `RotatingFileHandler` to silently fail | ✅ FIXED — `logs/.gitkeep` committed |
| P7 | Redis TLS (`rediss://`) — Celery crashing in production with SSL verification error | ✅ FIXED — `ssl_cert_reqs=CERT_NONE` appended to `rediss://` URLs |
| P8 | Celery result backend was set to `django-db` — required `django-celery-results` (not installed) | ✅ FIXED — changed to Redis result backend |
| P9 | Cloudinary defaults — missing env vars causing crash on startup | ✅ FIXED — safe defaults with empty string fallback |

---

### CATEGORY 8: Content Issues

| # | Issue | Status |
|---|---|---|
| CT1 | Leadership page — content exists but some profiles lack photos | 🔲 PENDING |
| CT2 | Member state profiles — several countries have incomplete economic data | 🔲 PENDING |
| CT3 | Success stories — most member states have no success stories entered | 🔲 PENDING |
| CT4 | FDI data points — incomplete historical data for many member states | 🔲 PENDING |
| CT5 | Events section — no upcoming events listed | 🔲 PENDING |
| CT6 | WAIIS data portal — no real data submitted yet | 🔲 PENDING |

---

### CATEGORY 9: Enhancements

| # | Enhancement | Status |
|---|---|---|
| E1 | Internationalization (i18n) — French and Portuguese translations exist on `feat_localization` branch | 🔲 NOT MERGED |
| E2 | Programs section — build out `Program`, `ProgramCategory`, `Applicant`, `Faculty` models when institution is ready | ⏸️ DEFERRED |
| E3 | WAIIS data portal — complete the data submission and analytics UI | 🔲 PENDING |
| E4 | Email notifications — Mailjet integration for invitation emails | 🔲 PARTIAL |
| E5 | Two-factor authentication (2FA) — `django-otp` and `qrcode` are installed but UI not wired | 🔲 PENDING |
| E6 | Sentry error tracking — SDK installed, configure `SENTRY_DSN` env var | 🔲 PENDING (easy) |
| E7 | Heroku `release` phase for automatic migrations | 🔲 PENDING (easy — add one line to Procfile) |
| E8 | Branch protection rules on GitHub (require CI before merge to main) | 🔲 PENDING |

---

## 11. What Has Been Done — Detailed Change Log

### Phase 1 — Critical Issue Fixes (merged to `main`)

**Commit `3928f73`** — Fix all 8 critical issues from user testing:
- Recovered missing pages (leadership, ECOWAS profiles, IPA profiles) via git reflog recovery after a bad merge where `git merge` silently wrote 0 files due to index corruption
- Added favicon `<link rel="icon">` to base template
- Fixed `MemberStatesHubView` N+1 — added `prefetch_related("sectors__sector")`, replaced per-iteration `.filter()` DB calls with Python-side filtering on prefetched data
- Added `CacheService` with 24h TTL for statistics and member state detail pages
- Created `CacheService.get_or_set_statistics()` and `CacheService.get_or_set_member_state()`
- Implemented `ALLOWED_IMAGE_TYPES` validation for file uploads
- Set `FILE_UPLOAD_MAX_MEMORY_SIZE = 10MB` and `DATA_UPLOAD_MAX_MEMORY_SIZE = 50MB`

**Commit `fbafab1`** — Redis/Heroku crash fix + custom error pages:
- Provisioned `heroku-redis:mini` addon on Heroku
- Removed stale `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` config vars pointing to localhost
- Made cache config resilient: falls back to `LocMemCache` if `REDIS_URL` not set
- Created custom error pages: `core/templates/core/errors/404.html`, `500.html`, `403.html`
- Registered custom error handlers in `config/urls.py` and `core/views/errors.py`

**Commit `6068181`** — Dashboard invitations `NoReverseMatch` fix:
- Fixed `dashboard/templates/dashboard/hq_admin/invitations/list.html` — HQ admins use `dashboard:hq:invitations:create`, IPA staff use `dashboard:country:invitations:create`

**Commits `9a43193`, `4d5e5cf`, `f23d38c`** — Heroku startup stability:
- Changed Celery result backend from `django-db` to Redis
- Added `ssl_cert_reqs=CERT_NONE` for Heroku's `rediss://` TLS URLs
- Fixed Cloudinary initialization defaults to prevent crash on missing env vars

---

### Phase 2 — CI/CD & Test Suite (on `ci-cd-and-tests` branch — not yet merged)

**Commit `e1dd3ae`**:
- Created `.github/workflows/ci.yml` — 4 jobs: lint (flake8/black/isort), test (pytest + PostgreSQL + Redis), security (bandit), django-check
- Created `.github/workflows/cd.yml` — deploys to Heroku on `main` push
- Created `config/settings/test.py` — `DummyCache`, SQLite `:memory:`, MD5 hasher, locmem email, eager Celery
- Created `pytest.ini` with `DJANGO_SETTINGS_MODULE = config.settings.test`
- Added `test` branch to `config/settings/__init__.py`
- Created `tests/factories.py` — Factory Boy factories for all major models
- Created test files:
  - `tests/test_members_models.py` — 20+ model tests
  - `tests/test_members_services.py` — service layer tests
  - `tests/test_members_views.py` — view tests including N+1 query bound checks
  - `tests/test_dashboard_views.py` — auth guards, URL regression tests
  - `tests/test_accounts.py` — user model, login flow
  - `tests/test_error_pages.py` — 404/500/403 status codes
  - `tests/test_cache_resilience.py` — cache backend smoke tests

---

### Phase 3 — Functionality Fixes (on `fix-functionality-issues` branch — not yet merged)

**Commit `4ee10cb`** — All 5 functionality categories from user testing:
- **Navigation:**
  - Fixed Programs nav link from empty `href=""` to `{% url 'programs:hub' %}`
  - Fixed 15+ empty footer links across the base template
  - Added global search bar to navbar pointing to `{% url 'knowledge_hub:search' %}`
  - Added missing programs URL include to `core/urls/__init__.py`
  - Fixed broken relative import in `core/urls/programs.py`
  - Fixed URL slug param mismatch (`<slug:slug>` → `<slug:program_slug>`)
- **Forms:**
  - Fixed `ContactFormView` crash — added `CONTACT_EMAIL` to `base.py`, updated view to use `getattr` fallback
- **Settings:**
  - Added `CONTACT_EMAIL = config("CONTACT_EMAIL", default="infodesk@ipawas.org")` to `base.py`

**Commit `b575eb2`** — Docker support + programs import fix:
- Created `Dockerfile` (Python 3.10-slim with WeasyPrint system libs)
- Created `docker-compose.yml` (web + db + redis + worker with healthchecks)
- Created `.env.docker` template with Docker service hostnames
- Fixed `core/views/programs.py` — removed phantom imports (`from .forms import ProgramApplicationForm`, `from .models import Program, ...`) that crashed the server on startup

**Commit `15c1be0`** — Heroku collectstatic + DATABASE_URL:
- Created `bin/post_compile` — runs `collectstatic` during Heroku build so static files are baked into the slug
- Fixed `prod.py` to use `dj_database_url.config()` for database (reads `DATABASE_URL` from Heroku env)

**Commit `3276072`** — Production logging improvements:
- `prod.py` now has a clean console-only `LOGGING` config that overrides `base.py`'s file-handler config
- Format: `[{levelname}] {name} {message}` — clearly shows logger name and full tracebacks in Heroku logs

**Commit `2beb5e3`** — Migration cleanup:
- Removed incorrect `initial=True` flags from `accounts/0002_initial.py` and `core/0002_initial.py` (these are NOT initial migrations but were mistakenly marked as such)

**Commit `8f5b53a`** — Logs directory:
- Committed `logs/.gitkeep` so the directory exists on Heroku (prevents `RotatingFileHandler` from failing silently)

**Commit `079cb0a`** — Dashboard routing fix:
- `dashboard/views/routing.py` — replaced `redirect("accounts:profile_incomplete")` (non-existent URL) with `redirect("accounts:profile")`

**Commit `fb69818`** — Missing migration:
- Committed `dashboard/migrations/0002_alter_ipadashboardactivity_action_type.py` — this file existed locally but was never committed, causing Django to warn about unapplied model changes on every Heroku deploy

**Commit `2275851`** — Temporary debug:
- Added `DEBUG_PROPAGATE_EXCEPTIONS = True` to `prod.py` temporarily to expose the full `/dashboard` 500 traceback in Heroku logs
- **MUST BE REMOVED** after the bug is identified and fixed

---

## 12. Current Production Bugs (UNRESOLVED)

### 🔴 BUG 1: `/dashboard` returns HTTP 500

**Symptom:** Any logged-in user navigating to `/dashboard` or `/dashboard/` gets a 500 error page.

**What has been investigated and fixed (but 500 persists):**
1. ✅ `accounts:profile_incomplete` — phantom URL in routing.py → replaced with `accounts:profile`
2. ✅ `dashboard/0002` migration missing → committed
3. ✅ `logs/` directory missing → fixed
4. ✅ `RotatingFileHandler` hiding tracebacks → improved prod logging

**Current debug state:**
`DEBUG_PROPAGATE_EXCEPTIONS = True` has been added to `prod.py` on the `fix-functionality-issues` branch. Once this branch is merged and deployed, hitting `/dashboard` will print the **full Python traceback** to Heroku logs instead of silently returning 500.

**How to diagnose after merge:**
```bash
# Terminal 1 — watch live logs
heroku logs --tail --app ipawas

# Terminal 2 (or browser) — trigger the error
# Navigate to https://ipawas.org/dashboard while logged in
```

Look for `Traceback (most recent call last):` in the logs. The last line will be the specific error.

**Likely candidates** (to investigate with the traceback):
- An import in `dashboard/views/hq_admin/__init__.py` that fails lazily (URL conf loads views at first request)
- A missing template for the HQ dashboard view
- A database query that fails due to a missing column or unapplied migration
- A middleware issue specific to authenticated requests

**After fixing:** Remove `DEBUG_PROPAGATE_EXCEPTIONS = True` from `prod.py`.

---

### 🟡 BUG 2: Static files 500 on fresh deploy (intermittent)

**Symptom:** `/static/css/home.css` and other static files return 500 immediately after a fresh Heroku deploy.

**Root cause (fixed):** `staticfiles/` was not being generated during build — only available after manual `collectstatic`.

**Fix applied:** `bin/post_compile` now runs `collectstatic` during the Heroku build phase. This was committed in `15c1be0`.

**If it still happens after merge:** Run manually:
```bash
heroku run python manage.py collectstatic --noinput --app ipawas
```

---

### 🟡 BUG 3: `dashboard` migration warning on every deploy

**Symptom:** `heroku run python manage.py migrate` says:
```
Your models in app(s): 'dashboard' have changes that are not yet reflected in a migration
```

**Root cause (fixed):** `dashboard/migrations/0002_alter_ipadashboardactivity_action_type.py` existed locally but was never committed to git.

**Fix applied:** Migration committed in `fb69818`. Once merged and `heroku run python manage.py migrate` is run, the warning disappears.

---

## 13. Pending Tasks — Priority Order

### 🔴 Immediate (Blocking Production)

1. **Merge `fix-functionality-issues` PR to main**
   - Contains all Phase 3 fixes including the dashboard routing fix, logging improvements, missing migration, Docker setup
   - After merge: `heroku run python manage.py migrate --app ipawas`

2. **Diagnose and fix `/dashboard` 500**
   - After merge, check `heroku logs --tail --app ipawas` while hitting `/dashboard`
   - Full traceback will be visible thanks to `DEBUG_PROPAGATE_EXCEPTIONS = True`
   - Fix the underlying cause, then **remove `DEBUG_PROPAGATE_EXCEPTIONS` from `prod.py`**

3. **Add `release` phase to Procfile**
   - Edit `Procfile`, add: `release: python manage.py migrate`
   - This eliminates the manual migration step after every deploy

---

### 🟠 Short-term

4. **Merge `ci-cd-and-tests` PR to main**
   - Activates GitHub Actions CI/CD pipeline

5. **Add GitHub Secrets for CD pipeline**
   - `HEROKU_API_KEY` — get from: `heroku auth:token`
   - `HEROKU_EMAIL` — your Heroku account email
   - Go to: GitHub Repo → Settings → Secrets and variables → Actions

6. **Configure GitHub branch protection for `main`**
   - Require CI checks to pass before merging
   - GitHub Repo → Settings → Branches → Add rule for `main`

7. **Configure Sentry DSN**
   - `heroku config:set SENTRY_DSN=https://... --app ipawas`
   - Immediately gives error tracking with email alerts

---

### 🟡 Medium-term (Feature Completeness)

8. **Fix Interactive Map (`/` homepage)**
   - Countries should be clickable and link to `/members/<slug>/`
   - Hover tooltip should show country name and key stat
   - Review `static/js/` Leaflet.js code and GeoJSON data

9. **Fix CMS functionality**
   - News article rich text editor (save content blocks)
   - Image upload with Cloudinary feedback
   - Draft/publish workflow

10. **Fix Search & Filters**
    - Knowledge hub search — consider PostgreSQL full-text search (`SearchVector`)
    - Member state language filter
    - Opportunities sector filter reset

11. **Complete form fixes**
    - Investor inquiry confirmation email
    - Onboarding step validation

12. **Content population**
    - Complete member state profiles (economic data)
    - Add success stories for at least 5 member states
    - FDI data points for all member states
    - Events for upcoming ECOWAS activities

---

### 🟢 Long-term / Future

13. **Programs section** — When the institution is ready to activate programs:
    - Create models: `Program`, `ProgramCategory`, `Applicant`, `Faculty`, `ProgramApplication`
    - Run `python manage.py makemigrations` and `migrate`
    - Update `core/views/programs.py` to use ORM queries (replace static empty context)
    - Restore Programs nav link

14. **WAIIS Data Portal** — Complete the data submission UI and analytics dashboard

15. **Internationalization** — Merge `feat_localization` branch (French + Portuguese translations already done)

16. **Two-factor authentication** — `django-otp` is installed; wire up the UI in account settings

17. **Paystack payment integration** — For program registration fees (env vars already in `.env.example`)

---

## 14. Programs Section — Intentionally Silenced

The Programs section (`/programs/`) was **deliberately disabled** because IPAWAS does not currently operate formal programs.

### What was done

`core/views/programs.py` was rewritten to:
- Remove all phantom imports (`from .forms import ProgramApplicationForm`, `from .models import Program, ProgramCategory, Applicant, Faculty`) — these models **do not exist** in the database
- All view functions return static/empty context (no DB queries)
- `submit_application()` returns HTTP 503 with a JSON message "Program applications are not yet open"

The URLs still exist (routes are registered) but pages render with empty content.

### What does NOT exist (and must be created before reactivating)

- `Program` model and migration
- `ProgramCategory` model
- `Applicant` model
- `Faculty` model
- `ProgramApplicationForm` form class

### How to reactivate when ready

```bash
# 1. Create models in a new app or add to core/models.py
# 2. Create and run migrations
python manage.py makemigrations
python manage.py migrate

# 3. Create ProgramApplicationForm in core/forms.py

# 4. Update core/views/programs.py to use ORM queries
# 5. Restore Programs link in navbar (core/templates/core/new_base.html)
```

---

## 15. Branch Strategy

| Branch | Status | Purpose |
|---|---|---|
| `main` | ✅ Active — auto-deploys to Heroku | Production branch |
| `fix-functionality-issues` | 🔲 PR open — **MERGE THIS FIRST** | All Phase 3 fixes + Docker + migration |
| `ci-cd-and-tests` | 🔲 PR open | GitHub Actions CI/CD + test suite |
| `feat_localization` | 🔲 Exists — not reviewed | French + Portuguese i18n |

### Merge Order

1. Merge `fix-functionality-issues` → `main` first (fixes production crashes)
2. Merge `ci-cd-and-tests` → `main` second (activates automated testing)
3. Review `feat_localization` — test thoroughly before merging (i18n affects every template)

---

## 16. Key Files Reference

| File | Purpose |
|---|---|
| `config/settings/__init__.py` | Selects settings module based on `DJANGO_ENV` |
| `config/settings/base.py` | All shared settings (installed apps, middleware, cache, celery, logging) |
| `config/settings/prod.py` | Production overrides (DEBUG=False, Postgres, HTTPS) |
| `config/settings/dev.py` | Development overrides (DEBUG=True) |
| `config/urls.py` | Root URL conf — registers all apps + error handlers |
| `config/celery.py` | Celery app configuration |
| `core/templates/core/new_base.html` | **Master base template** — navbar, footer, favicons |
| `core/urls/__init__.py` | Core URL conf — homepage + all public section URLs |
| `core/views/errors.py` | Custom 404/500/403 handlers |
| `core/views/programs.py` | Programs views — currently silenced (static empty context) |
| `dashboard/views/routing.py` | Smart router — sends users to correct dashboard |
| `dashboard/urls/urls.py` | Dashboard URL conf — routes to hq/ or `<slug>/` |
| `members/services.py` | Business logic layer for member states (CacheService here) |
| `members/views.py` | Member state public views with N+1 fix and caching |
| `accounts/views.py` | Auth views — login redirects to correct dashboard by `user_type` |
| `bin/post_compile` | Heroku build hook — runs `collectstatic` during slug build |
| `Procfile` | Heroku process types (web + worker) |
| `comprehensive_populate_ipawas.py` | Full seed data script — run in Django shell |

---

## 17. Known Gotchas & Traps

1. **`DJANGO_ENV` must be exactly `"prod"`** — not `"production"`, not `"PROD"`. The `__init__.py` does a case-insensitive `.lower()` check but only for `"prod"`. If the env var is missing or wrong, `dev.py` loads silently.

2. **`staticfiles/` must not be in git** — it's large (~hundreds of files), changes on every `collectstatic` run, and causes noisy diffs. It's in `.gitignore`. Static files are baked into the Heroku slug via `bin/post_compile`.

3. **Python 3.10 only in production** — `runtime.txt` specifies `python-3.10.13`. Local dev works on 3.12. **Python 3.14 breaks `Pillow==10.2.0`** — do not use 3.14 for local dev.

4. **Programs models do not exist** — `Program`, `ProgramCategory`, `Applicant`, `Faculty` are referenced in old code comments and views but have **never been created**. Do not try to query them.

5. **`accounts:profile_incomplete` does not exist** — This URL name was referenced in `dashboard/views/routing.py` and caused a `NoReverseMatch` 500 on every dashboard visit. Fixed to `accounts:profile` in commit `079cb0a`.

6. **`dashboard/0002` was uncommitted** — The migration file existed locally but wasn't in git. Fixed in `fb69818`. Always run `git status` after `makemigrations` to ensure new files are staged.

7. **`DEBUG_PROPAGATE_EXCEPTIONS = True` is TEMPORARY** — Added to `prod.py` to diagnose the `/dashboard` 500. **Remove this line once the bug is fixed.** It bypasses Django's exception handling and returns raw error responses to users.

8. **Two separate `initial` migrations exist for `accounts` and `core`** — `0001_initial` and `0002_initial`. This is unusual (normally you only have one initial migration). They exist because models were split across two migration files. The `initial=True` flag was incorrectly set on `0002` migrations — fixed in `2beb5e3`.

9. **Heroku Redis TLS** — Heroku's Redis URL uses `rediss://` (double-s) for TLS. Django's Redis cache backend and Celery both need `ssl_cert_reqs=CERT_NONE` appended to work without certificate verification. This is handled automatically in `base.py`.

10. **Celery worker** — The `worker` process in `Procfile` must be running on Heroku for async tasks (email sending, invitation cleanup). On the free/eco tier, workers may not be enabled. Check: `heroku ps --app ipawas`.

11. **Login URL name** — `settings.LOGIN_URL = "accounts:login"` is a URL name, not a path. `LoginRequiredMixin` uses Django's `resolve_url()` which reverses this correctly. Do not change it to a path.

12. **`settings.LOGIN_REDIRECT_URL`** — Currently set to `"dashboard:country:overview"` in `base.py`. This URL requires a `member_state_slug` argument. Django's built-in `LoginView` (not used here — a custom `LoginView` is used instead) would fail trying to reverse this. The custom `LoginView._redirect_to_dashboard()` handles the redirect correctly by passing the slug.

---

## 18. Database Migrations Reference

### Migration Graph (dependency order)

```
auth/0001-0012 (Django built-in)
    └── core/0001_initial
    └── accounts/0001_initial
            └── members/0001_initial
                    └── accounts/0002_initial
                    └── core/0002_initial
                    └── waiis/0001_initial
                    └── dashboard/0001_initial
                    └── dashboard/0002_alter_ipadashboardactivity_action_type
                    └── opportunities/0001_initial
accounts/0001_initial
    └── accounts/0003-0005 (additional account fields)
core/0001_initial
    └── core/0003_publication_cover_media
    └── core/0004_publication_tags_topics
knowledge_hub/0001_initial
    └── knowledge_hub/0002_newsarticle_content_blocks_...
invitations/0001_initial
media_app/0001_initial
members/0001_initial
    └── members/0002_memberstateipa_corporate_tax_rate_...
    └── members/0003_ecowasleadershipposition_ipaleadership
```

### Applied on Heroku (as of March 2026)

All migrations are applied **except `dashboard/0002`** (fixed in `fb69818`, will apply after PR merge).

Run after every deploy that adds new migrations:
```bash
heroku run python manage.py migrate --app ipawas
```

---

## 19. Populating the Database (Seed Data)

Several population scripts exist in the root directory:

| Script | Contents |
|---|---|
| `comprehensive_populate_ipawas.py` | Full dataset — all member states, sectors, FDI data, news, opportunities |
| `populate_accounts.py` | Test users (admin + IPA staff per country) |
| `populate_core.py` | Sectors, partners, events |
| `populate_knowledge_hub.py` | News articles, resources, topics, tags |
| `populate_member_states.py` | Member state profiles (MemberStateIPA) |
| `populate_members_part1/2/3.py` | Split member state data |
| `populate_opportunities.py` | Investment opportunities |
| `populate_all.py` | Runs all scripts in sequence |

**Usage:**
```bash
# Run the comprehensive script (recommended for fresh setup)
python manage.py shell < comprehensive_populate_ipawas.py

# Or run individual scripts
python manage.py shell < populate_accounts.py
```

---

## 20. Test Suite

> ⚠️ **Status:** Test files exist on the `ci-cd-and-tests` branch but are **not on `main`** yet.

### Running Tests (after merging `ci-cd-and-tests`)

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_members_views.py -v
```

### Test Configuration

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_test.py
addopts = --tb=short -q
```

### Test Settings (`config/settings/test.py`)

- Database: SQLite `:memory:` (fast, no Postgres needed)
- Cache: `DummyCache` (no Redis needed)
- Password hasher: MD5 (fast)
- Email: `locmem` backend (captured in `mail.outbox`)
- Celery: `CELERY_TASK_ALWAYS_EAGER = True` (tasks run synchronously)
- Storage: `InMemoryStorage` (no filesystem writes)

### Test Files

| File | What it tests |
|---|---|
| `tests/factories.py` | Factory Boy factories for all major models |
| `tests/test_members_models.py` | MemberStateIPA, MemberStateSector, InvestorInquiry, SuccessStory, FDIDataPoint models |
| `tests/test_members_services.py` | MemberStateService, DataService, CacheService |
| `tests/test_members_views.py` | Hub (N+1 query bound), detail, inquiry, filter API, statistics API |
| `tests/test_dashboard_views.py` | Auth guards, sector CRUD `success_url`, URL resolution regressions |
| `tests/test_accounts.py` | User model, login flow, IPAUser profile |
| `tests/test_error_pages.py` | 404/500/403 status codes and template content |
| `tests/test_cache_resilience.py` | TLS Redis helper, cache backend smoke tests |

### Coverage Target

60% minimum coverage gate enforced in CI.

---

## Quick Reference — Most Urgent Commands

```bash
# Check what's deployed vs what's pending
git log --oneline main | head -5
git log --oneline fix-functionality-issues ^main | head -10

# After merging fix-functionality-issues to main:
heroku run python manage.py migrate --app ipawas

# Watch live logs for /dashboard traceback
heroku logs --tail --app ipawas

# Check running dynos
heroku ps --app ipawas

# Restart all dynos
heroku restart --app ipawas

# Check config vars
heroku config --app ipawas

# Run Django management command on Heroku
heroku run python manage.py <command> --app ipawas
```

---

*End of DEVELOPER_HANDOFF.md — for questions about specific implementation decisions, refer to the git commit messages which contain detailed explanations for each change.*
