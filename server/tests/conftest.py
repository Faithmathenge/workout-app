import pytest

from app import create_app
from models import db


@pytest.fixture
def client():
    """A test client backed by a fresh in-memory database."""
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()
        