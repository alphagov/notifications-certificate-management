import boto3
import pytest
from flask import current_app, url_for
from moto import mock_s3

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


def test_get_crl_returns_404_if_ca_name_is_unknown(client):
    response = client.get(url_for('main.crl', ca_name='bad_name'))
    assert response.status_code == 404


@mock_s3
@pytest.mark.parametrize('ca_name', ['vpn', 'tls'])
def test_get_crl_returns_500_if_there_is_an_s3_error(client, ca_name):
    ca = current_app.config['PRIVATE_CAS'][ca_name]

    # Create the correct bucket, but leave it empty so that a
    # botocore.exceptions.ClientError is raised when trying to get an object from it
    conn = boto3.resource('s3', region_name=current_app.config['AWS_REGION'])
    conn.create_bucket(
        Bucket=ca['revocation_bucket'],
        CreateBucketConfiguration={'LocationConstraint': current_app.config['AWS_REGION']}
    )

    response = client.get(url_for('main.crl', ca_name=ca_name))
    assert response.status_code == 500


@mock_s3
@pytest.mark.parametrize('ca_name', ['vpn', 'tls'])
def test_get_crl_returns_the_crl(client, ca_name):
    ca = current_app.config['PRIVATE_CAS'][ca_name]
    bucket_name = ca['revocation_bucket']
    filename = f"crl/{ca['ca_id']}.crl"

    conn = boto3.resource('s3', region_name=current_app.config['AWS_REGION'])
    conn.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': current_app.config['AWS_REGION']}
    )
    s3 = boto3.client('s3', region_name=current_app.config['AWS_REGION'])
    s3.put_object(Bucket=bucket_name, Key=filename, Body=b'This is a crl')

    response = client.get(url_for('main.crl', ca_name=ca_name))
    assert response.status_code == 200
    assert response.data.decode('utf-8') == 'This is a crl'
    assert response.mimetype == 'application/pkix-crl'
