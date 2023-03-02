..
    This file is part of Invenio.
    Copyright (C) 2015-2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 1.3.0 (released 2023-03-02)

- Replace deprecated flask_babelex dependency and imports
- Upgrade invenio-i18n

Version 1.2.4 (released 2022-11-18)

- Add translations workflow
- Add translations
- Add code formatters
- Update CI scripts

Version 1.2.3 (released 2022-02-28)

- Replaces pkg_resources with importlib for entry points iteration.

Version 1.2.2 (released 2021-01-19)

- Fix a consistency issue in the providers API where the create() method takes
  kwargs and passes them to __init__, but __init__ doesn't take kwargs by
  default. This made it difficult to exchange providers. Now __init__ takes
  kwargs by default.

Version 1.2.1 (released 2020-07-22)

- Support returning NEW and RESERVED PIDs by setting the `registered_only` flag.
- Support setting default status for PIDs with object type and uuid.

Version 1.2.0 (released 2020-03-09)

- Change exception interpolation for better aggregation
- Depend on Invenio-Base, Invenio-Admin, and Invenio-I18N to centralize
  3rd-party module dependencies.

Version 1.1.0 (released 2019-11-18)

- New record id provider v2 to generate random, base32, URI-friendly
  hyphen-separated, optionally checksummed PIDs

Version 1.0.0 (released 2018-03-23)

- Initial public release.
