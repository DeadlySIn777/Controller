#!/bin/sh
# SPDX-License-Identifier: LicenseRef-Proprietary
# Build and run the cnc3 host tests (codec and driver core against the endpoint model).
# Host tests only: no LinuxCNC, no RTL, no hardware. Runs in any Linux with gcc; the evidence
# run uses the isolated Debian rootfs so AddressSanitizer is available (musl lacks it).
#   sh cnc3/tools/host_tests.sh [output-dir]
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out=${1:-/tmp/cnc3-host}
mkdir -p "$out"
flags="-std=c11 -O1 -g -Wall -Wextra -Werror -pedantic -Wconversion -Wshadow -D_DEFAULT_SOURCE"
san="-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer"
inc="-I$here/src -I$here/model -I$here/tests"
gcc $flags $san $inc "$here/src/cnc3_proto.c" "$here/tests/test_proto.c" -o "$out/test_proto"
gcc $flags $san $inc "$here/src/cnc3_proto.c" "$here/src/cnc3.c" "$here/model/cnc3_model.c" \
    "$here/tests/test_driver.c" -lm -o "$out/test_driver"
"$out/test_proto"
"$out/test_driver"
