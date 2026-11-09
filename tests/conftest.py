"""Общие фикстуры pytest: отдельная временная БД для каждого теста."""
import pytest

from app import create_app, db
from config import Config


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False


@pytest.fixture()
def app(tmp_path):
    class _Config(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
        UPLOAD_FOLDER = str(tmp_path / 'uploads')

    application = create_app(_Config)
    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username, password):
    return client.post(
        '/login',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )


@pytest.fixture()
def admin_client(client):
    login(client, 'admin', 'admin123')
    return client


@pytest.fixture()
def teacher_client(client):
    login(client, 'teacher', 'teacher123')
    return client


@pytest.fixture()
def parent_client(client):
    login(client, 'parent', 'parent123')
    return client
