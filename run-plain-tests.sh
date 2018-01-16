#!/usr/bin/env bash

set -ex

modules="$(liable modules "$@")"
liable utilities -t tests ${modules}
liable tests -t tests ${modules}
