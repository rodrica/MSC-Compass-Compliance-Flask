# Techlock Auth Service

This project uses `make` to help you develop.
To view available commands and what they do, you can view the `Makefile` at the root of this project.

## Build

```bash
make build-docker
```

## Run locally

Please note that is expects you to have your environment initialized. You can find instructions in `CONTRIBUTE.md` under `Initialize environment for testing`

All api calls are performed in Postman

1. Start app in docker

    ```bash
    make run
    ```

2. Get a mocked JWT token

    `POST http://127.0.0.1:6101/login`

    ```json
    {
      "sub": "test@test.com",
      "tenant_id": "tenant1",
      "roles": [
        "tenant1",
      ],
      "claims": [
        "allow:*:user-management:*:*:*",
      ]
    }
    ```

    This will return an `access_token`

3. Call the api.

    You can now use Postman, to do so, add the token as `Bearer Token` under `Authorization`

    Or you can use the swagger doc at http://127.0.0.1:6105/doc/swagger
    At the top you will find an `Authorize` button, enter the token and authorize.
    You can now try out the api via the swagger page.


## View API documentation

This project is setup to autogenerate swagger and redoc documentation as well as host UIs for both.
Swagger is hosted on `/doc/swagger`, example: http://127.0.0.1:5000/doc/swagger
Redoc is hosted on `/doc/redoc`, example: http://127.0.0.1:5000/doc/redoc

## Authenticate for development

This project uses JWT Bearer tokens for authentication and authorization.
If you've followed the steps above, there is a Mock JWT service running in docker. And this project is configured to trust it. You can use this mock service to generate JWT tokens for testing.

For example, you can use Postman to generate a new token by executing the following request:
`POST http://127.0.0.1:6101/login`

```json
{
  "sub": "root@root.com",
  "username": "root@root.com",
  "tenant_id": "root",
  "roles": [
    "tenant1"
  ],
  "claims": [
    "allow:*:user-management:*:*:*"
  ]
}
```

This will return an access token you can use in any api calls to this service.
Just add the token as a header like so: `Authentication: Bearer {token}`

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

## Tests

This project comes with unittests and end-to-end (e2e) tests.
The unittests can be ran and debugged with VSCode's built-in test tool. Click on the beaker, or lab icon on the left. This should open a test panel showing a tree with all tests. From there you can either run them all at once, or one at a time.

There is also a `run_tests.sh` script at the root of the project.
You can run it as follows to run the unittests `./run_tests.sh --unittest`
To run the e2e test you run `./run_tests.sh --end-to-end`

## Config

### General

OS Variables:
| Key | Required | Default | Description | Allowed Values |
|-----|----------|---------|-------------|----------------|
| IDP_NAME | False | MOCK | Which IDP to use for /user endpoints, default to the mock idp which does nothing | AUTH0, COGNITO, MOCK |

ConfigManager
| Key | Required | Default | Description | Allowed Values |
|-----|----------|---------|-------------|----------------|
| idp.name | False | MOCK | Which IDP to use for /user endpoints, default to the mock idp which does nothing | AUTH0, COGNITO, MOCK |
| auth0.domain | True if  | |
| auth0.client_id |
| | | | | |
| sns.topics.UserNotification | False | | Which SNS Topic to publish UserNotifications to. If not set, will log each message in an error message | True, False |

### Hydrator

OS Variables:
| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| HYDRATOR_BASIC_ENABLED | False | True | Flag to enable Basic authentication for the /hydrator endpoint | true, false |
| HYDRATOR_BASIC_USER | True if HYDRATOR_BASIC_ENABLED is True | | Username to use in Basic authentication | |
| HYDRATOR_BASIC_PASSWORD | True if HYDRATOR_BASIC_ENABLED is True | | Password to use in Basic authentication | |
