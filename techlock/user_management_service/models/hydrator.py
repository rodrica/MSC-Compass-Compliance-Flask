import marshmallow as ma
import marshmallow.fields as mf


__all__ = [
    'HydratorPostSchema',
]


class HydratorPostSchema(ma.Schema):
    class Meta:
        ordered = True

    subject = mf.String(allow_none=True)
    extra = mf.Dict(keys=mf.String(), allow_none=True)
    header = mf.Dict(keys=mf.String(), allow_none=True)
