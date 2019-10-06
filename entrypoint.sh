#!/usr/bin/env sh

gunicorn --config="python:techlock.user_management_service.gunicorn" techlock.user_management_service.app:app
