#!/usr/bin/env sh

gunicorn --config="python:techlock.compas.gunicorn" techlock.compas.app:app
