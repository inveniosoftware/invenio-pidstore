#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Create the user
flask users create -a admin@inveniosoftware.org --password 123456

# Create a role "admins"
flask roles create admins

# Add the role "admins" to the user
flask roles add admin@inveniosoftware.org admins

# Give access to admin pages to the "admins" users
flask access allow admin-access role admins
echo '{"title": "Test title"}' | flask records create \
  -i deadbeef-9fe4-43d3-a08f-38c2b309afba --pid-minter recid
