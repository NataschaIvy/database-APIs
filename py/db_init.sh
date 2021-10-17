#!/bin/bash
echo 'migrating database'
cd /app
export FLASK_APP=main.py

flask db init
flask db migrate -m 'migrate'
flask db upgrade

echo 'database migration complete'