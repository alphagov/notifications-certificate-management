import hmac
import logging
import os

import botocore
from boto3 import client, resource
from cryptography import x509
from cryptography.x509.oid import NameOID
from flask import Blueprint, Flask, Response, abort, current_app, request
from flask_httpauth import HTTPBasicAuth

from config import configs

logger = logging.getLogger()
logger.setLevel(logging.INFO)
main = Blueprint('main', __name__)
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    credentials = current_app.config['CREDENTIALS']
    if username in credentials and hmac.compare_digest(credentials[username], password):
        return username


@main.route('/healthcheck')
def healthcheck():
    # what format should this be, should it be JSON
    return 'ok'


@main.route('/<ca_name>/crl')
def crl(ca_name):
    """
    Returns a certificate revocation list for one of our private certificate authorities

    Mimics the HTTP response and headers of a GET request to the public S3 bucket for this
    file

    CRL is encoded in DER format as per
    https://docs.aws.amazon.com/acm-pca/latest/userguide/PcaCreateCa.html#crl-structure
    so if you need to view it, you need to use
    `openssl crl -inform DER -in path-to-crl-file -text -noout`
    """
    ca = current_app.config['PRIVATE_CAS'].get(ca_name)
    if not ca:
        abort(404)

    ca_id = ca["ca_id"]
    bucket_name = ca["revocation_bucket"]
    file_name = f"crl/{ca_id}.crl"

    try:
        s3 = resource('s3')
        key = s3.Object(bucket_name, file_name)
        crl_data = key.get()['Body'].read()
    except botocore.exceptions.ClientError as error:
        logger.error(error)
        abort(500)

    return Response(crl_data, mimetype='application/pkix-crl')


@main.route('/<ca_name>/sign-certificate', methods=["POST"])
@auth.login_required
def sign_certificate(ca_name):
    """
    Issues and returns a certificate for a PEM certificate signing request.
    This endpoint is protected with basic auth.

    curl --user my-username:my-password -X POST --data-binary "@csr.pem" http://127.0.0.1:5000/vpn/sign-certificate
    """
    ca = current_app.config['PRIVATE_CAS'].get(ca_name)
    if not ca:
        abort(404)

    mno = auth.current_user()
    allowed_common_names = current_app.config['ALLOWED_COMMON_NAMES'][mno]

    csr = request.get_data()
    parsed_csr = x509.load_pem_x509_csr(csr)
    common_name_value = parsed_csr.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value

    if common_name_value not in allowed_common_names:
        abort(403)

    ca_id = ca["ca_id"]
    account_id = ca["account_id"]
    ca_arn = f"arn:aws:acm-pca:{current_app.config['AWS_REGION']}:{account_id}:certificate-authority/{ca_id}"

    ca_client = client('acm-pca', config=current_app.config['AWS_CONFIG'])
    response = ca_client.issue_certificate(
        CertificateAuthorityArn=ca_arn,
        Csr=csr,
        SigningAlgorithm='SHA256WITHRSA',
        Validity={
            'Value': 365,
            'Type': "DAYS"
        }
    )
    cert_arn = response["CertificateArn"]

    # Poll AWS for up to 180 seconds for certificate to be issued
    waiter = ca_client.get_waiter('certificate_issued')
    try:
        waiter.wait(
            CertificateAuthorityArn=ca_arn,
            CertificateArn=cert_arn,
        )
    except botocore.exceptions.WaiterError as e:
        logger.error(f"Certificate {cert_arn} was not issued within 180 seconds: {e}")
        abort(500)

    cert = ca_client.get_certificate(
        CertificateAuthorityArn=ca_arn,
        CertificateArn=cert_arn
    )

    return cert


def create_app():
    app = Flask(__name__)
    notify_environment = os.environ['NOTIFY_ENVIRONMENT']
    app.config.from_object(configs[notify_environment])

    app.register_blueprint(main)

    return app


app = create_app()
