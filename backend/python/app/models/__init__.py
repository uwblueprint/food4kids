from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()


def init_app(app):
    from .entity import Entity
    from .simple_entity import SimpleEntity
    from .user import User

    app.app_context().push()
    db.init_app(app)
    migrate.init_app(app, db)

    erase_db_and_sync = app.config["TESTING"]

    if erase_db_and_sync:
        # drop tables
        db.reflect()
        db.drop_all()

        # recreate tables
        db.create_all()
