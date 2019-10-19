include .env
export

clean:
	# Remove __pycache__ and .pytest_cache folders
	@echo "Cleaning project"
	@py3clean .

dev-setup:
	# Installs development dependencies
	@echo "Installing pip requirements"
	@pip install -q -r requirements.txt \
		--extra-index-url https://${NEXUS_USERNAME}:${NEXUS_PASSWORD}@${NEXUS_HOST}/repository/pypi-hosted/simple

install:
	# Installs the project to your python installation
	@echo "Installing"
	@pip install -q \
		--extra-index-url https://${NEXUS_USERNAME}:${NEXUS_PASSWORD}@${NEXUS_HOST}/repository/pypi-hosted/simple \
		.

build-docker:
	# Build this projects docker image
	@echo "Building docker image"
	@docker build \
		--build-arg NEXUS_HOST=${NEXUS_HOST} \
		--build-arg NEXUS_USERNAME=${NEXUS_USERNAME} \
		--build-arg NEXUS_PASSWORD=${NEXUS_PASSWORD} \
		-t registry.gitlab.com/techlock/msc-user-management-service:local .

run:
	# Runs the project in docker. Allows easy testing
	@echo "Running docker-compose project"
	@docker-compose up -d api

run-dependencies:
	# Runs the project dependencies only. Allows running the project in an IDE.
	@echo "Running docker-compose project"
	@docker-compose up -d init

stop:
	# Stops whatever is running via docker-compose. Both run, and run-dependencies
	@echo "Stopping docker-compose"
	@docker-compose down

unittest:
	# Run the unittests
	@echo "Running unittests"
	@python -m pytest -W ignore tests/unittests -vv

e2e:
	# Run the End-to-End tests
	@echo "Running End-to-End tests"
	@./run_tests.sh -d -e
