#!/bin/sh

pip install -r requirements.txt
[ -e "app.db" ] && rm app.db
export FLASK_APP=app.py
flask db init
flask db create
# Create the user
flask users create -a admin@inveniosoftware.org --password 123456
# Create a role "admins"
flask roles create admins
# Add the role "admins" to the user
flask roles add admin@inveniosoftware.org admins
# Give access to admin pages to the "admins" users
flask access allow -r admins admin-access
echo '{"title": "Test title"}' | flask records create \
  -i deadbeef-9fe4-43d3-a08f-38c2b309afba --pid-minter recid
flask run -h 0.0.0.0 -p 5000
