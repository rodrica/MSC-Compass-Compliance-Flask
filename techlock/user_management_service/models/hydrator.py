import marshmallow as ma
import marshmallow.fields as mf
from marshmallow.utils import EXCLUDE

__all__ = [
    'HydratorPostSchema',
]


class HydratorPostSchema(ma.Schema):
    '''
        https://www.ory.sh/oathkeeper/docs/pipeline/mutator/#hydrator
    '''
    class Meta:
        ordered = True
        unknown = EXCLUDE

    subject = mf.String(allow_none=True)
    extra = mf.Dict(keys=mf.String(), allow_none=True)
    header = mf.Dict(keys=mf.String(), allow_none=True)
    match_context = mf.Dict(keys=mf.String(), allow_none=True)
