# Techlock Auth Service

## Build

```bash
make build-docker
```

## Running locally for testing

```bash
docker-compose up
```

This will start up all dependencies for local development:

* Mock AWS Cognito
* Mock AWS DynamoDB
* Mock JWT service
* Redis

And will initialize it with default tables and userpool, as well as a root tenant and user.
Email: `root@root.com`
