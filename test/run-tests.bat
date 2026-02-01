@echo off

:: Install required packages.
rem pip3 install coverage --upgrade --user %*

python -m unittest discover -t ../ "test" -q
rem coverage run -m unittest discover -t ../ "test" -q
rem coverage report -m
rem coverage html
