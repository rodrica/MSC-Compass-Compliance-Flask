import marshmallow as ma
import marshmallow.fields as mf
from dataclasses import dataclass

from techlock.common.api.models import BaseResponseSchema

__all__ = [
    'RegistrationResponse',
    'RegistrationSchema',
    'RegistrationResponseSchema',
]


@dataclass
class RegistrationResponse():
    message: str


class RegistrationSchema(ma.Schema):
    email = mf.String(required=True)
    password = mf.String(required=True)


class RegistrationResponseSchema(BaseResponseSchema):
    access_token = mf.String()
    refresh_token = mf.String()
