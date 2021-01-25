# notifications-certificate-management

## What this app does

An HTTP app that:

- when given a certificate signing request, will sign it and return an issued certificate
- provides certificate revocation lists (CRL) for our private certificate authorities

## Why do we have this app

We need to let the Mobile Network Operators (MNOs) get issued certificates signed by us for both TLS and VPN connections. We want to automate this process as much as possible so we avoid manual work every couple of months when certificates need rotating. This is especially important as there are multiple mobile networks to do this for. By having an HTTP endpoint for this the MNOs can request and get new certificates themselves.

We need to let the mobile networks have access to our CRLs. The CRLs are publically accessible from S3. However the cell broadcast infrastructure for the mobile networks does not have access to the public internet so they can not get them from S3. Therefore, we run this app so they can get the CRLs from S3 via our network.

## Set up and run locally

To run this app locally, you need to make sure it has permissions to talk to the AWS Certificate Manager service. For local development we suggest you use the cell broadcast staging AWS account for this as shown in this example.

```
pip install -r requirements_for_test.txt
export FLASK_APP=main.py
export NOTIFY_ENVIRONMENT=development
export EE_USERNAME=ee
export EE_PASSWORD=ee_password
export O2_USERNAME=o2
export O2_PASSWORD=o2_password
export VODAFONE_USERNAME=vodafone
export VODAFONE_PASSWORD=vodafone_password
export THREE_USERNAME=three
export THREE_PASSWORD=three_password
gds aws cell-broadcast-staging-admin -- flask run
```

## Run tests

```
pip install -r requirements_for_test.txt
make test
```
