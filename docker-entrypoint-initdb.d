#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$DATABASE_USER" --dbname "$DATABASE_NAME" <<-EOSQL
	CREATE USER triage_user;
	CREATE DATABASE triage;
	GRANT ALL PRIVILEGES ON DATABASE triage_user TO triage_user;
EOSQL
