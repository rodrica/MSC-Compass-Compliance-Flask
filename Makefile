include .env
export

clean:
# 	Remove __pycache__ and .pytest_cache folders
	@echo "Cleaning project"
	@py3clean .

dev-setup:
# 	Installs development dependencies
	@echo "Updating pip"
	@python3 -m pip install --upgrade pip

	@echo "Installing pip requirements"
	@pip3 install -r requirements.txt --extra-index-url https://${NEXUS_HOST}/repository/pypi-hosted/simple

	@echo "Initializing pre-commit"
	@pre-commit install

init-virtualenv:
# 	Installs VirtualEnv and creates a local directory for it.
#	NOTE: Can not be used if you use pyenv-virtualenv. They conflict with eachother.
	@echo "Installing VirtualEnv"
	@pip3 install virtualenv

	@echo "Creating .venv"
	@virtualenv .venv

virtual-dev-setup: init-virtualenv dev-setup
#	Creates a virtualenv and installs all dev dependencies in it.

init-pyenv:
#	Initializes pyenv-virtualenv.
	@echo "Installing Python 3.7.9"
	@pyenv install --skip-existing 3.7.9
	@pyenv shell 3.7.9

	@echo "Creating virtualenv"
	@pyenv virtualenv 3.7.9 msc-common
	@pyenv local msc-common

pyenv-dev-setup: init-pyenv dev-setup
#	Creates a virtualenv using pyenv and installs all dev dependencies in it.

install:
# 	Installs the project to your python installation
	@echo "Installing"
	@pip3 install --extra-index-url https://${NEXUS_HOST}/repository/pypi-hosted/simple .

build-docker:
# 	Build this projects docker image
	@echo "Building docker image"
	@docker build \
		--build-arg NEXUS_HOST=${NEXUS_HOST} \
		-t registry.gitlab.com/techlock/msc-user-management-service:local .

run:
# 	Runs the project in docker. Allows easy testing
	@echo "Running docker-compose project"
	@docker-compose build
	@docker-compose up -d api

run-dependencies:
# 	Runs the project dependencies only. Allows running the project in an IDE.
	@echo "Running docker-compose project"
	@docker-compose build
	@docker-compose up -d init

stop:
# 	Stops whatever is running via docker-compose. Both run, and run-dependencies
	@echo "Stopping docker-compose"
	@docker-compose down

restart:
# 	Restart the project in docker. Allows easy testing
	@echo "Restarting docker-compose project"
	@docker-compose down
	@docker-compose build
	@docker-compose up -d api

pre-commit:
# 	Runs pre-commit
	@echo "Running pre-commit"
	@pre-commit run --all-files

lint:
# 	Run lint / style test
	@echo "Running style check"
	@python3 -m flake8

unittest:
# 	Run the unittests
	@echo "Running unittests"
	@python3 -m pytest -W ignore tests/unittests -vv

e2e:
# 	Run the End-to-End tests
	@echo "Running End-to-End tests"
	@./run_tests.sh -d -e

test:
# 	Run all tests
	@echo "Running all tests"
	@./run_tests.sh -d -a -k -v -n

	@echo "Leaving test environment running"
	@docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | sort
