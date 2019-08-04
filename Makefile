include .env
export

build-docker:
	@docker build \
		--build-arg NEXUS_HOST=${NEXUS_HOST} \
		-t registry.gitlab.com/techlock/auth_service:local .

