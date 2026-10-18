"""Offline scene metadata validation; no CAD parsing, rendering or machine access.

Usage: python -m controller_lab.scene_manifest examples/mr1-scene-draft.json

``registered`` means an externally supplied commissioning record matches this
exact metadata and geometry. It never grants motion authority. Records/profile
arguments are trusted caller inputs, not values taken from the imported scene.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys


ROLES = frozenset(("machine", "plate", "vise", "fixture", "stock", "tool", "reference"))
SOURCE_KINDS = frozenset(("synthetic", "user_import", "vendor_download", "cad_export"))
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _digest(value):
    return isinstance(value, str) and DIGEST.fullmatch(value) is not None


def _keys(value, required, optional, path, errors):
    if not isinstance(value, dict):
        errors.append({"path": path, "code": "object_required"})
        return False
    missing, extra = required - value.keys(), value.keys() - required - optional
    for key in sorted(missing):
        errors.append({"path": f"{path}.{key}", "code": "field_missing"})
    for key in sorted(extra):
        errors.append({"path": f"{path}.{key}", "code": "unknown_field"})
    return not missing and not extra


def _finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _transform(value, path, errors):
    if not _keys(value, {"translation_mm", "quaternion_xyzw"}, set(), path, errors):
        return
    for key, length in (("translation_mm", 3), ("quaternion_xyzw", 4)):
        vector = value[key]
        if not isinstance(vector, list) or len(vector) != length or not all(_finite_number(n) for n in vector):
            errors.append({"path": f"{path}.{key}", "code": "finite_vector_required"})
    quaternion = value["quaternion_xyzw"]
    if isinstance(quaternion, list) and len(quaternion) == 4 and all(_finite_number(n) for n in quaternion):
        if not math.isclose(math.hypot(*quaternion), 1.0, rel_tol=0, abs_tol=1e-6):
            errors.append({"path": f"{path}.quaternion_xyzw", "code": "quaternion_must_be_normalized"})


def _profile(value, path, errors):
    if not _keys(value, {"id", "version", "sha256"}, set(), path, errors):
        return
    for key in ("id", "version"):
        if not _text(value[key]):
            errors.append({"path": f"{path}.{key}", "code": "nonempty_string_required"})
    if not _digest(value["sha256"]):
        errors.append({"path": f"{path}.sha256", "code": "lowercase_sha256_required"})


def registration_binding_sha256(manifest, asset_id):
    """Bind reviewed metadata; call only on a structurally valid manifest.

    Includes ancestor frame transforms so moving a parent invalidates registration.
    Does not create or approve a commissioning record.
    """
    assets = [asset for asset in manifest["assets"] if asset["id"] == asset_id]
    if len(assets) != 1:
        raise ValueError("asset id must identify exactly one asset")
    asset = {key: value for key, value in assets[0].items() if key != "trust_level"}
    frames = {frame["id"]: frame for frame in manifest["frames"]}
    chain, seen, parent = [], set(), asset["parent_frame"]
    while parent is not None:
        if parent in seen or parent not in frames:
            raise ValueError("invalid parent frame graph")
        seen.add(parent)
        frame = frames[parent]
        chain.append(frame)
        parent = frame["parent_frame"]
    binding = {"version": 1, "machine_profile": manifest.get("machine_profile"),
               "asset": asset, "ancestor_frames": chain}
    encoded = json.dumps(binding, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_manifest(manifest, *, active_profile=None, registrations=None, asset_bytes=None):
    """Return errors, registration blockers and effective trust for each asset.

    ``asset_bytes`` maps asset ids to bytes, supplied explicitly by the caller.
    ``active_profile`` is an external {id, version, sha256} identity.
    ``registrations`` maps ids to external {record_id, binding_sha256} records.
    A record matches only after the supplied geometry bytes match provenance.
    No imported URI is fetched; no scene can authorize or request machine motion.
    """
    errors, blockers, results = [], [], []
    report = {"schema_version": 1, "structurally_valid": False, "errors": errors,
              "registration_blockers": blockers, "assets": results,
              "motion_authorized": False,
              "scope": "Offline metadata only; no CAD interpretation, collision proof, hardware connection or motion authority."}
    if not _keys(manifest, {"schema_version", "frames", "assets"}, {"title", "machine_profile", "notes"}, "scene", errors):
        return report
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        errors.append({"path": "scene.schema_version", "code": "unsupported_version"})
    for key in ("title", "notes"):
        if key in manifest and not _text(manifest[key]):
            errors.append({"path": f"scene.{key}", "code": "nonempty_string_required"})
    for key in ("frames", "assets"):
        if not isinstance(manifest[key], list) or not manifest[key]:
            errors.append({"path": f"scene.{key}", "code": "nonempty_array_required"})
    if not isinstance(manifest["frames"], list) or not isinstance(manifest["assets"], list):
        return report
    profile = manifest.get("machine_profile")
    if profile is not None:
        _profile(profile, "scene.machine_profile", errors)
    if active_profile is not None:
        _profile(active_profile, "context.active_profile", errors)
    if registrations is not None and not isinstance(registrations, dict):
        errors.append({"path": "context.registrations", "code": "object_required"})
        registrations = {}
    if asset_bytes is not None and not isinstance(asset_bytes, dict):
        errors.append({"path": "context.asset_bytes", "code": "object_required"})
        asset_bytes = {}
    registrations, asset_bytes = registrations or {}, asset_bytes or {}
    all_ids, frames = set(), {}
    for index, frame in enumerate(manifest["frames"]):
        path = f"scene.frames[{index}]"
        if not _keys(frame, {"id", "parent_frame", "transform"}, set(), path, errors):
            continue
        if not _text(frame["id"]):
            errors.append({"path": f"{path}.id", "code": "nonempty_string_required"})
            continue
        if frame["id"] in all_ids:
            errors.append({"path": f"{path}.id", "code": "duplicate_id"})
        all_ids.add(frame["id"])
        frames[frame["id"]] = frame
        if frame["parent_frame"] is not None and not _text(frame["parent_frame"]):
            errors.append({"path": f"{path}.parent_frame", "code": "parent_id_or_null_required"})
        _transform(frame["transform"], f"{path}.transform", errors)
    if sum(frame["parent_frame"] is None for frame in frames.values()) != 1:
        errors.append({"path": "scene.frames", "code": "exactly_one_root_frame_required"})
    for name, frame in frames.items():
        parent = frame["parent_frame"]
        if parent is not None and (not isinstance(parent, str) or parent not in frames):
            errors.append({"path": f"frame:{name}.parent_frame", "code": "unknown_parent_frame"})
        seen, current = set(), name
        while isinstance(current, str) and current in frames:
            if current in seen:
                errors.append({"path": f"frame:{name}", "code": "frame_cycle"})
                break
            seen.add(current)
            current = frames[current]["parent_frame"]
    valid_assets = []
    for index, asset in enumerate(manifest["assets"]):
        path = f"scene.assets[{index}]"
        if not _keys(asset, {"id", "asset_uri", "provenance", "parent_frame", "transform", "trust_level"}, {"role", "source_units", "label"}, path, errors):
            continue
        if not _text(asset["id"]):
            errors.append({"path": f"{path}.id", "code": "nonempty_string_required"})
            continue
        if asset["id"] in all_ids:
            errors.append({"path": f"{path}.id", "code": "duplicate_id"})
        all_ids.add(asset["id"])
        valid_assets.append(asset)
        for key in ("asset_uri", "label"):
            if key in asset and not _text(asset[key]):
                errors.append({"path": f"{path}.{key}", "code": "nonempty_string_required"})
        if "role" in asset and (not isinstance(asset["role"], str) or asset["role"] not in ROLES):
            errors.append({"path": f"{path}.role", "code": "unsupported_role"})
        if "source_units" in asset and asset["source_units"] not in ("mm", "in"):
            errors.append({"path": f"{path}.source_units", "code": "explicit_mm_or_in_required"})
        if asset["trust_level"] not in ("visual_only", "registered"):
            errors.append({"path": f"{path}.trust_level", "code": "unsupported_trust_level"})
        if not isinstance(asset["parent_frame"], str) or asset["parent_frame"] not in frames:
            errors.append({"path": f"{path}.parent_frame", "code": "unknown_parent_frame"})
        _transform(asset["transform"], f"{path}.transform", errors)
        provenance = asset["provenance"]
        if _keys(provenance, {"source_kind"}, {"sha256", "notes"}, f"{path}.provenance", errors):
            if not isinstance(provenance["source_kind"], str) or provenance["source_kind"] not in SOURCE_KINDS:
                errors.append({"path": f"{path}.provenance.source_kind", "code": "unsupported_source_kind"})
            if "sha256" in provenance and not _digest(provenance["sha256"]):
                errors.append({"path": f"{path}.provenance.sha256", "code": "lowercase_sha256_required"})
            if "notes" in provenance and not _text(provenance["notes"]):
                errors.append({"path": f"{path}.provenance.notes", "code": "nonempty_string_required"})
    structurally_valid = not errors
    for asset in valid_assets:
        name, reasons = asset["id"], []
        if not isinstance(asset.get("role"), str) or asset["role"] not in ROLES:
            reasons.append("role_missing_or_invalid")
        if asset.get("source_units") not in ("mm", "in"):
            reasons.append("source_units_missing_or_invalid")
        if profile is None:
            reasons.append("machine_profile_missing")
        elif active_profile is None:
            reasons.append("active_machine_profile_unavailable")
        elif profile != active_profile:
            reasons.append("machine_profile_identity_version_or_digest_mismatch")
        provenance = asset["provenance"] if isinstance(asset["provenance"], dict) else {}
        digest = provenance.get("sha256")
        verified = False
        if not _digest(digest):
            reasons.append("geometry_digest_missing_or_invalid")
        elif not isinstance(asset_bytes.get(name), bytes):
            reasons.append("geometry_bytes_not_supplied_for_digest_verification")
        elif hashlib.sha256(asset_bytes[name]).hexdigest() != digest:
            reasons.append("geometry_digest_mismatch")
        else:
            verified = True
        binding = registration_binding_sha256(manifest, name) if structurally_valid else None
        record = registrations.get(name)
        if not isinstance(record, dict) or set(record) != {"record_id", "binding_sha256"} or not _text(record.get("record_id")) or not _digest(record.get("binding_sha256")):
            reasons.append("external_commissioning_record_missing_or_invalid")
        elif binding != record["binding_sha256"]:
            reasons.append("commissioning_record_does_not_match_scene_binding")
        if not structurally_valid:
            reasons.append("scene_structure_invalid")
        effective = "registered" if asset["trust_level"] == "registered" and not reasons else "visual_only"
        if asset["trust_level"] == "visual_only":
            reasons.append("asset_explicitly_visual_only")
        results.append({"id": name, "requested_trust": asset["trust_level"], "effective_trust": effective,
                        "source_to_mm_scale": 1.0 if asset.get("source_units") == "mm" else 25.4 if asset.get("source_units") == "in" else None,
                        "geometry_digest_verified": verified, "registration_binding_sha256": binding,
                        "registration_blockers": reasons, "motion_authorized": False})
        blockers.extend({"asset_id": name, "code": reason} for reason in reasons)
    report["structurally_valid"] = structurally_valid
    return report


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"nonfinite JSON value: {value}")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_object, parse_constant=_invalid_constant)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--profile", type=Path, help="External active profile identity JSON")
    parser.add_argument("--registrations", type=Path, help="External reviewed registration records JSON")
    parser.add_argument("--asset-bytes", action="append", default=[], metavar="ID=PATH", help="Read only this explicitly supplied local asset file; no CAD parsing")
    args = parser.parse_args(argv)
    try:
        contents = {}
        for entry in args.asset_bytes:
            name, separator, path = entry.partition("=")
            if not separator or not name or not path or name in contents:
                raise ValueError("--asset-bytes requires a unique ID=PATH")
            contents[name] = Path(path).read_bytes()
        report = validate_manifest(load_json(args.manifest),
                                   active_profile=load_json(args.profile) if args.profile else None,
                                   registrations=load_json(args.registrations) if args.registrations else None,
                                   asset_bytes=contents)
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0 if report["structurally_valid"] else 2
    except (OSError, ValueError, OverflowError) as exc:
        print(json.dumps({"structurally_valid": False, "motion_authorized": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
