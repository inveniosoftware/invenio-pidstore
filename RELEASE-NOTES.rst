===========================
 Invenio-PIDStore v1.0.0b1
===========================

Invenio-PIDStore v1.0.0b1 was released on November 8, 2016.

About
-----

Invenio module that stores and registers persistent identifiers.

Incompatible changes
--------------------

- Major rewrite of PIDStore in order to fix performance issues and
  clean up programmatic API. (#21) (#20) (#19) (#9) (#4) (#1)
- Refactoring and column name change for pidSTORE table.

New features
------------

- Adds basic CLI API.  (#42)
- Adds pid fetchers which enable to retrieve a PID from a previously
  minted data.
- Adds recid_fetcher which can retrieve pids minted by recid_minter.

Installation
------------

   $ pip install invenio-pidstore==1.0.0b1

Documentation
-------------

   https://invenio-pidstore.readthedocs.io/

Happy hacking and thanks for flying Invenio-PIDStore.

| Invenio Development Team
|   Email: info@inveniosoftware.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: https://twitter.com/inveniosoftware
|   GitHub: https://github.com/inveniosoftware/invenio-pidstore
|   URL: http://inveniosoftware.org
