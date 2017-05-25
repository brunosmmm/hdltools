#!/bin/bash

echo "Running Tests..."

python $(which nosetests) --with-coverage --cover-package=hdltools --cover-html tests/*
