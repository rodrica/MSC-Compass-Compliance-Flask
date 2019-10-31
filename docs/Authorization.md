# Authorization

Authorization is about validating that an entity had permission to access a resource. This is very different from **authentication** which is about proving that an entity is who they claim to be.

In order to **authorize** an entity, you must first be sure that the entity is who they say they are. Thus they must first be **authenticated**.

## TechLock's Authentication architecture

At TeckLock we use [Auth0](https://auth0.com/) as our Identity Provider (IDP). This means that we use Auth0 to handle authentication.
The advantages here are that we do not need to securely store username and password information, and manage regulatory compliances on the matter. Auth0 will handle this for us, source: https://auth0.com/security/.

Furthermore, Auth0 has great built-in support for SAML, OAuth and others. Making it easy for us to create an Single Sign-On (SSO) solution for all our products.
It also allows us to delegate authentication to other IDPs. This enables us to use a client's existing Active Directory (AD) solution to authenticate their users on our system. And finally, Auth0 has great documentation. This makes working with it, from a development standpoint, very easy.

All these features are very difficult to implement ourselves.

## TeckLock's Authorization architecture

At TechLock we're creating a micro-service architecture.
This means we have certain requirements:

- Services need to be able to do authorization themselves. They should not need to connect to a authorization service to do this.
- Services should be easy to test for development.

The best way to do this is that by makin sure services are not be aware of users and roles. They simply get claims. For auditing reasons they will need an entity_name. This will allow us to set a `created_by`, and `modified_by` field for example.

JSON Web Tokens (JWT) are well suited for this task. The standard `subject` field will be used for the entity_name, and we can add our own `claims` field in the json body.

JWT's do have a problem, they are signed, not encrypted. This means that anybody can read what's in them.
They are also passed via the Authorization header, which may have a size limit. Apache web server has a limit of 8KB for example.

For these reasons we will take in the IDP's identity JWT, and generate our own access JWT for use by the micro-services. The access JWT will contain the identity's claims, but only for the requested service.
This means that we have complete separation between services. And the user only ever gets the identity JWT which gives him no insight into his own access policy.

### Implementation

To implement this we use a few OSS projects.

- Traefik is our API proxy, it has the ability to contact another service to validate access and get new headers.
- OathKeeper is and Access Proxy and Access Control Decision API. It allows us to generate new JWTs
- user-Management-service, this is our own service for managing users and claims. It returns the relevant claims based on the identity token and requested service.

To view the UML Flow diagram, you can open the `docs/diagrams/TL_Auth_flow.drawio` with [draw.io](https://www.draw.io/)
