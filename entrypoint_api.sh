#!/bin/bash

cd wd_api
python manage.py migrate --no-input
python manage.py collectstatic --no-input
gunicorn wd_api.wsgi:application --bind 0:8000