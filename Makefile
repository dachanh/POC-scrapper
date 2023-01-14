PHONY: build
PYTHON := $(shell which python3)
SHELL := /bin/bash

build:
	$(PYTHON) -m venv env &&  source ./env/bin/activate && pip install -r requirements.txt
