#!/bin/bash

ROOT=$(pwd)

# Create and activate the virtual environment
python -mvenv .venv
source .venv/bin/activate

# Install Python dependencies
cd $ROOT/src
pip install -r ./requirements.txt

# Install JavaScript dependencies
cd $ROOT/src
npm i -g yarn
yarn

# Update default environment
cd $ROOT/src
cp .env-template .env
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(64))")
sed -i "s/%RANDOM_STRING%/$SECRET_KEY/" .env
unset SECRET_KEY

# Create working directories
mkdir $ROOT/logs

# Set up database
cd src
python manage.py migrate
python manage.py makemigrations
python manage.py migrate triage

echo "Initialization completed." >> $ROOT/logs/omega-triage.log


