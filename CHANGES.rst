Changes
=======

Version 1.0.0b2 (released 2016-08-10)
-------------------------------------

- Updates documentation.

- Updates example app.

- Fixes issue with tests directory being detected as a package and hence
  being installed due to the __init__.py in the tests package.


Version 1.0.0b1 (released 2016-11-08)
-------------------------------------

Incompatible changes
~~~~~~~~~~~~~~~~~~~~

- Major rewrite of PIDStore in order to fix performance issues and
  clean up programmatic API. (#21) (#20) (#19) (#9) (#4) (#1)
- Refactoring and column name change for pidSTORE table.

New features
~~~~~~~~~~~~

- Adds basic CLI API.  (#42)
- Adds pid fetchers which enable to retrieve a PID from a previously
  minted data.
- Adds recid_fetcher which can retrieve pids minted by recid_minter.

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
