#!/bin/bash

# Install required packages.
#pip3 install coverage --upgrade --user "$@"

python3 -m unittest discover -t ../ "test" -q
#coverage run -m unittest discover -t ../ "test" -q
#coverage report -m
#coverage html
