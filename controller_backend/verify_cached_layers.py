"""Re-check the layer extraction filter against cached, digest-pinned layer archives.

Downloads nothing and never touches the provisioned rootfs. Run as root under
Linux (WSL) after ``fetch_debian_rootfs.py``. It reads the provenance record
``debian-rootfs-source.json`` beside ``$CONTROLLER_LAB_ROOTFS`` (default
``/root/.cache/controller-lab-linuxcnc/rootfs``), verifies each cached
``debian-layer-<digest>.tar.gz`` against its recorded SHA-256, extracts it
through ``rootfs_member_filter`` into a scratch ``filter-dryrun`` directory in
the same work directory, compares setuid/setgid modes and ownership with the
archive, then deletes the scratch directory. Current ``fetch_debian_rootfs.py``
removes layer archives after extraction, so this check is only possible where
an archive is still cached; a missing archive is reported, not fetched.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tarfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from controller_backend.fetch_debian_rootfs import extract_layer  # noqa: E402


def check_layer(archive, digest, scratch):
    result = {"digest": "sha256:" + digest, "archive": str(archive)}
    if not archive.is_file():
        result["status"] = "archive-not-cached"
        return result
    sha = hashlib.sha256()
    with archive.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    result["sha256_matches"] = sha.hexdigest() == digest
    if not result["sha256_matches"]:
        result["status"] = "digest-mismatch"
        return result
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
    kinds = {}
    for member in members:
        kind = ("directory" if member.isdir() else "symlink" if member.issym() else
                "hardlink" if member.islnk() else "file" if member.isreg() else
                "device_or_fifo" if member.isdev() else "other")
        kinds[kind] = kinds.get(kind, 0) + 1
    special = [m for m in members if m.isreg() and m.mode & (stat.S_ISUID | stat.S_ISGID)]
    result.update(members=len(members), kinds=kinds,
                  absolute_symlinks=sum(1 for m in members if m.issym() and m.linkname.startswith("/")),
                  setuid_or_setgid_files=len(special))
    root = scratch / "rootfs"
    shutil.rmtree(scratch, ignore_errors=True)
    root.mkdir(parents=True)
    try:
        try:
            extract_layer(archive, root)
        except tarfile.FilterError as error:
            result["status"] = "refused"
            result["refusal"] = str(error)
            return result
        preserved = 0
        for member in special:
            st = os.lstat(root / member.name)
            preserved += (st.st_mode & 0o7777, st.st_uid, st.st_gid) == (member.mode & 0o7777, member.uid, member.gid)
        result["setuid_or_setgid_mode_and_owner_preserved"] = preserved
        result["status"] = "extracted-without-refusal" if preserved == len(special) else "mode-or-owner-lost"
        return result
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        result["scratch_removed"] = not scratch.exists()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootfs", type=Path,
                        default=Path(os.environ.get("CONTROLLER_LAB_ROOTFS", "/root/.cache/controller-lab-linuxcnc/rootfs")))
    parser.add_argument("--output", type=Path, help="optional JSON result path")
    args = parser.parse_args()
    if os.name != "posix" or os.geteuid() != 0:
        raise SystemExit("Run as root under Linux so modes and ownership can be compared")
    work_dir = args.rootfs.resolve().parent
    provenance = json.loads((work_dir / "debian-rootfs-source.json").read_text())
    report = {
        "schema": 1,
        "evidence_class": "host test on Linux (WSL) of the extraction filter against the cached pinned layer; no download, no provisioning",
        "utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "manifest_digest": provenance.get("manifest_digest"),
        "provenance_record_keys": sorted(provenance),
        "layers": [],
    }
    for layer in provenance["layers"]:
        digest = layer["digest"].removeprefix("sha256:")
        report["layers"].append(check_layer(work_dir / ("debian-layer-" + digest + ".tar.gz"), digest,
                                            work_dir / "filter-dryrun"))
    report["success"] = all(entry["status"] == "extracted-without-refusal" for entry in report["layers"])
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
