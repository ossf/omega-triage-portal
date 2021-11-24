#!/bin/bash

# Create and activate the virtual environment
python -mvenv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r ./requirements.txt

# Install JavaScript dependencies
npm i -g yarn
yarn

# Update default environment
cp .env-template .env
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(64))")
sed -i "s/%RANDOM_STRING%/$SECRET_KEY/" .env
unset SECRET_KEY

# Set up database
cd src
python manage.py migrate
python manage.py makemigrations
python manage.py migrate triage


