"""
Management command: download_geoip_db

Downloads the MaxMind GeoLite2-Country.mmdb database file.
Run this once locally and on each Heroku release to keep geo-data current.

Usage:
    MAXMIND_LICENSE_KEY=your_key python manage.py download_geoip_db

Set MAXMIND_LICENSE_KEY as a Heroku config var and add to Procfile:
    release: python manage.py download_geoip_db
"""
import os
import tarfile
import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


DOWNLOAD_URL = (
    "https://download.maxmind.com/app/geoip_download"
    "?edition_id=GeoLite2-Country"
    "&license_key={key}"
    "&suffix=tar.gz"
)


class Command(BaseCommand):
    help = "Download the MaxMind GeoLite2-Country.mmdb database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--require-key",
            action="store_true",
            default=False,
            help="Exit with a non-zero status if MAXMIND_LICENSE_KEY is not set.",
        )

    def handle(self, *args, **options):
        license_key = os.environ.get("MAXMIND_LICENSE_KEY", "").strip()
        if not license_key:
            msg = (
                "MAXMIND_LICENSE_KEY environment variable is not set. "
                "Skipping GeoIP download. "
                "Get a free key at: https://www.maxmind.com/en/geolite2/signup"
            )
            if options["require_key"]:
                raise CommandError(msg)
            self.stdout.write(self.style.WARNING(msg))
            return

        geoip_dir: Path = settings.GEOIP_PATH
        geoip_dir.mkdir(parents=True, exist_ok=True)
        dest = geoip_dir / "GeoLite2-Country.mmdb"

        url = DOWNLOAD_URL.format(key=license_key)
        tar_path = geoip_dir / "GeoLite2-Country.tar.gz"

        self.stdout.write("Downloading GeoLite2-Country database...")
        try:
            urllib.request.urlretrieve(url, tar_path)
        except Exception as e:
            raise CommandError(f"Download failed: {e}")

        self.stdout.write("Extracting...")
        try:
            with tarfile.open(tar_path, "r:gz") as tar:
                for member in tar.getmembers():
                    if member.name.endswith(".mmdb"):
                        member.name = "GeoLite2-Country.mmdb"
                        tar.extract(member, path=geoip_dir)
                        break
        except Exception as e:
            raise CommandError(f"Extraction failed: {e}")
        finally:
            tar_path.unlink(missing_ok=True)

        self.stdout.write(self.style.SUCCESS(f"GeoLite2-Country.mmdb saved to {dest}"))
