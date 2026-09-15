# GeoIP Database

This directory holds the MaxMind GeoLite2-Country binary database used for
IP-based country detection on the homepage.

## Setup

1. Register for a free account at https://www.maxmind.com/en/geolite2/signup
2. Download **GeoLite2-Country.mmdb** from your MaxMind account dashboard
3. Place the file here: `geoip/GeoLite2-Country.mmdb`

The `.mmdb` file is excluded from git (listed in `.gitignore`) because it is
updated monthly and is ~6MB. On Heroku, provision it via a release phase command
or download it during the build using your MaxMind license key.

## Heroku deployment

Add these config vars to Heroku and add a release-phase script to fetch the DB:

    MAXMIND_LICENSE_KEY=your_key_here

Release phase command in `Procfile`:
    release: python manage.py download_geoip_db
