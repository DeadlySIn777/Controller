#!/bin/sh
# Run only against this task's isolated rootfs, never the host filesystem.
set -eu
task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
export CONTROLLER_LAB_ROOTFS="$task_root"
test -f "$task_root/etc/debian_version"
test "$task_root" != /
mkdir -p "$task_root/dev/shm" "$task_root/tmp" "$task_root/proc"
chmod 1777 "$task_root/dev/shm" "$task_root/tmp"
for device in null zero random urandom; do
    case "$device" in null) minor=3;; zero) minor=5;; random) minor=8;; urandom) minor=9;; esac
    if [ ! -e "$task_root/dev/$device" ]; then mknod "$task_root/dev/$device" c 1 "$minor"; fi
    chmod 666 "$task_root/dev/$device"
done
cp /etc/resolv.conf "$task_root/etc/resolv.conf"
printf '#!/bin/sh\nexit 101\n' > "$task_root/usr/sbin/policy-rc.d"
chmod 755 "$task_root/usr/sbin/policy-rc.d"
chroot "$task_root" /bin/sh -c 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y linuxcnc-uspace=1:2.9.4-2+deb13u1'
chroot "$task_root" /bin/sh -c 'id cnclab >/dev/null 2>&1 || useradd --create-home --uid 1000 cnclab'
chroot "$task_root" dpkg-query -W linuxcnc-uspace python3
