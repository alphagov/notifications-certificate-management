import os

import pytest

from main import create_app

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


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


@pytest.fixture
def ee_valid_csr():
    """
    Returns the contents of a CSR with the CommonName of "ee.tls.test.notify"
    """
    with open(os.path.join(__location__, 'ee_tls_test_csr.pem'), 'rb') as csr:
        csr_contents = csr.read()

    return csr_contents


@pytest.fixture
def csr_for_unknown_mno():
    """
    Returns the contents of a CSR with the CommonName of "fakemno.tls.test.notify"
    """
    with open(os.path.join(__location__, 'fake_mno_csr.pem'), 'rb') as csr:
        csr_contents = csr.read()

    return csr_contents
