from marshmallow import fields, Schema

__all__ = [
    'LoginSchema'
]


class LoginSchema(Schema):
    email = fields.String(required=True)
    password = fields.String(required=True)
