import logging

from flask_sqlalchemy import SQLAlchemy

from ...date_utils import get_current_timestamp

logger = logging.getLogger(__name__)


def init_db(db):

    def save(model):
        timestamp = get_current_timestamp()

        if model.created_date is None:
            logger.debug('Creating entity for the first time', extra={
                'created_date': timestamp,
            })

            model.created_date = timestamp

        model.last_modified_date = timestamp

        db.session.add(model)
        db.session.commit()

        return model

    db.Model.save = save


db = SQLAlchemy()
