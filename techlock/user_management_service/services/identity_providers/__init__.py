from techlock.common import ConfigManager

from .auth0 import Auth0Idp
from .cognito import CognitoIdp
from .mock import MockIdp

_idp_map = {
    'AUTH0': Auth0Idp,
    'COGNITO': CognitoIdp,
    'MOCK': MockIdp,
}


def get_idp(idp_name=None):
    if idp_name is None:
        idp_name = ConfigManager().get(ConfigManager._DEFAULT_TENANT_ID, 'idp.name', 'MOCK')

    idp_class = _idp_map.get(idp_name.upper())
    if idp_class is None:
        raise NotImplementedError("No idp with name '{}' is implemented".format(idp_name))

    idp_instance = idp_class()
    return idp_instance
