liable
======

.. image:: https://travis-ci.org/lycantropos/liable.svg?branch=master
   :target: https://travis-ci.org/lycantropos/liable

.. image:: https://img.shields.io/github/license/lycantropos/liable.svg
   :target: https://github.com/lycantropos/liable/blob/master/LICENSE

.. image:: https://badge.fury.io/py/liable.svg
   :target: https://badge.fury.io/py/liable

In what follows ``python3`` is an alias for ``python3.6`` or any later
version.

Installation
------------

Install the latest ``pip`` & ``setuptools`` packages versions

.. code-block:: bash

   python3 -m pip install --upgrade pip setuptools

Release
^^^^^^^

Download and install the latest stable version from ``PyPI`` repository

.. code-block:: bash

   python3 -m pip install --upgrade liable

Developer
^^^^^^^^^

Download and install the latest version from ``GitHub`` repository

.. code-block:: bash

   git clone https://github.com/lycantropos/liable.git
   cd liable
   python3 setup.py install

Bumping version
---------------

Install
`bumpversion <https://github.com/peritus/bumpversion#installation>`_.

Choose which version number category to bump following `semver
specification <http://semver.org/>`_.

Test bumping version

.. code-block:: bash

   bumpversion --dry-run --verbose $VERSION

where ``$VERSION`` is the target version number category name, possible
values are ``patch``\ /\ ``minor``\ /\ ``major``.

Bump version

.. code-block:: bash

   bumpversion --verbose $VERSION

**Note**\ : to avoid inconsistency between branches and pull requests,
bumping version should be merged into ``master`` branch as separate pull
request.

Running tests
-------------

Plain

.. code-block:: bash

   ./run-plain-tests.sh -r $PATHS_TO_MODULES

where ``$PATHS_TO_MODULES`` is a list of whitespace-separated paths 
(absolute or relative) to target ``Python`` modules (e.g. ``liable``\ ).
Flag ``-r`` (or its analogue ``--recursive``\ ) says to search 
in given ``Python`` paths recursively.

Inside ``Docker`` container

.. code-block:: bash

   docker-compose up

Inside ``Docker`` container with remote debugger

.. code-block:: bash

   ./set-dockerhost.sh docker-compose up

Bash script (e.g. can be used in ``Git`` hooks)

.. code-block:: bash

   ./run-tests.sh
