#!/usr/bin/env sh

echo "Auth0 domain=$AUTH0_DOMAIN"

gunicorn --config="python:techlock.user_management_service.gunicorn" techlock.user_management_service.app:app
