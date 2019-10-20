# Contribute

## Git commits

Please use the `fix:` and `feat:` prefixes for each commit. A feat adds new functionality, or changes behavior in a non breaking way.
When introducing a breaking change, please add `BREAKING CHANGE:` to the footer.

Examples:

```text
fix: Ensure type is cast to string
```

```text
feat: Removing length option from user's api

BREAKING CHANGE: Removed length option from user's api
```

The idea is that we'll be using https://github.com/relekang/python-semantic-release for automated semver versioning.
At this time this isn't implemented yet.

## Pull requests

All work should be done in new branches and then merged into the master branch via a pull request (PR).
Only PRs were the CI pipeline succeeds will be merged.

## Initialize environment for testing

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
