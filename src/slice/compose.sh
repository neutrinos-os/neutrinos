#!/bin/sh
# Kept for one reason: sixteen accepted records cite this path as the command a
# measurement was taken with. Those citations are statements about what was
# executed, so rewriting them to say slice.py would falsify them; keeping the
# path working costs three lines and falsifies nothing.
#
# Nothing is decided here. slice.py holds the build, and reads
# NEUTRINOS_SLICE_ARM, NEUTRINOS_SLICE_VARIANT and NEUTRINOS_SLICE_ROLE itself
# so the documented invocations behave as they did. New callers should invoke
# slice.py with arguments: mise.toml sets sandbox.deny_env, so a mise task
# cannot pass an environment variable through at all.
set -eu
exec python3 "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/slice.py" build "$@"
