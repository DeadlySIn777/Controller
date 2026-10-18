#!/bin/sh
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
export CONTROLLER_LAB_ROOTFS="$task_root"
test -f "$task_root/usr/include/linux/spi/spidev.h"
# Compile only the checked-in sources: discard the previous lab work copy.
rm -rf "$task_root/work/spidev-lab"
mkdir -p "$task_root/work/spidev-lab/src" "$task_root/work/spidev-lab/tests" "$task_root/work/spidev-lab/build" "$source_dir/evidence/spidev"
cp "$source_dir/src/cnc1.h" "$source_dir/src/spidev_transport.h" "$source_dir/src/spidev_transport.c" "$task_root/work/spidev-lab/src/"
cp "$source_dir/tests/test_spidev.c" "$task_root/work/spidev-lab/tests/"
cp "$source_dir/tests/test_spidev_cpp.cpp" "$task_root/work/spidev-lab/tests/"
cat > "$task_root/work/spidev-lab/run.sh" <<'RUN'
  set -eu
  cd /work/spidev-lab
  gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic -Isrc src/spidev_transport.c tests/test_spidev.c -o build/test_spidev
  ./build/test_spidev
  gcc -std=c11 -O1 -g -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined -fno-omit-frame-pointer -Isrc src/spidev_transport.c tests/test_spidev.c -o build/test_spidev_sanitized
  ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 ./build/test_spidev_sanitized
  gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic -Isrc -c src/spidev_transport.c -o build/spidev_transport.o
  g++ -std=c++17 -O2 -Wall -Wextra -Werror -pedantic -Isrc tests/test_spidev_cpp.cpp build/spidev_transport.o -o build/test_spidev_cpp
  ./build/test_spidev_cpp
  echo 'PASS C++ public header links to actual C object; no device opened'
RUN
unshare --mount --pid --net --fork --kill-child sh -c '
  task_root=$CONTROLLER_LAB_ROOTFS
  mount -t proc proc "$task_root/proc"
  exec chroot "$task_root" sh /work/spidev-lab/run.sh
'
chroot "$task_root" dpkg-query -W gcc g++ libc6-dev linux-libc-dev > "$source_dir/evidence/spidev/build-packages.tsv"
# Preserve the exact compiled common header and the executed test binaries for
# cnc1/tools/record_spidev_evidence.py (stdout is captured by the caller as tests.log).
mkdir -p "$source_dir/evidence/spidev/binaries"
cp "$task_root/work/spidev-lab/src/cnc1.h" "$source_dir/evidence/spidev/build-cnc1.h"
for binary in test_spidev test_spidev_sanitized test_spidev_cpp spidev_transport.o; do
  cp "$task_root/work/spidev-lab/build/$binary" "$source_dir/evidence/spidev/binaries/"
done
