#!/bin/bash

pytest -vv --cov=ampdup
pylint ampdup
flake8 ampdup
mypy ampdup
pylint test/*
flake8 test
mypy test
