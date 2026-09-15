#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py loaddata datadump.json

# One-time staff account bootstrap: only runs when DJANGO_SUPERUSER_USERNAME
# is set (e.g. on the very first deploy). Django's --noinput reads
# DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD from the environment. `|| true`
# keeps later deploys from failing once the account already exists — there's
# no shell access on Render's free tier to run this by hand.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser --noinput || true
fi