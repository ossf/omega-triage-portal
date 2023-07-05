#!/bin/sh

python manage.py makemigrations
python manage.py migrate
# run to test the collectstatic does not break anything
python manage.py collectstatic -n
# run to fully pull the static files
# python manage.py collectstatic
# mv . /opt/omega/static
