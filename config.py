import json
import os

import botocore.config


class Config(object):
    AWS_REGION = "eu-west-2"
    AWS_CONFIG = botocore.config.Config(region_name=AWS_REGION)

    EE_USERNAME = os.environ['EE_USERNAME']
    EE_PASSWORD = os.environ['EE_PASSWORD']
    O2_USERNAME = os.environ['O2_USERNAME']
    O2_PASSWORD = os.environ['O2_PASSWORD']
    VODAFONE_USERNAME = os.environ['VODAFONE_USERNAME']
    VODAFONE_PASSWORD = os.environ['VODAFONE_PASSWORD']
    THREE_USERNAME = os.environ['THREE_USERNAME']
    THREE_PASSWORD = os.environ['THREE_PASSWORD']

    CREDENTIALS = {
        EE_USERNAME: EE_PASSWORD,
        O2_USERNAME: O2_PASSWORD,
        VODAFONE_USERNAME: VODAFONE_PASSWORD,
        THREE_USERNAME: THREE_PASSWORD,
    }
    ALLOWED_COMMON_NAMES = {
        EE_USERNAME: json.loads(os.environ.get('EE_COMMON_NAMES', '[]')),
        O2_USERNAME: json.loads(os.environ.get('O2_COMMON_NAMES', '[]')),
        VODAFONE_USERNAME: json.loads(os.environ.get('VODAFONE_COMMON_NAMES', '[]')),
        THREE_USERNAME: json.loads(os.environ.get('THREE_COMMON_NAMES', '[]')),
    }


class Staging(Config):
    PRIVATE_CAS = {
        "vpn": {
            "ca_id": "fb0bf875-66a5-4447-bae3-403c457bda2d",
            "revocation_bucket": "gds-cb-vjv982-vpn-ca-revoc",
            "account_id": "144489291306"
        },
        "tls": {
            "ca_id": "89a1067f-8bc0-48b3-8e85-bab92785c6a0",
            "revocation_bucket": "gds-cb-jysgde-tls-ca-revoc",
            "account_id": "144489291306"
        }
    }


class Development(Staging):
    # Use our staging private CAs for local development
    pass


class Production(Config):
    PRIVATE_CAS = {
        "vpn": {
            "ca_id": "TBC",
            "revocation_bucket": "TBC",
            "account_id": "TBC"
        },
        "tls": {
            "ca_id": "TBC",
            "revocation_bucket": "TBC",
            "account_id": "TBC"
        }
    }


class Test(Config):
    TESTING = True
    PRIVATE_CAS = {
        "vpn": {
            "ca_id": "1",
            "revocation_bucket": "test_vpn_bucket",
            "account_id": "1234"
        },
        "tls": {
            "ca_id": "2",
            "revocation_bucket": "test_tls_bucket",
            "account_id": "5678"
        }
    }


configs = {
    'test': Test,
    'development': Development,
    'staging': Staging,
    'production': Production,
}
