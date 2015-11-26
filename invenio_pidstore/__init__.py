# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Module that mints, stores, registers and resolves persistent identifiers.

Invenio-PIDStore is a core component of Invenio responsible for managing a
mapping from persistent identifiers to internal objects. The mapping is used
to resolve requests for e.g. an external integer record identifier to an
internal metadata record.

PIDStore consists of:

- `Persistent identifier API` - for working with persistent identifiers (
  create, reserve, register, delete, and redirect).
- `Resolver` - given a persistent identifier retrieve the assigned internal
  object.
- `Providers` - wrappers around a persistent identifier to provide extra
  functionality (e.g. interaction with remote services).
- `Minters` - small functions that are responsible for minting a specific
  persistent identifier type for a specific internal object type in as
  automatic way as possible.

Initialization
--------------
First create a Flask application (Flask-CLI is not needed for Flask
version 1.0+):

>>> from flask import Flask
>>> from flask_cli import FlaskCLI
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
>>> ext_cli = FlaskCLI(app)

You initialize PIDStore like a normal Flask extension, however Invenio-PIDStore
is dependent on Invenio-DB so you need to initialize both extensions:

>>> from invenio_db import InvenioDB
>>> from invenio_pidstore import InvenioPIDStore
>>> ext_db = InvenioDB(app)
>>> ext_pidstore = InvenioPIDStore(app)

In order for the following examples to work, you need to work within an
Flask application context so let's push one:

>>> ctx = app.app_context()
>>> ctx.push()

Also, for the examples to work we need to create the database and tables (note,
in this example we use an in-memory SQLite database):

>>> from invenio_db import db
>>> db.create_all()

Persistent identifiers
----------------------
Persistent identifiers map an external persistent identifier into an internal
object.

- A persistent identifier has **zero or one** assigned internal object.
- An internal object has **one or many** persistent identifiers.
- PIDStore can only map to internal objects which are **identified by UUIDs**.
- Persistent identifiers have a **type** (scheme) which is identified by a
  6 character string.
- All persistent identifier values are stored as string values, even if they
  may have a data type such as integer or UUID.

Persistent identifiers have a **state**:

- New: The persistent identifier is new.
- Reserved: The persistent identifier is reserved.
- Registered: The persistent identifier is registered.
- Redirected: The persistent identifier is redirected to another persistent
  identifier.
- Deleted: The persistent identifier is deleted/inactivated.

The different states might not all be relevant for different types of
identifiers. In addition persistent identifiers may be associated with a
specific **provider** (see below).

Creating PIDs
~~~~~~~~~~~~~
You create a persistent identifier like this:

>>> from invenio_pidstore.models import PersistentIdentifier
>>> pid = PersistentIdentifier.create('doi', '10.1234/foo')

By default, persistent identifiers are created in the `new` state, and has
no object assigned:

>>> from invenio_pidstore.models import PIDStatus
>>> pid.status == PIDStatus.NEW
True
>>> pid.has_object()
False

Assign objects
~~~~~~~~~~~~~~
You can either assign objects after having created the persistent identifier:

>>> import uuid
>>> pid.assign('rec', uuid.uuid4())
True

or alternatively simply assign the object while you create the persistent
identifier (and also set the correct status immediately):

>>> pid = PersistentIdentifier.create('recid', '10',
...     object_type='rec', object_uuid=uuid.uuid4(),
...     status=PIDStatus.REGISTERED)
>>> pid.has_object()
True

Note, that once an object has been assigned you cannot assign a new object
unless you use the ``overwrite`` parameter:

>>> pid.assign('rec', uuid.uuid4())
Traceback (most recent call last):
...
invenio_pidstore.errors.PIDObjectAlreadyAssigned: ...
>>> pid.assign('rec', uuid.uuid4(), overwrite=True)
True

Modifying status
~~~~~~~~~~~~~~~~
You can modify the state of a persistent identifier:

>>> pid = PersistentIdentifier.create('doi', '10.1234/bar')
>>> pid.reserve()
True
>>> pid.register()
True
>>> pid.delete()
True

Note that if you delete a persistent identifier in state *new* it will be
completely removed from the database. Also, certain state changes are not
allowed (e.g. here trying to reserve a deleted persistent identifier):

>>> pid.reserve()
Traceback (most recent call last):
...
invenio_pidstore.errors.PIDInvalidAction: ...

Redirecting
~~~~~~~~~~~
You can redirect a registered  persistent identifier to another persistent
identifier. This can be useful in cases where you merge two underlying
records or you have multiple identifier schemes but one is preferred over
another.

>>> pid = PersistentIdentifier.create('recid', '11',
...     status=PIDStatus.REGISTERED)
>>> pid.redirect(PersistentIdentifier.get('recid', '10'))
True

This allows you easily retrieve the persistent identifier being redirected to:

>>> pid.get_redirect()
<PersistentIdentifier recid:10 / rec:... (R)>

