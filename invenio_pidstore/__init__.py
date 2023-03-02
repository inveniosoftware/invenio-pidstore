# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
- `Fetchers` - small functions that are responsible for returning a minted
  persistent identifier.

Initialization
--------------
First create a Flask application with a Click support (Flask version 0.11+):

>>> from flask import Flask
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

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
You can create a persistent identifier like this:

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

Following is an example for creating a record resolver.

>>> from invenio_pidstore.resolver import Resolver
>>> records = {}
>>> resolver = Resolver(pid_type='recid', object_type='rec',
...    getter=records.get)

Above creates a resolver that will translate ``recid`` persistent identifiers
to internal records. The getter argument must be a callable that takes one
argument which is the persistent identifiers object UUID.

Before we use the resolver, let's first create record and a persistent
identifier that we can use to test the resolver with:

>>> my_object_uuid = uuid.uuid4()
>>> records[my_object_uuid] = {'title': 'PIDStore test'}
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
invenio_pidstore.errors.PIDUnregistered: ...

Providers
---------
Providers wrap the creation of persistent identifiers with extra functionality.
Use cases for this include automatically creating the persistent identifier or
retrieving the persistent identifier from an external service.

PIDStore comes by default with three providers:

- :py:class:`invenio_pidstore.providers.recordid_v2.RecordIdProviderV2` which
  creates random, checksummed, alphanumeric, PersistentIdentifier.
  (Recommended)
- :py:class:`invenio_pidstore.providers.datacite.DataCiteProvider` which
  creates and manages a PersistentIdentifier given a valid DOI.
- :py:class:`invenio_pidstore.providers.recordid.RecordIdProvider` which
  creates Invenio legacy integer record identifiers. (Not Recommended)

>>> from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
>>> provider = RecordIdProviderV2.create()
>>> provider.pid.pid_type
'recid'
>>> provider.pid.pid_value  # doctest: +SKIP
'3sbk2-5j060'

Configure ``PIDSTORE_RECORDID_OPTIONS`` in ``config.py``, to construct a
custom `pid_value`.

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


Fetchers
--------
Fetchers are small functions that are responsible for returning a minted
persistent identifier.

A fetcher takes two arguments:

- an `object uuid` of the internal object which the persistent identifier
  should be assigned to.
- a `dictionary object`, which the fetcher may extract information from. For
  instance, if a record object is passed, it might contain a previously minted
  DOI.

Below is an example fetcher which extracts external UUIDs previously minted in
the dictionary object (which could be e.g. a record):

>>> import uuid
>>> def my_uuid_fetcher(object_uuid, data):
...     return data['uuid']

Registering fetchers
~~~~~~~~~~~~~~~~~~~~
Fetchers are usually used by other modules and thus registered on the
Flask application.

First import the proxy to the current application's PIDStore:

>>> from invenio_pidstore import current_pidstore

Next, register a fetcher:

>>> current_pidstore.register_fetcher('my_uuid_fetcher', my_uuid_fetcher)

You can retrieve registered fetchers from the extension as well:

>>> current_pidstore.fetchers['my_uuid_fetcher']
<function my_uuid_fetcher at ...>


Entry points loading
~~~~~~~~~~~~~~~~~~~~
PIDStore will automatically register minters and fetchers defined by the entry
point groups ``invenio_pidstore.minters`` and . ``invenio_pidstore.fetchers``.

Example code:

.. code-block:: python

   # setup.py
   setup(
       # ...
       entry_points={
           'invenio_pidstore.minters': [
               'recid = invenio_pidstore.minters:recid_minter',
           ],
           'invenio_pidstore.fetchers': [
               'recid = invenio_pidstore.fetchers:recid_fetcher',
           ]})

Above is equivalent to:

.. code-block:: python

   from invenio_pidstore.minters import recid_minter
   from invenio_pidstore.fetchers import recid_fetcher
   current_pidstore.register_minter('recid', recid_minter)
   current_pidstore.register_fetcher('recid', recid_fetcher)

"""

from __future__ import absolute_import, print_function

from .ext import InvenioPIDStore
from .proxies import current_pidstore

__version__ = "1.3.0"

__all__ = ("__version__", "InvenioPIDStore", "current_pidstore")
