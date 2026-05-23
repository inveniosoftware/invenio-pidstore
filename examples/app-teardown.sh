#!/bin/sh
# SPDX-FileCopyrightText: 2016-2017 CERN.
# SPDX-License-Identifier: MIT

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

flask db drop --yes-i-know

# clean environment
[ -d instance ] && rm -Rf instance
[ -e cookiefile ] && rm -Rf cookiefile
