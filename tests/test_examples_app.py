# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test example app."""

import os
import signal
import subprocess
import time

import pytest


@pytest.yield_fixture
def example_app():
    """Example app fixture."""
    current_dir = os.getcwd()

    # Go to example directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exampleappdir = os.path.join(project_dir, 'examples')
    os.chdir(exampleappdir)

    # Setup example
    cmd = './app-setup.sh'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0

    # Starting example web app
    cmd = 'FLASK_APP=app.py flask run --debugger -p 5000'
    webapp = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              preexec_fn=os.setsid, shell=True)
    time.sleep(10)
    # Return webapp
    yield webapp

    # Stop server
    os.killpg(webapp.pid, signal.SIGTERM)

    # Tear down example app
    cmd = './app-teardown.sh'
    subprocess.call(cmd, shell=True)

    # Return to the original directory
    os.chdir(current_dir)


def test_example_app(example_app):
    """Test example app."""
    # Load fixtures
    cmd = './app-fixtures.sh'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0

    # Open page
    email = 'admin@inveniosoftware.org'
    password = '123456'
    cmd = """
        curl -c cookiefile http://0.0.0.0:5000/login/ -d \
            'csrf_token=None&next=&email={0}&password={1}' && \
        curl -b cookiefile http://0.0.0.0:5000/admin/recordmetadata/
        """.format(email, password)
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    assert 'deadbeef-9fe4-43d3-a08f-38c2b309afba' in output
