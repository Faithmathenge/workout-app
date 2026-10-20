from flask import Flask
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from models import db
from routes import api

migrate = Migrate()


def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if config:
        app.config.update(config)

    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(api)
    register_error_handlers(app)
    return app


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_schema_error(err):
        return {"errors": err.messages}, 400

    # Raised by the @validates methods on the models.
    @app.errorhandler(ValueError)
    def handle_model_error(err):
        db.session.rollback()
        return {"errors": {"_model": [str(err)]}}, 400

    @app.errorhandler(IntegrityError)
    def handle_constraint_error(err):
        db.session.rollback()
        is_duplicate = "UNIQUE" in str(err.orig).upper()
        message = "That record already exists." if is_duplicate else "Database constraint violated."
        return {"errors": {"_database": [message]}}, 409 if is_duplicate else 400

    @app.errorhandler(404)
    def handle_not_found(err):
        return {"error": "Not found"}, 404

    @app.errorhandler(405)
    def handle_bad_method(err):
        return {"error": "Method not allowed"}, 405


app = create_app()
