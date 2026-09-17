# Mobile Shop Project

A Django storefront for browsing phones, laptops, and tablets. This is a **view-only catalog**: visitors can search, filter, and inspect product specifications, but there is no cart, checkout, or customer account system. Catalog management (adding/editing products) is restricted to staff accounts via Django's own admin login.

It includes a read-only Django REST API for the catalog.

## Requirements

- Python 3.12 (pinned in `runtime.txt`; CI runs the same version)
- Docker Desktop and Docker Compose (recommended, for PostgreSQL)
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

4. Start PostgreSQL, then apply migrations and optionally seed the catalog:

   ```powershell
   docker compose up -d db
   python manage.py migrate
   python manage.py seed_db
   ```

5. Create a staff account so you can manage the catalog through the admin and the "Manage Products" page:

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
- PostgreSQL on port 5432

The Django admin is mounted at `ADMIN_URL` (default `system-console/`), not `/admin/`.
This keeps the default path scanners probe from returning anything, but it is obscurity
rather than a control — any protected page still redirects to the real login URL, so treat
the admin as publicly known and rely on strong credentials.

## Useful commands

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check
```

The public Django API and schema documentation are available at `/api/`, `/api/schema/`, and `/api/docs/`.

Tests also run automatically on every push and pull request to `main` (see `.github/workflows/ci.yml`),
against PostgreSQL and the Python version pinned in `runtime.txt`.

## Removing products is reversible

Removing a listing from **Manage Webpage** is how a sale gets recorded: it writes a `Sale` row
(a snapshot of the name, brand, category, catalog code and price at that moment, which is what the
monthly report reads) and then *soft*-deletes the product — the row and its photos are kept and
`deleted_at` is stamped instead.

The listing disappears from the storefront, the catalog and the API immediately, but it stays under
**Recently removed** on the management page for as long as it is among the 10 most recent removals.
Restoring it puts it back and deletes the sale it recorded, so the month's revenue is not left
inflated by a mis-click.

Because the row survives, a removed product keeps its slug and its per-category `#ID` reserved —
a replacement listing with the same name gets `-2` appended rather than colliding.

## Deploying safely

**Render auto-deploys from `main` by default**, which means a push migrates the production
database within minutes and CI finishes *alongside* the deploy rather than in front of it — a
red build does not stop the release.

To make tests an actual gate, turn off auto-deploy for the service in the Render dashboard and
add its Deploy Hook URL as a `RENDER_DEPLOY_HOOK` repository secret. The `deploy` job in
`.github/workflows/ci.yml` then fires the hook only after the tests pass, and stays skipped
(green) until you do both.

`build.sh` runs `migrate` against the production database on every deploy. There is no automatic
backup in front of it, so before shipping a migration that drops or alters a column:

1. **Take a backup.** `pg_dump "$DATABASE_URL" > backup-$(date +%F).sql`
2. **Verify it is non-empty** before relying on it: `wc -l backup-*.sql`
3. **Restore path**, if a migration goes wrong: `psql "$DATABASE_URL" < backup-YYYY-MM-DD.sql`
4. **Roll back one migration** without a full restore, when the migration is reversible:
   `python manage.py migrate shop <previous_migration_name>`

> Enable your host's own scheduled database backups as well — the commands above only help if
> someone remembers to run them. Check the retention window your plan actually provides; on free
> tiers it is often short or absent.

## Configuration

Never commit `.env`. Use `.env.example` as the template. In production, provide a strong `SECRET_KEY`, set `DEBUG=False`, configure `ALLOWED_HOSTS`, and use a real email backend if you re-introduce transactional email in the future.
