
import marshmallow as ma
import marshmallow.fields as mf
from dataclasses import dataclass, asdict, field
from typing import Any, List

__all__ = [
    'PageableResponse',
    'PageableResponseBaseSchema',
    'PageableQueryParametersSchema',
]


@dataclass
class PageableResponse:
    items: List[Any] = field(default_factory=list)
    last_key: str = None
    num_items: int = 0

    def __post_init__(self):
        self.num_items = len(self.items)

    def asdict(self):
        return asdict(self)


class PageableResponseBaseSchema(ma.Schema):
    '''
        Add the `items` field yourself
        i.e.:
            items = mf.List[UserSchema]
    '''
    class Meta:
        ordered = True

    last_key = mf.String()
    num_items = mf.Int()


class PageableQueryParametersSchema(ma.Schema):
    class Meta:
        ordered = True

    start_key = mf.String(allow_none=True)
    limit = mf.Int(default=100)
