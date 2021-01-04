SHELL := /bin/bash

DOCKER_USER_NAME = govuknotify
DOCKER_IMAGE = ${DOCKER_USER_NAME}/notifications-certificate-management
DOCKER_IMAGE_TAG = latest
DOCKER_IMAGE_NAME = ${DOCKER_IMAGE}:${DOCKER_IMAGE_TAG}

NOTIFY_ENVIRONMENT ?= development 
PORT ?= 8000

.PHONY: test
test:
	flake8 .

.PHONY: build-docker-image
build-docker-image:
	docker build -t ${DOCKER_IMAGE_NAME} .

.PHONY: run-with-docker
run-with-docker: build-docker-image
	docker run -it --rm \
		-p ${PORT}:${PORT} \
		-e PORT=${PORT} \
		-e NOTIFY_ENVIRONMENT=${NOTIFY_ENVIRONMENT} \
		${DOCKER_IMAGE_NAME}