Resolver
--------
The resolver is responsible for retrieving an internal object for a given
persistent identifier.

Following is an example for creating a record resolver (note, you must have
Invenio-Records installed in order for this example to work):

>>> from invenio_pidstore.resolver import Resolver
>>> from invenio_records.api import Record
>>> resolver = Resolver(pid_type='recid', object_type='rec',
...    getter=Record.get_record)

Above creates a resolver that will translate ``recid`` persistent identifiers
to internal records. The getter argument must be a callable that takes one
argument which is the persistent identifiers object UUID.

Before we use the resolver, let's first create record and a persistent
identifier that we can use to test the resolver with:

>>> my_object_uuid = uuid.uuid4()
>>> record = Record.create(
...     {'title': 'PIDStore test'}, id_=my_object_uuid)
>>> pid = PersistentIdentifier.create(
...     'recid', '12', object_type='rec', object_uuid=my_object_uuid,
...     status=PIDStatus.REGISTERED)

Using the resolver, we can now retrieve the record like this:

>>> pid, record = resolver.resolve('12')
>>> pid
<PersistentIdentifier recid:12 / rec:... (R)>
>>> record
{'title': 'PIDStore test'}

The resolver will only resolve **registered** persistent identifiers. Any
non-resolvable value will raise an exception. E.g. trying to resolve a reserved
persistent identifier will throw a
:py:exc:`invenio_pidstore.errors.PIDUnregistered` exception:

>>> pid = PersistentIdentifier.create(
...     'recid', '13', object_type='rec', object_uuid=my_object_uuid,
...     status=PIDStatus.RESERVED)
>>> resolver.resolve('13')
Traceback (most recent call last):
...
invenio_pidstore.errors.PIDUnregistered

Providers
---------
Providers adds extra functionality persistent identifiers. Use cases for this
includes automatically creating the persistent identifier or retrieving the
persistent identifier from an external service.

PIDStore comes by default with a
:py:class:`invenio_pidstore.providers.recordid.RecordIdProvider` which will
create Invenio legacy integer record identifiers:

>>> from invenio_pidstore.providers.recordid import RecordIdProvider
>>> provider = RecordIdProvider.create()
>>> provider.pid.pid_type
'recid'
>>> provider.pid.pid_value
'1'

Creating your own provider
~~~~~~~~~~~~~~~~~~~~~~~~~~
In order to create your own provider, you need to inherit from
:py:class:`invenio_pidstore.providers.base.BaseProvider` and override the
methods you want to customize.

Here's a minimal example:

>>> from invenio_pidstore.providers.base import BaseProvider
>>> class MyProvider(BaseProvider):
...     pid_type = 'my'
...     pid_provider = 'test'
...     default_status = PIDStatus.RESERVED

Minters
-------
Minters are small functions that are responsible for minting a specific
persistent identifier type for a specific internal object type in as automatic
way as possible.

A minter takes two arguments:

- an `object uuid` of the internal object which the persistent identifier
  should be assigned to.
- a `dictionary object`, which the minter may extract information from, and/or
  store extra information in. For instance, if a record object is passed, it
  might contain the DOI which a provider should mint, or alternatively, if the
  persistent identifier is generated, the minter can store the generated value
  into the record.

Below is an example minter which mints external UUIDs (not to be confused with
the internal object UUIDs), and stores the generated UUID into the dictionary
object (which could be e.g. a record):

>>> import uuid
>>> def my_uuid_minter(object_uuid, data):
...     pid = PersistentIdentifier.create('myuuid', str(uuid.uuid4()))
...     data['uuid'] = str(pid.object_uuid)
...     return pid

Registering minters
~~~~~~~~~~~~~~~~~~~
Minters are usually used by other modules and thus registered on the
Flask application.

First import the proxy to the current application's PIDStore:

>>> from invenio_pidstore import current_pidstore

Next, register a minter:

>>> current_pidstore.register_minter('my_uuid_minter', my_uuid_minter)

You can retrieve registered minters from the extension as well:

>>> current_pidstore.minters['my_uuid_minter']
<function my_uuid_minter at ...>

Entry points loading
~~~~~~~~~~~~~~~~~~~~
PIDStore will automatically register minters defined by the entry point group
``invenio_pidstore.minters``.

Example:

.. code-block:: python

   # setup.py
   setup(
       # ...
       entry_points={
           'invenio_pidstore.minters': [
               'recid_minter = invenio_pidstore.minters:recid_minter',
           ]})

Above is equivalent to:

.. code-block:: python

   from invenio_pidstore.minters import recid_minter
   current_pidstore.register_minter('recid_minter', recid_minter)

"""

from __future__ import absolute_import, print_function

from .ext import InvenioPIDStore, current_pidstore
from .version import __version__

__all__ = ('__version__', 'InvenioPIDStore', 'current_pidstore')
