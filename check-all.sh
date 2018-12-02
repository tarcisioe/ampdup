#!/bin/bash

pytest -vv --cov=ampdup
pylint ampdup
flake8 ampdup
mypy ampdup
pylint test/*.py
flake8 test
mypy test
