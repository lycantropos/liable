liable
======

[![](https://travis-ci.org/lycantropos/liable.svg?branch=master)](https://travis-ci.org/lycantropos/liable "Travis CI")
[![](https://codecov.io/gh/lycantropos/liable/branch/master/graph/badge.svg)](https://codecov.io/gh/lycantropos/liable "Codecov")
[![](https://img.shields.io/github/license/lycantropos/liable.svg)](https://github.com/lycantropos/liable/blob/master/LICENSE "License")
[![](https://badge.fury.io/py/liable.svg)](https://badge.fury.io/py/liable "PyPI")

In what follows `python3` is an alias for `python3.6` or any later
version.

Installation
------------

Install the latest `pip` & `setuptools` packages versions

```bash
python3 -m pip install --upgrade pip setuptools
```

### Release

Download and install the latest stable version from `PyPI` repository

```bash
python3 -m pip install --upgrade liable
```

### Developer

Download and install the latest version from `GitHub` repository

```bash
git clone https://github.com/lycantropos/liable.git
cd liable
python3 setup.py install
```

Bumping version
---------------

Install
[bumpversion](https://github.com/peritus/bumpversion#installation).

Choose which version number category to bump following [semver
specification](http://semver.org/).

Test bumping version

```bash
bumpversion --dry-run --verbose $VERSION
```

where `$VERSION` is the target version number category name, possible
values are `patch`/`minor`/`major`.

Bump version

```bash
bumpversion --verbose $VERSION
```

**Note**: to avoid inconsistency between branches and pull requests,
bumping version should be merged into `master` branch as separate pull
request.

Running tests
-------------

Plain

```bash
./run-plain-tests.sh -r $PATHS_TO_MODULES
```
where `$PATHS_TO_MODULES` is a list of whitespace-separated paths 
(absolute or relative) to target `Python` modules (e.g. `liable`).
Flag `-r` (or its analogue `--recursive`) says to search 
in given `Python` paths recursively.

Inside `Docker` container

```bash
docker-compose up
```

Inside `Docker` container with remote debugger

```bash
./set-dockerhost.sh docker-compose up
```

Bash script (e.g. can be used in `Git` hooks)
```bash
./run-tests.sh
```
