FROM python:3.7-alpine3.10
LABEL maintainer_name="Michiel Vanderlee" maintainer_email="mvanderlee@changedynamix.io"

# Install packages that must be present at runtime
RUN apk add --no-cache \
    git \
    libpq \
    bash

EXPOSE 5000

ARG NEXUS_HOST

# Copy only requirements.txt so that we only execute the expensive dependency install when the dependencies actually change.
# This results in much faster build time, and we're not constantly pulling down packages.
COPY requirements.txt /requirements.txt

# Install package.
# This also installs build dependency packages needed for aegis-common, but removes them at the end to keep image size to a minimum.
RUN apk add --no-cache --virtual .build-deps \
        postgresql-dev \
        gcc \
        musl-dev \
        libffi-dev \
        libressl-dev \
    && pip install -r requirements.txt \
      --no-cache-dir \
      --extra-index-url "http://${NEXUS_HOST}/repository/pypi-hosted/simple/" \
      --trusted-host "${NEXUS_HOST}" \
    && apk del .build-deps

# Copy the app code, and install it without dependencies.
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir --no-dependencies .


ENTRYPOINT ["/app/entrypoint.sh"]
