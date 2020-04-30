FROM python:3.7-slim-stretch
LABEL maintainer_name="Michiel Vanderlee" maintainer_email="mvanderlee@techlockinc.com"

# Install packages that must be present at runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      git \
      libpq5 \
      libstdc++ \
      bash \
      wait-for-it \
    && rm -rf /var/lib/apt/lists/

ENV prometheus_multiproc_dir=/app/multiproc-tmp
RUN mkdir -p /app/multiproc-tmp

EXPOSE 5000

ARG NEXUS_HOST
ARG NEXUS_USERNAME
ARG NEXUS_PASSWORD

# Copy only requirements.txt so that we only execute the expensive dependency install when the dependencies actually change.
# This results in much faster build time, and we're not constantly pulling down packages.
COPY requirements.txt /requirements.txt

# Install package.
# This also installs build dependency packages needed for techlock-common, but removes them at the end to keep image size to a minimum.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      libpq-dev \
      gcc \
      g++ \
    && pip install -r requirements.txt \
      --no-cache-dir \
      --extra-index-url "https://${NEXUS_USERNAME}:${NEXUS_PASSWORD}@${NEXUS_HOST}/repository/pypi-hosted/simple/" \
    && apt-get purge -y \
      libpq-dev \
      gcc \
      g++ \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/

# Copy the app code, and install it without dependencies.
COPY . /app
RUN chmod +x /app/*.sh
WORKDIR /app
RUN pip install --no-cache-dir --no-dependencies .


ENTRYPOINT ["/app/entrypoint.sh"]
