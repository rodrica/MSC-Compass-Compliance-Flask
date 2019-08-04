import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base

__all__ = [
    'Permission',
    'PermissionSchema',
]

Base = declarative_base()


class Permission(Base):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    service = db.Column(db.String(255), nullable=False)

    tags = db.Column(db.JSON())


class PermissionSchema(ma.Schema):
    class Meta:
        ordered = True

    id = mf.Integer(dump_only=True)
    name = mf.String()
    description = mf.String()
    service = mf.String()

    tags = mf.Dict(keys=mf.String())
