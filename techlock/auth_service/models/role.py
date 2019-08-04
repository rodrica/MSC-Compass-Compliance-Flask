import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base

__all__ = [
    'Role',
    'RoleSchema',
]

Base = declarative_base()


class Role(Base):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.String(255), nullable=False)

    tags = db.Column(db.JSON())


class RoleSchema(ma.Schema):
    class Meta:
        ordered = True

    id = mf.Integer(dump_only=True)
    name = mf.String()
    description = mf.String()
    created_on = mf.DateTime()
    created_by = mf.String()

    tags = mf.Dict(keys=mf.String())
