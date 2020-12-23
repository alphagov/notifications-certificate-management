import logging

from flask import Flask, Response, abort, request
from boto3 import client, resource
import botocore

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Flask(__name__)


AWS_REGION = "eu-west-2"
AWS_CONFIG = botocore.config.Config(region_name=AWS_REGION)
PRIVATE_CAS = {
    "vpn": {
        "ca_id": "fb0bf875-66a5-4447-bae3-403c457bda2d",
        "revocation_bucket": "gds-cb-vjv982-vpn-ca-revoc",
        "account_id": "144489291306"
    }
}


@app.route('/healthcheck')
def healthcheck():
    # what format should this be, should it be JSON
    return 'ok'


@app.route('/vpn/crl')
def crl():
    """
    Returns a certificate revocation list for the VPN certificate authority

    Mimics the HTTP response and headers of a GET request to the public S3 bucket for this
    file

    CRL is encoded in DER format as per
    https://docs.aws.amazon.com/acm-pca/latest/userguide/PcaCreateCa.html#crl-structure
    so if you need to view it, you need to use
    `openssl crl -inform DER -in path-to-crl-file -text -noout`
    """
    ca = PRIVATE_CAS.get("vpn")
    ca_id = ca["ca_id"]
    bucket_name = ca["revocation_bucket"]
    file_name = f"crl/{ca_id}.crl"

    try:
        s3 = resource('s3')
        key = s3.Object(bucket_name, file_name)
        crl_data = key.get()['Body'].read()
    except botocore.exceptions.ClientError as error:
        # check whether this should be logger.exception or logger.error
        logger.error(error)
        abort(500)

    return Response(crl_data, mimetype='application/pkix-crl')


@app.route('/vpn/sign-certificate', methods=["POST"])
def sign_certificate():
    """
    Issues and returns a certificate for a certificate signing request

    curl -X POST --data-binary "@csr.txt" http://127.0.0.1:5000/vpn/sign-certificate
    """
    ca = PRIVATE_CAS.get("vpn")
    ca_id = ca["ca_id"]
    account_id = ca["account_id"]
    ca_arn = f"arn:aws:acm-pca:{AWS_REGION}:{account_id}:certificate-authority/{ca_id}"
    csr = request.get_data()

    ca_client = client('acm-pca', config=AWS_CONFIG)
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
