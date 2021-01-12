import pytest
from flask import url_for

from main import create_app


@pytest.fixture(scope='session')
def app():
    app = create_app()
    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture
def client(app):
    with app.test_request_context(), app.test_client() as client:
        yield client


def test_healthcheck(client):
    response = client.get(url_for('main.healthcheck'))
    assert response.status_code == 200
    assert response.data.decode('utf-8') == 'ok'
