..
    This file is part of Invenio.
    Copyright (C) 2015 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.

Changes
=======

Version 1.0.0 (released 2015-11-19)
-----------------------------------

Version 0.1.3 (released 2015-10-11)
-----------------------------------

Improved features
~~~~~~~~~~~~~~~~~

- Makes Datacite provider optional.

Version 0.1.2 (released 2015-10-02)
-----------------------------------

Bug fixes
~~~~~~~~~

- Removes calls to PluginManager consider_setuptools_entrypoints()
  removed in PyTest 2.8.0.
- Uses nested transactions instead of sub-transactions.
- Adds missing `invenio_base` dependency.

Version 0.1.1 (released 2015-08-25)
-----------------------------------

Improved features
~~~~~~~~~~~~~~~~~

- Adds category icon for the main sidebar-menu in the admin UI.

Bug fixes
~~~~~~~~~

- Adds missing `invenio_upgrader` dependency following its separation
  into standalone package.

- Fixes import of invenio_upgrader.

Version 0.1.0 (released 2015-07-16)
-----------------------------------

- Initial public release.
