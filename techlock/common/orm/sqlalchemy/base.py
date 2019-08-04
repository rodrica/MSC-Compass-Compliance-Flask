from .db import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.DateTime, unique=False, nullable=True)
    last_modified_date = db.Column(db.DateTime, unique=False, nullable=True)
