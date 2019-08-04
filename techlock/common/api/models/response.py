
import marshmallow as ma
import marshmallow.fields as mf

from dataclasses import dataclass

__all__ = [
    'ErrorResponse',
    'BaseResponseSchema',
    'ErrorResponseSchema',
]


@dataclass
class ErrorResponse():
    message: str
    error: str = None


class BaseResponseSchema(ma.Schema):
    class Meta:
        ordered = True

    message = mf.String()


class ErrorResponseSchema(BaseResponseSchema):
    class Meta:
        ordered = True

    error = mf.String()
