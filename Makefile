SHELL := /bin/bash

.PHONY: test
test:
	flake8 .
