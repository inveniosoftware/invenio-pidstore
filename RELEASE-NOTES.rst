===========================
 Invenio-PIDStore v1.0.0a9
===========================

Invenio-PIDStore v1.0.0a9 was released on July 4, 2016.

About
-----

Invenio module that stores and registers persistent identifiers.

*This is an experimental development preview release.*

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

   $ pip install invenio-pidstore==1.0.0a9

Documentation
-------------

   http://pythonhosted.org/invenio-pidstore/

Happy hacking and thanks for flying Invenio-PIDStore.

| Invenio Development Team
|   Email: info@inveniosoftware.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: https://github.com/inveniosoftware/invenio-pidstore
|   URL: http://inveniosoftware.org
