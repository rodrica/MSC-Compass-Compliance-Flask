import marshmallow as ma
import marshmallow.fields as mf


class DashboardDataSchema(ma.Schema):
    class Meta:
        ordered = True
        unknown = ma.EXCLUDE

    name = mf.String()
    url = mf.String()
    height = mf.String()
    width = mf.String()
    metadata = mf.Dict(mf.String(), mf.String())
