# ipawas

A Django 5.1 project with modern best practices, split settings, Docker support, and automated code quality checks.

## 🚀 Quick Start

### Local Development (Recommended for beginners)

1. **Activate virtual environment:**
```bash
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

2. **Run migrations:**
```bash
python manage.py migrate
```

3. **Create superuser:**
```bash
python manage.py createsuperuser
```

4. **Start development server:**
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

### Docker Development

```bash
docker-compose up --build
```

## 📁 Project Structure

```
ipawas/
├── config/
│   ├── settings/
│   │   ├── __init__.py      # Smart settings loader
│   │   ├── base.py          # Shared settings
│   │   ├── dev.py           # Development settings
│   │   └── prod.py          # Production settings
│   ├── urls.py
│   └── wsgi.py
├── templates/               # HTML templates
├── static/                  # CSS, JS, images
├── media/                   # User uploads
├── venv/                    # Virtual environment
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment file
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── docker-compose.yml       # Docker configuration
└── manage.py
```

## 🔧 Configuration

Settings are split into:
- **base.py**: Shared settings
- **dev.py**: Development (uses SQLite)
- **prod.py**: Production (uses PostgreSQL)

Control which settings to use with the `DJANGO_ENV` environment variable:
```bash
export DJANGO_ENV=dev   # Use development settings
export DJANGO_ENV=prod  # Use production settings
```

## 🗄️ Database

**Development**: Uses SQLite (no setup needed)

**Production**: Configure PostgreSQL in `.env`:
```env
DJANGO_ENV=prod
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

## 🧪 Testing

```bash
pytest
pytest --cov  # With coverage report
```

## 📝 Code Quality

Pre-commit hooks are installed automatically. They run:
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting

Run manually:
```bash
black .
isort .
flake8 .
```

## 🐳 Docker Commands

```bash
# Start services
docker-compose up

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

## 📦 Adding Apps

```bash
python manage.py startapp myapp
```

Then add to `INSTALLED_APPS` in `config/settings/base.py`

## 🚢 Deployment

1. Set `DJANGO_ENV=prod` in production environment
2. Update `.env` with production values
3. Run migrations: `python manage.py migrate`
4. Collect static files: `python manage.py collectstatic`
5. Use gunicorn: `gunicorn config.wsgi:application`

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)

## 📄 License

MIT License - Feel free to use this template for your projects!
