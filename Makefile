SHELL := /bin/bash

DOCKER_USER_NAME = govuknotify
DOCKER_IMAGE = ${DOCKER_USER_NAME}/notifications-certificate-management
DOCKER_IMAGE_TAG = latest
DOCKER_IMAGE_NAME = ${DOCKER_IMAGE}:${DOCKER_IMAGE_TAG}

NOTIFY_ENVIRONMENT ?= development
PORT ?= 8000

.PHONY: test
test:
	./run_tests.sh

.PHONY: bootstrap
bootstrap: ## Set up everything to run the app
	pip3 install -r requirements_for_test.txt

.PHONY: freeze-requirements
freeze-requirements: ## Pin all requirements including sub dependencies into requirements.txt
	pip install --upgrade pip-tools
	pip-compile requirements.in

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
