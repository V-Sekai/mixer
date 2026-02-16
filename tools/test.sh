#!/bin/sh
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux

cd "$(dirname "$0")/.."

# Check if MIXER_BLENDER_EXE_PATH is set
if [ -z "${MIXER_BLENDER_EXE_PATH:-}" ]; then
    echo "Error: MIXER_BLENDER_EXE_PATH environment variable is not set"
    echo "Please set it to the path of your Blender executable"
    exit 1
fi

# Run tests inside Blender
exec "$MIXER_BLENDER_EXE_PATH" --background --python tools/unittest_discover.py -- "$@"