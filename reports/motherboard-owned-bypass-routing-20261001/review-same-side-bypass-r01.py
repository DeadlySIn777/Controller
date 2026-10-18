"""Read-only native positive/adversarial exercise on real adopted circuits."""
import copy
import hashlib
import json
from pathlib import Path
import pcbnew
from check_same_side_bypass_r01 import check_group

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76/motherboard-literal38-neck-rule-candidate.kicad_pcb'
MAP = ROOT/'reports/motherboard-domains-20261001/source26-r76-r01/domain-map.json'
OWNERS = ROOT/'reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json'
GROUPS = ROOT/'reports/motherboard-owned-bypass-routing-20261001/source26-r73-typed-retry-r01/receipt.json'
OUT = Path(__file__).parent/'same-side-real-circuit-proof-r01.json'
assert not OUT.exists()
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
frozen = {str(p):sha(p) for p in [BASE,MAP,OWNERS,GROUPS,Path(__file__),Path(__file__).with_name('check_same_side_bypass_r01.py')]}
mapping = read(MAP)
assert mapping['input_sha256'][str(BASE)] == sha(BASE)
rows = {r['ref']:r for r in read(OWNERS)['capacitors']}
groups = {r['ref']:r for r in read(GROUPS)['owned_loops'] if r['retained']}
b = pcbnew.LoadBoard(str(BASE)); b.BuildConnectivity()
cu = {t.m_Uuid.AsString():t for t in b.GetTracks()}
fps = {f.GetReference():f for f in b.GetFootprints()}
positive = []
for ref in ['C17001','C13013']:
    row = rows[ref]
    supply = next(p.GetNetname() for p in fps[ref].Pads() if p.GetNumber()==row['cap_power'])
    g = dict(groups[ref], complete_supply_branch_UUIDs=[u for u in groups[ref]['new_UUIDs'] if cu[u].GetNetname()==supply])
    try:
        positive.append(dict(ref=ref, passed=True, group=g, review=check_group(b,g,row,mapping)))
    except ValueError as error:
        positive.append(dict(ref=ref, passed=False, reason=str(error)))
assert frozen == {p:sha(Path(p)) for p in frozen}
OUT.write_text(json.dumps(dict(read_only=True, inputs=frozen, actual_circuit_checks=positive,
                              passed=all(r['passed'] for r in positive),
                              no_change_to_prior_97_loop_acceptance=True,
                              new_router_authorized=False),indent=2)+'\n')
print([{k:v for k,v in r.items() if k in ['ref','passed','reason']} for r in positive])
