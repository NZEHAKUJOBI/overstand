release: python manage.py migrate --noinput && python manage.py download_geoip_db
web: gunicorn config.wsgi --config gunicorn.conf.py --preload --workers 3 --timeout 60 --max-requests 1200 --max-requests-jitter 100 --log-file -
worker: celery -A config worker --loglevel=info --concurrency=2
beat: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
