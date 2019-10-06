include .env
export

build-docker:
	@docker build \
		--build-arg NEXUS_HOST=${NEXUS_HOST} \
		-t registry.gitlab.com/techlock/msc-user-management-service:local .

unittest:
	python -m pytest -W ignore tests/unittests -vv
