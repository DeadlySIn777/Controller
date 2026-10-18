"""Read-only exact reconstruction of the frozen four-signal plus FAG source."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPORT = HERE.parent.parent.parent
FAG = REPORT / 'power-audit/fag-r07-repair'
FOUR = HERE.parent / 'four-path'
sys.path.insert(0, str(FAG)); sys.path.insert(0, str(FOUR))
import construct as C
import compose_four as F

R07_SHA = F.R07_SHA
EXPECTED = {
 'construction': 'b836c714122a68d6df48481f444119f5086fb22952df462e758a5ce335fa211b',
 'candidate': '198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab',
 'manifest': 'aa5108761ce96ae90696f53dbedc5c31504e83df23f1c419cc32d009dd0cfdcc',
 'constructor': '5486815b9120d20588b0434ed42e3a90cc970f39fc9250aa7164485366d70fa6',
}

def sha(raw): return hashlib.sha256(raw).hexdigest()

def validate_construction(construction_path, candidate_path):
    receipt_raw = Path(construction_path).read_bytes()
    if sha(receipt_raw) != EXPECTED['construction']:
        raise ValueError('Frozen combined construction receipt differs')
    receipt = json.loads(receipt_raw)
    if receipt['schema'] != 'fag-r07-repaired-source-construction-v1' or receipt['verdict'] != 'PASS_SOURCE_ONLY_NATIVE_OPEN':
        raise ValueError('Unexpected construction contract')
    if receipt['adopted'] or receipt['manufacturing_ready'] or receipt['native_jobs'] or receipt['gpu_jobs']:
        raise ValueError('Source construction claims unexpected adoption or native qualification')
    if sha(Path(C.__file__).read_bytes()) != EXPECTED['constructor']:
        raise ValueError('Frozen native chunk constructor differs')
    manifest_raw = (FAG / 'manifest.json').read_bytes()
    if sha(manifest_raw) != EXPECTED['manifest']:
        raise ValueError('Frozen FAG source manifest differs')
    manifest = json.loads(manifest_raw)
    for relative, expected in manifest['files'].items():
        path = (FAG / relative).resolve()
        if not path.is_relative_to(FAG.resolve()) or sha(path.read_bytes()) != expected:
            raise ValueError('Frozen FAG source member differs: ' + relative)
    for path, expected in receipt['source_files_sha256'].items():
        if sha(Path(path).read_bytes()) != expected:
            raise ValueError('Frozen combined construction input differs: ' + path)
    F.validate_construction(FOUR / 'construction.json', FOUR / 'r07-four-path.kicad_pcb')
    packet_raw = C.AUDIT.read_bytes()
    if sha(packet_raw) != receipt['whole_group_audit_sha256'] or sha(packet_raw) != C.AUDIT_SHA:
        raise ValueError('Frozen whole-group audit differs')
    packet = json.loads(packet_raw)
    donor, candidate, additions, generated, gap = C.reconstruct(
        packet, sha(packet_raw), F.R07.read_bytes(), C.P.I.DONOR.read_bytes(), C.W.TARGET.read_bytes())
    if sha(donor) != receipt['donor_sha256'] or donor != Path(receipt['donor_path']).read_bytes():
        raise ValueError('Repaired donor reconstruction differs')
    if {uid: sha(chunk) for uid, chunk in additions} != receipt['owned269'] or generated != receipt['new_generated19']:
        raise ValueError('Repaired donor ownership differs')
    if gap != receipt['minimum_owned_to_four_path_shared_layer_gap_mm']:
        raise ValueError('Combined shared-layer clearance evidence differs')
    raw = Path(candidate_path).read_bytes()
    if candidate != raw or sha(raw) != receipt['combined_sha256'] or sha(raw) != EXPECTED['candidate']:
        raise ValueError('Combined candidate is not the exact frozen replay')
    return {'verdict': 'PASS_SOURCE_CONSTRUCTION_NATIVE_OPEN', 'candidate_sha256': sha(raw),
            'r07_sha256': R07_SHA, 'all_r07_items_bytes_exact': True,
            'four_signal_items_exact': 18, 'field_return_items': 269,
            'total_new_copper_items': 287, 'minimum_shared_layer_gap_mm': gap,
            'scope_A': .096, 'adopted': False, 'manufacturing_ready': False}

def construction_hashes(construction_path):
    receipt = json.loads(Path(construction_path).read_bytes())
    result = dict(receipt['source_files_sha256'])
    for path in (Path(construction_path), FAG / 'manifest.json', FAG / 'retained-via-source-flags.json',
                 Path(receipt['donor_path']), FOUR / 'construction.json'):
        result[str(path.resolve())] = sha(path.read_bytes())
    for relative, expected in json.loads((FAG / 'manifest.json').read_bytes())['files'].items():
        result[str((FAG / relative).resolve())] = expected
    # The four constructor protects its whole transitive source closure as well.
    result.update(json.loads((FOUR / 'construction.json').read_bytes())['source_files_sha256'])
    return result
