#!/usr/bin/env sh

gunicorn --config="python:techlock.auth_service.gunicorn" techlock.auth_service.app:app
