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

## Claims

Claims must match one of the following schemas:

```
{allow | deny}:{tenant}:{audience}:{action}:{resource}:{id}
{allow | deny}:{tenant}:{audience}:{action}:{resource}:{filter_field}:{filter_value}
```

The `allow` part is optional and when ommitted will be interpreted as `allow`

## Auth Flow

It is expected that you use an independent identity provider (idp).
At the time of this writing, only AWS Cognito is supported.

This service expects to be running in docker with Traefik and Ory Oathkeeper
Traefik would forward all requests to Oathkeeper, which will send the IDP's access token to our `/hydrator` endpoint. We will return the `tenant_id`, `roles`, and `claims` of the user. Oathkeeper will then generate a new access token with that information in it, and forward it back to us, or any other service.
That service will then use this new token to validate access.
