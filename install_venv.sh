#!/usr/bin/env bash

set -e

# Create a virtual environment
VIRTUAL_ENVIRONMENT='venv'
#pip3 install virtualenv
python3 -m venv ${VIRTUAL_ENVIRONMENT}

# Activate that environment in your current shell
source ./${VIRTUAL_ENVIRONMENT}/bin/activate

# Pip install the required packages.
python -m pip install --upgrade pip numpy pyproj matplotlib
# python -m pip install git+https://github.com/matplotlib/basemap.git
pyton -m pip install -r requirements.txt
