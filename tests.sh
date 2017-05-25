#!/bin/bash

python (which nosetests) --with-coverage --cover-package=hdltools --cover-html tests/*
