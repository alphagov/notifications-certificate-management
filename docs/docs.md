# GOV.UK Notify cell broadcast certificate management app

This documentation is for the mobile networks who will be the users of our certificate management app.

This app will allow you to be issued a certificate and to download certificate revocation lists.

## Authentication

Authentication uses HTTP Basic Auth. You will be provided with two sets of credentials, one for staging and one for production. The username will be the same for both environments.

## IP address

You will be provided two static IP addresses for the certificate management app, one for staging and one for production.


## Healthcheck endpoint

### Request

GET `/healthcheck`

### Response

HTTP 200 with `text/html` content type.

### Example

```sh
curl --user my-username:my-password https://192.0.2.1/healthcheck

ok
```


## Download a certificate revocation list endpoint

### Request

- GET `/vpn/crl` for VPN certificates
- GET `/tls/crl` for TLS certificates

### Response

HTTP 200 with `application/pkix-crl` content type.

The response is encoded in DER format as per https://docs.aws.amazon.com/acm-pca/latest/userguide/PcaCreateCa.html#crl-structure so if you need to view it, you need to use
    
```sh
openssl crl -inform DER -in path-to-crl-file -text -noout
```

### Example

```sh
curl --user my-username:my-password https://192.0.2.1/tls/crl > crl-response.txt
openssl crl -inform DER -in crl-response.txt -text -noout

Certificate Revocation List (CRL):
        Version 2 (0x1)
....
```


## Signing a certificate signing request endpoint

### Request

- POST `/tls/sign-certificate` for a TLS certificate
- POST `/vpn/sign-certificate` for a VPN certificate

Your request body should be a certificate signing request sent as binary data using the `application/x-www-form-urlencoded` content type.

### Response

HTTP 200 with `application/json` content type. The response will contain your certificate and the certificate chain.

```json
{
    "Certificate":"-----BEGIN CERTIFICATE-----....-----END CERTIFICATE-----",
    "CertificateChain":"-----BEGIN CERTIFICATE-----....-----END CERTIFICATE-----\n-----BEGIN CERTIFICATE-----....-----END CERTIFICATE-----",
    "ResponseMetadata":{....}
}
```

### Example

Create a CSR for `ee.vpn.notify.staging` and store it in `csr.txt`. Then:

```sh
curl --user my-username:my-password -X POST --data-binary "@csr.txt" http://127.0.0.1:5000/vpn/sign-certificate > my-certificate.txt
```













