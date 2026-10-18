"""Fetch the official Debian OCI rootfs for an isolated software-only test.

This downloads/extracts files only. It does not install host packages, start
LinuxCNC, mount host devices, or connect a machine. Run under Linux with a new
empty destination. The trust anchor is the pinned manifest digest: the manifest
and every layer are SHA-256 verified before extraction, and each layer member is
additionally checked by ``rootfs_member_filter`` so that no path, hardlink or
symlink-following write can land outside the destination and no device node is
created, while the file modes (including setuid bits) of a Debian rootfs are kept.

The destination's parent directory is used as the work directory: layer
archives are downloaded there temporarily (and removed after extraction) and
``debian-rootfs-source.json`` (the provenance record) is written there next to
the rootfs. The companion launchers (provision_isolated_runtime.sh,
run_isolated_simulation.sh, cnc1/tools/*.sh) locate the rootfs through
``$CONTROLLER_LAB_ROOTFS`` (default ``/root/.cache/controller-lab-linuxcnc/rootfs``)
and read the provenance file from its parent. This script defaults its
destination to the same variable, so set it once for every step or leave it
unset to use the default path.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tarfile
import urllib.request


def _inside(root, path):
    """True when ``path`` (after resolving symlinks already on disk) stays under ``root``."""
    real_root = os.path.realpath(root)
    real_path = os.path.realpath(os.path.join(real_root, path))
    return real_path == real_root or real_path.startswith(real_root + os.sep)


def _escapes_lexically(path):
    """True when a POSIX tar path climbs above its root without touching the disk."""
    depth = 0
    for part in path.split("/"):
        if part == "..":
            depth -= 1
            if depth < 0:
                return True
        elif part not in ("", "."):
            depth += 1
    return False


def rootfs_member_filter(root):
    """Build a tarfile extraction filter for an OCI rootfs layer.

    Unlike ``filter="tar"`` this keeps mode bits (a Debian rootfs needs setuid
    on su/mount/passwd) and allows absolute symlink targets, which are rootfs
    relative under chroot (Debian ships chains such as
    ``/usr/bin/awk -> /etc/alternatives/awk -> /usr/bin/mawk``). It rejects:

    * member paths that are absolute, contain ``..`` or, after following
      symlinks already extracted, resolve outside ``root`` (so a layer with
      ``usr -> /etc`` followed by ``usr/passwd`` is refused at ``usr/passwd``);
    * hardlink targets that are absolute or resolve outside ``root`` (tarfile
      links them from the host path ``root/linkname``);
    * symlink targets that lexically climb above the rootfs;
    * every device node.
    """
    def _filter(member, dest_path):
        name = member.name
        if name.startswith("/") or _escapes_lexically(name) or not _inside(root, name):
            raise tarfile.FilterError("Unsafe layer member path: " + name)
        if member.isdev():
            raise tarfile.FilterError("Device node in layer: " + name)
        link = member.linkname
        if member.islnk():
            if link.startswith("/") or _escapes_lexically(link) or not _inside(root, link):
                raise tarfile.FilterError("Unsafe hardlink target: " + name + " -> " + link)
        elif member.issym():
            target = link if link.startswith("/") else os.path.dirname(name) + "/" + link
            if _escapes_lexically(target):
                raise tarfile.FilterError("Unsafe symlink target: " + name + " -> " + link)
        return member
    return _filter


def fetch(url, token=None, accept=None):
    headers = {"User-Agent": "controller-lab-offline-audit"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if accept:
        headers["Accept"] = accept
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "destination",
        type=Path,
        nargs="?",
        default=Path(os.environ.get("CONTROLLER_LAB_ROOTFS", "/root/.cache/controller-lab-linuxcnc/rootfs")),
        help="empty rootfs destination (default: $CONTROLLER_LAB_ROOTFS or /root/.cache/controller-lab-linuxcnc/rootfs)",
    )
    args = parser.parse_args()
    root = args.destination.resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit("Destination must be empty; refusing to merge root filesystems")
    root.mkdir(parents=True, exist_ok=True)
    work_dir = root.parent
    print("Work directory for layer archives and provenance:", work_dir, flush=True)
    token = json.load(fetch("https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/debian:pull"))["token"]
    base = "https://registry-1.docker.io/v2/library/debian/"
    accept = "application/vnd.oci.image.index.v1+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.docker.distribution.manifest.v2+json"
    manifest_digest = "sha256:7792b1f7702a86946cd518db72b6a407302c3e9bc1635634368b878189e8221c"
    raw_manifest = fetch(base + "manifests/" + manifest_digest, token, accept).read()
    if "sha256:" + hashlib.sha256(raw_manifest).hexdigest() != manifest_digest:
        raise SystemExit("Downloaded manifest digest mismatch")
    manifest = json.loads(raw_manifest)
    for layer in manifest["layers"]:
        digest = layer["digest"].removeprefix("sha256:")
        archive = work_dir / ("debian-layer-" + digest + ".tar.gz")
        with fetch(base + "blobs/" + layer["digest"], token) as response, archive.open("wb") as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
            raise SystemExit("Downloaded layer digest mismatch")
        with tarfile.open(archive) as tar:
            try:
                tar.extractall(root, filter=rootfs_member_filter(root))
            except tarfile.FilterError as error:
                raise SystemExit(str(error)) from error
        archive.unlink()
        print("Verified and extracted", layer["digest"], flush=True)
    (work_dir / "debian-rootfs-source.json").write_text(json.dumps({"image": "docker.io/library/debian:trixie-slim", "manifest_digest": manifest_digest, "layers": manifest["layers"]}, indent=2))


if __name__ == "__main__":
    main()
