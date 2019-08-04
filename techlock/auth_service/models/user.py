import bcrypt
import marshmallow as ma
import marshmallow.fields as mf

from techlock.common.orm.sqlalchemy.db import db
from techlock.common.orm.sqlalchemy.base import BaseModel


__all__ = [
    'User',
    'UserSchema',
]


class User(BaseModel):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    tags = db.Column(db.JSON())

    def __init__(self, email, password):
        self.email = email
        self.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


class UserSchema(ma.Schema):
    class Meta:
        ordered = True

    id = mf.Integer(dump_only=True)
    email = mf.String()
    password = mf.String()

    tags = mf.Dict(keys=mf.String())
