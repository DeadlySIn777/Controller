"""Fetch the official Debian OCI rootfs for an isolated software-only test.

This downloads/extracts files only. It does not install host packages, start
LinuxCNC, mount host devices, or connect a machine. Run under Linux with a new
empty destination. The trust anchor is the pinned manifest digest: the tag's
image index must list that digest for linux/amd64, the image config named by the
manifest must declare linux/amd64, and the manifest, config and every layer are
SHA-256 verified before extraction, and each layer member is
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

    Unlike ``filter="tar"`` or ``filter="data"`` this keeps mode bits and
    ownership (a Debian rootfs needs setuid on su/mount/passwd) and allows
    absolute symlink targets, which are rootfs relative under chroot (Debian
    ships ``/var/run -> /run`` and alternatives chains such as
    ``/usr/bin/awk -> /etc/alternatives/awk``). It rejects:

    * member paths that are empty, absolute or contain ``..`` above the root;
    * regular files, directories, hardlinks and other non-symlink members whose
      host path, after following symlinks already on disk, resolves outside
      ``root`` (tarfile opens/chmods/chowns that path, so a layer with
      ``usr -> /etc`` followed by ``usr/passwd`` is refused at ``usr/passwd``);
    * symlink members whose parent directory resolves outside ``root`` (tarfile
      replaces an existing link in place, so only the parent must be contained)
      or whose final name component is empty, ``.`` or ``..`` (``p -> .``
      followed by ``p/..`` would otherwise name the directory above ``root``);
    * hardlink targets that are absolute or resolve outside ``root`` (tarfile
      links them from the host path ``root/linkname``);
    * relative symlink targets that lexically climb above the rootfs;
    * every character/block device node and FIFO (``TarInfo.isdev()``).

    OCI whiteout entries are not interpreted; the pinned image has one layer.
    """
    def _filter(member, dest_path):
        name = member.name
        if not name or name.startswith("/") or _escapes_lexically(name):
            raise tarfile.FilterError("Unsafe layer member path: " + repr(name))
        if member.issym():
            # Only the parent must resolve inside root (tarfile replaces an
            # existing link in place), but the link's own final component must
            # then be a real name: ``p/..`` or ``p/.`` would make the link path
            # the parent directory itself, which can sit above root.
            stripped = name.rstrip("/")
            if os.path.basename(stripped) in ("", ".", ".."):
                raise tarfile.FilterError("Unsafe symlink member name: " + repr(name))
            contained = _inside(root, os.path.dirname(stripped) or ".")
        else:
            contained = _inside(root, name)
        if not contained:
            raise tarfile.FilterError("Layer member escapes destination: " + name)
        if member.isdev():
            raise tarfile.FilterError("Device node or FIFO in layer: " + name)
        link = member.linkname
        if member.islnk():
            if not link or link.startswith("/") or _escapes_lexically(link) or not _inside(root, link):
                raise tarfile.FilterError("Unsafe hardlink target: " + name + " -> " + link)
        elif member.issym():
            target = link if link.startswith("/") else os.path.dirname(name) + "/" + link
            if _escapes_lexically(target):
                raise tarfile.FilterError("Unsafe symlink target: " + name + " -> " + link)
        return member
    return _filter


def require_link_fallback_refilter():
    """Refuse a tarfile without the CVE-2025-4138 link-fallback re-filter.

    When creating a link fails, tarfile falls back to extracting the link's
    target member at the link path. CPython releases before the fix
    (3.12.0-3.12.10, 3.13.0-3.13.3 and the 3.8-3.11 filter backports) did that
    without passing the fallback member through the extraction filter, so the
    filter above would not be the only gate. Fixed releases (3.12.11+, 3.13.4+,
    3.14+ and patched backports) re-filter it and define
    ``tarfile.LinkFallbackError``; that attribute is the feature test.
    """
    if not hasattr(tarfile, "LinkFallbackError"):
        raise RuntimeError(
            "This Python's tarfile lacks the CVE-2025-4138 link-fallback re-filter "
            "(tarfile.LinkFallbackError); use CPython 3.12.11+, 3.13.4+ or 3.14+ to extract layers")


def extract_layer(archive, root):
    """Extract one digest-verified layer archive into ``root`` through the filter.

    Raises ``RuntimeError`` before opening the archive when this Python lacks
    the link-fallback re-filter, and ``tarfile.FilterError`` (a
    ``tarfile.TarError``) on the first refused member; members before it may
    already have been written inside ``root``.
    """
    require_link_fallback_refilter()
    with tarfile.open(archive) as tar:
        tar.extractall(root, filter=rootfs_member_filter(root))


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
    try:
        require_link_fallback_refilter()  # before any download or mkdir
    except RuntimeError as error:
        raise SystemExit(str(error))
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
    tag = "trixie-slim"
    platform = {"os": "linux", "architecture": "amd64"}
    # Resolve the tag's image index and require the pinned digest to be listed
    # for linux/amd64, so the tag/architecture recorded below are verified
    # properties of the registry state, not a hand-written label.
    index = json.loads(fetch(base + "manifests/" + tag, token, accept).read())
    listed = [
        entry for entry in index.get("manifests", [])
        if entry.get("digest") == manifest_digest
        and entry.get("platform", {}).get("os") == platform["os"]
        and entry.get("platform", {}).get("architecture") == platform["architecture"]
    ]
    if not listed:
        raise SystemExit("Pinned manifest digest is not listed for linux/amd64 under tag " + tag)
    raw_manifest = fetch(base + "manifests/" + manifest_digest, token, accept).read()
    if "sha256:" + hashlib.sha256(raw_manifest).hexdigest() != manifest_digest:
        raise SystemExit("Downloaded manifest digest mismatch")
    manifest = json.loads(raw_manifest)
    config_digest = manifest["config"]["digest"]
    raw_config = fetch(base + "blobs/" + config_digest, token).read()
    if "sha256:" + hashlib.sha256(raw_config).hexdigest() != config_digest:
        raise SystemExit("Downloaded image config digest mismatch")
    config = json.loads(raw_config)
    if config.get("os") != platform["os"] or config.get("architecture") != platform["architecture"]:
        raise SystemExit("Image config platform is %s/%s, expected linux/amd64" % (config.get("os"), config.get("architecture")))
    print("Verified tag", tag, "-> ", manifest_digest, "for", config["os"] + "/" + config["architecture"], flush=True)
    for layer in manifest["layers"]:
        digest = layer["digest"].removeprefix("sha256:")
        archive = work_dir / ("debian-layer-" + digest + ".tar.gz")
        with fetch(base + "blobs/" + layer["digest"], token) as response, archive.open("wb") as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
            raise SystemExit("Downloaded layer digest mismatch")
        try:
            extract_layer(archive, root)
        except tarfile.FilterError as error:
            raise SystemExit(str(error)) from error
        archive.unlink()
        print("Verified and extracted", layer["digest"], flush=True)
    (work_dir / "debian-rootfs-source.json").write_text(json.dumps({
        "image": "docker.io/library/debian:" + tag,
        "tag_verified": "pinned manifest digest listed under tag for linux/amd64 in the image index at fetch time",
        "platform": {"os": config["os"], "architecture": config["architecture"]},
        "manifest_digest": manifest_digest,
        "config_digest": config_digest,
        "layers": manifest["layers"],
    }, indent=2))


if __name__ == "__main__":
    main()
