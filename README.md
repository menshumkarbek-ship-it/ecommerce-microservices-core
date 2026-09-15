# Mobile Shop Project

A Django storefront for browsing phones, laptops, and tablets. This is a **view-only catalog**: visitors can search, filter, and inspect product specifications, but there is no cart, checkout, or customer account system. Catalog management (adding/editing products) is restricted to staff accounts via Django's own admin login.

It includes a Django REST API and a FastAPI stock-check service for read-only inventory data.

## Requirements

- Python 3.12+
- Docker Desktop and Docker Compose (recommended for PostgreSQL and Redis)
- Git

## Local setup

1. Create and activate a virtual environment:

   ```powershell
   py -3.12 -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and update the values for your environment.

4. Start PostgreSQL and Redis, then apply migrations and optionally seed the catalog:

   ```powershell
   docker compose up -d db redis
   python manage.py migrate
   python manage.py seed_db
   ```

5. Create a staff account so you can manage the catalog through `/admin/` and the "Manage Products" page:

   ```powershell
   python manage.py createsuperuser
   ```

6. Start the Django site:

   ```powershell
   python manage.py runserver
   ```

   Open <http://127.0.0.1:8000/>.

## Docker Compose

Run the full stack with:

```powershell
docker compose up --build
```

Services:

- Django storefront: <http://127.0.0.1:8000/>
- FastAPI stock API: <http://127.0.0.1:8001/docs>

## Useful commands

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check
```

The public Django API and schema documentation are available at `/api/`, `/api/schema/`, and `/api/docs/`.

## Configuration

Never commit `.env`. Use `.env.example` as the template. In production, provide a strong `SECRET_KEY`, set `DEBUG=False`, configure `ALLOWED_HOSTS`, and use a real email backend if you re-introduce transactional email in the future.
