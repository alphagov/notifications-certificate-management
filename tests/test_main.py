import base64
from unittest.mock import Mock

import boto3
import botocore
import pytest
from flask import current_app, url_for
from moto import mock_s3


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


def test_sign_certificate_returns_401_if_basic_auth_creds_are_not_provided(client):
    response = client.post(url_for('main.sign_certificate', ca_name='tls'))
    assert response.status_code == 401


def test_sign_certificate_returns_401_if_username_is_wrong(client):
    invalid_credentials = base64.b64encode(b'me:vodafone_password').decode('utf-8')

    response = client.post(
        url_for('main.sign_certificate', ca_name='bad_name'),
        headers={'Authorization': f'Basic {invalid_credentials}'}
    )
    assert response.status_code == 401


def test_sign_certificate_returns_401_if_password_is_wrong(client):
    invalid_credentials = base64.b64encode(b'ee:vodafone_password').decode('utf-8')

    response = client.post(
        url_for('main.sign_certificate', ca_name='bad_name'),
        headers={'Authorization': f'Basic {invalid_credentials}'}
    )
    assert response.status_code == 401


def test_sign_certificate_returns_404_if_ca_name_is_unknown(client):
    valid_credentials = base64.b64encode(b'ee:ee_password').decode('utf-8')
    response = client.post(
        url_for('main.sign_certificate', ca_name='bad_name'),
        headers={'Authorization': f'Basic {valid_credentials}'}
    )
    assert response.status_code == 404


def test_sign_certificate_returns_403_if_cn_is_forbidden_for_mno(client, mocker, csr_for_unknown_mno):
    mock_ca_client = Mock(issue_certificate=Mock())
    mocker.patch('main.client', return_value=mock_ca_client)

    valid_credentials = base64.b64encode(b'ee:ee_password').decode('utf-8')
    response = client.post(
        url_for('main.sign_certificate', ca_name='vpn'),
        headers={'Authorization': f'Basic {valid_credentials}'},
        data=csr_for_unknown_mno
    )
    assert response.status_code == 403
    assert not mock_ca_client.called


@pytest.mark.parametrize('ca_name, expected_ca_arn', [
    ('vpn', 'arn:aws:acm-pca:eu-west-2:1234:certificate-authority/1'),
    ('tls', 'arn:aws:acm-pca:eu-west-2:5678:certificate-authority/2'),
])
def test_sign_certificate_returns_500_if_certificate_is_not_issued(
    client,
    mocker,
    ca_name,
    expected_ca_arn,
    ee_valid_csr,
):
    def raise_waiter_error(**kwargs):
        raise botocore.exceptions.WaiterError('name', 'reason', 'last_response')

    # mock the ca_client waiter to raise an error when waiting for the certificate -
    # this is the error that would occur if a certificate was not issued within 180s
    mock_ca_client = Mock(
        issue_certificate=Mock(return_value={"CertificateArn": "my_cert_arn"}),
        get_waiter=lambda _: Mock(wait=raise_waiter_error)
    )
    mocker.patch('main.client', return_value=mock_ca_client)

    valid_credentials = base64.b64encode(b'ee:ee_password').decode('utf-8')
    response = client.post(
        url_for('main.sign_certificate', ca_name=ca_name),
        data=ee_valid_csr,
        headers={'Authorization': f'Basic {valid_credentials}'}
    )

    assert response.status_code == 500
    mock_ca_client.issue_certificate.assert_called_once_with(
        CertificateAuthorityArn=expected_ca_arn,
        Csr=ee_valid_csr,
        SigningAlgorithm='SHA256WITHRSA',
        Validity={
            'Value': 365,
            'Type': "DAYS"
        }
    )


@pytest.mark.parametrize('ca_name, expected_ca_arn', [
    ('vpn', 'arn:aws:acm-pca:eu-west-2:1234:certificate-authority/1'),
    ('tls', 'arn:aws:acm-pca:eu-west-2:5678:certificate-authority/2'),
])
def test_sign_certificate_issues_certificate(client, mocker, ca_name, expected_ca_arn, ee_valid_csr):
    mock_ca_client = Mock(
        issue_certificate=Mock(return_value={"CertificateArn": "my_cert_arn"}),
        get_certificate=Mock(return_value={'Certificate': 'my_certificate', 'CertificateChain': 'my_chain'})
    )
    mocker.patch('main.client', return_value=mock_ca_client)

    valid_credentials = base64.b64encode(b'ee:ee_password').decode('utf-8')
    response = client.post(
        url_for('main.sign_certificate', ca_name=ca_name),
        data=ee_valid_csr,
        headers={'Authorization': f'Basic {valid_credentials}'}
    )
    assert response.status_code == 200
    assert response.get_json() == {'Certificate': 'my_certificate', 'CertificateChain': 'my_chain'}
    mock_ca_client.issue_certificate.assert_called_once_with(
        CertificateAuthorityArn=expected_ca_arn,
        Csr=ee_valid_csr,
        SigningAlgorithm='SHA256WITHRSA',
        Validity={
            'Value': 365,
            'Type': "DAYS"
        }
    )
    mock_ca_client.get_certificate.assert_called_once_with(
        CertificateArn='my_cert_arn',
        CertificateAuthorityArn=expected_ca_arn
    )
