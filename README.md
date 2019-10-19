# Techlock Auth Service

This project uses `make` to help you develop.
To view available commands and what they do, you can view the `Makefile` at the root of this project.

## Build

```bash
make build-docker
```

## Running locally for testing

1. Ensure you have Docker & docker-compose installed.

2. Ensure you have Python3 installed. It's recommended you use a python version manager like PyEnv.

3. Install python dependency packages

    ```bash
    make dev-setup
    ```

4. Start up dependency projects

    ```bash
    make run-dependencies
    ```

    This will start up all dependencies for local development:

    * Mock AWS Cognito
    * Mock AWS DynamoDB
    * Mock JWT service
    * Redis

    And will initialize it with default tables and userpool, as well as a root tenant and user.
    Email: `root@root.com`

5. Create `.env` file at the root of this project with the following contents:

    ```conf
    NEXUS_HOST='nexus.techlockinc.com'
    NEXUS_USERNAME='will_be_provided'
    NEXUS_PASSWORD='will_be_provided'

    AUDIENCE=user-management

    REDIS_HOST=127.0.0.1
    REDIS_PORT=6100
    REDIS_DB=0
    REDIS_SOCKET_CONNECT_TIMEOUT=30
    REDIS_IS_CLUSTER='false'
    REDIS_SKIP_FULL_COVERAGE_CHECK='false'
    AWS_ACCESS_KEY_ID=fake
    AWS_SECRET_ACCESS_KEY=fake
    AWS_DEFAULT_REGION=us-east-1
    IDP_NAME=mock
    STAGE=test
    TENANT_ID=test
    NO_CACHE=false
    FLASK_JWT_ALGORITHM=RS256

    JWKS_URLS='http://127.0.0.1:6101/.well-known/jwks.json'
    DYNAMODB_ENDPOINT_URL=http://127.0.0.1:6102
    COGNITO_IDP_ENDPOINT_URL=http://127.0.0.1.10:6103

    AUTH0_DOMAIN=techlock.auth0.com
    AUTH0_CLIENT_ID=IlhsQW8CtOm3Ixp7XXneY8Vo8goMoM0e
    AUTH0_CLIENT_SECRET=y70eEscJP4e5Wp28Td60amxt5R-x39olqLLOG8AuZvu-4gkUtqZvq6qSUMnqZiwR
    AUTH0_AUDIENCE=https://techlock.auth0.com/api/v2/
    AUTH0_CONNECTION_ID=MSS-DEV
    ```

    This will provide environment variables to the runtime

6. Create `.vscode/launch.json` at the root of this project:

    ```json
    {
        // Use IntelliSense to learn about possible attributes.
        // Hover to view descriptions of existing attributes.
        // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Flask",
                "type": "python",
                "request": "launch",
                "module": "flask",
                "env": {
                    "FLASK_APP": "${workspaceFolder}/techlock/user_management_service/app.py",
                    "FLASK_ENV": "development",
                    "FLASK_DEBUG": "0"
                },
                "args": [
                    "run",
                    "--no-debugger",
                    "--no-reload",
                    "--port=5000"
                ],
                "envFile": "${workspaceFolder}/.env",
                "jinja": true,
            }
        ]
    }
    ```

7. Run the project
    a. Open VSCode
    b. Go to the Debug View. Click on the bug icon on the left, 3rd from the top by default, or press Ctrl+Shift+D
    c. At the top of the debug left panel, ensure `Python: Flask` is selected in the dropdown
    d. Hit the green play button at the top.

8. You're now running this API
    If all went well, you can now open a browser and go to http://127.0.0.1:5000/doc/swagger to see the Swagger UI.

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
