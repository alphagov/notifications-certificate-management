import botocore


class Config(object):
    AWS_REGION = "eu-west-2"
    AWS_CONFIG = botocore.config.Config(region_name=AWS_REGION)


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


configs = {
    'development': Development,
    'staging': Staging,
    'production': Production,
}
