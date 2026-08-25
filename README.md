# Mobile Shop Project

A Django storefront for browsing and selling mobile phones, laptops, and tablets. It includes a Django REST API, a FastAPI stock service, and a Flask PDF invoice service.

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

5. Start the Django site:

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
- Flask invoice API: <http://127.0.0.1:8002/apidocs/>

## Useful commands

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check
```

The public Django API and schema documentation are available at `/api/`, `/api/schema/`, and `/api/docs/`.

## Configuration

Never commit `.env`. Use `.env.example` as the template. In production, provide a strong `SECRET_KEY`, set `DEBUG=False`, configure `ALLOWED_HOSTS`, and use a real email backend. Generated media and invoice PDFs are intentionally ignored by Git.
