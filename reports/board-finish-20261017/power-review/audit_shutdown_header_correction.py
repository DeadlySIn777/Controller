"""Read-only independent semantic and native-packet audit after KiCad export."""
from pathlib import Path
import hashlib
import json
import math
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / 'shutdown-header-correction-r1'
PRIOR = ROOT / 'reports/board-finish-20261011/continuation-r2/field-power/combined-power-source-r3-hierarchy/source-export/fresh.net'
TOKEN = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)', re.S)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse(path):
    stack = [[]]
    for m in TOKEN.finditer(path.read_text(encoding='utf-8')):
        t = m[1]
        if t == '(':
            stack.append([])
        elif t == ')':
            stack[-2].append(stack.pop())
        else:
            stack[-1].append(json.loads(t) if t.startswith('"') else t)
    assert len(stack) == 1 and len(stack[0]) == 1
    return stack[0][0]

def children(node, name):
    return [x for x in node if isinstance(x, list) and x and x[0] == name]

def child(node, name):
    result = children(node, name)
    assert len(result) == 1, name
    return result[0]

def atom(node, name):
    return child(node, name)[1]

def reverse(node):
    if isinstance(node, list):
        return [reverse(x) for x in node]
    return '1803578' if node == '1803277' else node

def components(tree):
    return {atom(c, 'ref'): c for c in children(child(tree, 'components'), 'comp')}

def nets(tree):
    result = {}
    for n in children(child(tree, 'nets'), 'net'):
        name = atom(n, 'name')
        assert name not in result
        # Numeric exporter net codes are ephemeral; compare all actual attributes and node roles.
        result[name] = sorted(json.dumps(x, sort_keys=True) for x in n[1:] if x[0] != 'code')
    return result

def main():
    construction = json.loads((OUT / 'construction-receipt.json').read_text())
    assert all(sha(Path(p)) == expected for p, expected in construction['input_sha256'].items())
    before, after = parse(PRIOR), parse(OUT / 'fresh.net')
    oldcomps, newcomps = components(before), components(after)
    assert oldcomps.keys() == newcomps.keys()
    changes = sorted(r for r in oldcomps if oldcomps[r] != newcomps[r])
    assert changes == ['J11002', 'J11004', 'J11006'], changes
    assert all(reverse(newcomps[r]) == oldcomps[r] for r in changes)
    assert nets(before) == nets(after), 'Any exact raw-net/node role change is rejected'
    assert child(before, 'libparts') == child(after, 'libparts')
    assert child(before, 'libraries') == child(after, 'libraries')
    nodes = sum(len(children(n, 'node')) for n in children(child(after, 'nets'), 'net'))
    net_count = len(nets(after))
    assert len(oldcomps) == 2723 and nodes == 9609 and net_count == 2388
    mappings = []
    for ref in changes:
        bp = OUT / 'native-bom-packet' / f'{ref}.before.footprint-chunk'
        ap = OUT / 'native-bom-packet' / f'{ref}.BOM-only.footprint-chunk'
        b = bp.read_bytes()
        a = ap.read_bytes()
        assert a.replace(b'(property "Value" "1803277"', b'(property "Value" "1803578"').replace(b'(property "MPN" "1803277"', b'(property "MPN" "1803578"') == b
        bt, at = parse(bp), parse(ap)
        assert children(bt, 'pad') == children(at, 'pad')
        assert children(bt, 'at') == children(at, 'at')
        pads = children(at, 'pad')
        assert {p[1] for p in pads} == {'1', '2'}
        pp = {p[1]: p for p in pads}
        assert all(atom(p, 'drill') == '1.2' for p in pads)
        centers = [list(map(float, child(pp[k], 'at')[1:3])) for k in ('1','2')]
        assert abs(math.dist(*centers) - 3.81) < 1e-12
        exported_pins = {}
        for net in children(child(after, 'nets'), 'net'):
            for node in children(net, 'node'):
                if atom(node, 'ref') == ref:
                    exported_pins[atom(node, 'pin')] = atom(net, 'name')
        native_pins = {p[1]: atom(p, 'net') for p in pads}
        assert exported_pins == native_pins, (ref, exported_pins, native_pins)
        mappings.append({'ref': ref, 'pad_drill_mm': 1.2, 'pad_pitch_mm': 3.81, 'source_and_native_exact_raw_pin_nets': native_pins, 'all_pad_and_pose_bytes_unchanged': True})
    receipt = {
        'utc': datetime.now(timezone.utc).isoformat(),
        'verdict': 'PASS_NATIVE_SCHEMATIC_EXPORT_EXACT_BOM_ONLY_DELTA_AND_NATIVE_PACKET',
        'native_export_exit_code': 0,
        'baseline_netlist_sha256': sha(PRIOR),
        'corrected_netlist_sha256': sha(OUT / 'fresh.net'),
        'construction_receipt_sha256': sha(OUT / 'construction-receipt.json'),
        'audit_script_sha256': sha(Path(__file__)),
        'components': len(newcomps), 'raw_named_nets': net_count, 'nodes': nodes,
        'changed_components': changes,
        'only_exported_Value_MPN_occurrences_changed': True,
        'all_exact_raw_net_attributes_nodes_pin_roles_unchanged': True,
        'all_library_definitions_and_library_records_unchanged': True,
        'native_chunk_copper_pad_pose_and_all_other_properties_unchanged': True,
        'pin_and_hole_checks': mappings,
        'all_original_bound_inputs_rehashed_unchanged': True,
        'no_board_written': True, 'adopted': False,
        'ERC': False, 'DRC': False, 'manufacturing_ready': False,
        'remaining': ['source/packet integration into exact final accepted candidate', 'fresh integrated API parity after BOM integration', 'mechanical mate/orientation/coding/harness review', 'current thermal fault and physical qualification remain separate'],
    }
    (OUT / 'verification-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'verdict': receipt['verdict'], 'components': len(newcomps), 'nets': net_count, 'nodes': nodes, 'changed': changes, 'pins_verified': len(mappings) * 2}))

if __name__ == '__main__':
    main()
