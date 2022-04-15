#!/usr/bin/env sh

gunicorn --config="python:techlock.compass.gunicorn" techlock.compass.app:app
