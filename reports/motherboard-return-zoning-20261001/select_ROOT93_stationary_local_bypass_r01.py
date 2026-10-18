"""Exact native owner/pin selection; no source/placement/copper mutation."""
from pathlib import Path
import sys,json,math,hashlib
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_route_logic_return import mm
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-C11087-health-merged-r93/motherboard-bounded-merged-candidate.kicad_pcb')
O=Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json')
M=Path('reports/motherboard-return-zoning-20261001/C11087-moved-bypass-ground-transfer-r01/composed-current105-with-health4-manifest.json')
D=Path('reports/motherboard-return-zoning-20261001/ROOT93-stationary-bypass-selection-r01')
D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();c=b.GetConnectivity()
fps={f.GetReference():f for f in b.GetFootprints()}
pins={(ref,p.GetNumber()):p for ref,f in fps.items()for p in f.Pads()if p.GetNumber()}
owners=json.loads(O.read_text())
exclusion={r['ref']for r in json.loads(M.read_text())['owned_loops']}|{'C14804','C19042','C14012'}
cats={'supply_bypass','local_bypass','local_VDD_bypass','logic_bypass','status_local_bypass','MCU_VDD_bypass','window_supply_bypass','distributed_IO3_reset_bypass','microSD_local_bypass','USB_local_bypass'}
rows=[]
for r in owners['capacitors']:
    if r['ref']in exclusion or r['category']not in cats or not r['power_nodes']or not r['return_nodes']:
        continue
    numeric=int(r['ref'][1:])
    if numeric<12000 or 14000<=numeric<15000 or numeric>=20000:
        continue
    cp=pins[r['ref'],r['cap_power']];cr=pins[r['ref'],r['cap_return']]
    if cr.GetNetname()!='/LOGIC_GND':
        continue
    owning=[pins[n['ref'],n['pin']]for n in r['power_nodes']]
    owner=min(owning,key=lambda p:math.dist(mm(cp.GetPosition()),mm(p.GetPosition())))
    returns=[pins[n['ref'],n['pin']]for n in r['return_nodes']]
    peers={x.m_Uuid.AsString()for x in c.GetConnectedItems(cp)}
    retpeers={x.m_Uuid.AsString()for x in c.GetConnectedItems(cr)}
    power=owner.m_Uuid.AsString()in peers
    ret=any(p.m_Uuid.AsString()in retpeers for p in returns)
    d=math.dist(mm(cp.GetPosition()),mm(owner.GetPosition()))
    if d>5.0 or power and ret:
        continue
    rows.append(dict(ref=r['ref'],owner=r['owner'],category=r['category'],
       actual_power_pin=f'{owner.GetParentFootprint().GetReference()}.{owner.GetNumber()}',
       actual_power_net=cp.GetNetname(),actual_return=cr.GetNetname(),
       actual_distance_mm=d,cap_surface=b.GetLayerName(fps[r['ref']].GetLayer()),
       owner_surface=b.GetLayerName(owner.GetParentFootprint().GetLayer()),
       power_pair_connected=power,return_pair_connected=ret,
       cap_xy=mm(cp.GetPosition()),owner_xy=mm(owner.GetPosition())))
rows.sort(key=lambda r:r['actual_distance_mm'])
native=json.loads(B.with_name('drc.json').read_text())
assert not native['violations'] and not native['ignored_checks']
report=dict(passed=True,inspection_only=True,board=str(B),board_sha256=sha(B),
  owners_sha256=sha(O),excluded_current_105_and_dedicated_refs=sorted(exclusion),
  exact_selected_incomplete_stationary_LOGIC_local_bypass_rows=rows,
  no_bank_A_B_FPGA_power_precision_or_foreign_field_scope=True)
(D/'selection.json').write_text(json.dumps(report,indent=2)+'\n')
(D/'baseline-disposition.json').write_text(json.dumps(dict(board_sha256=sha(B),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=[]),indent=2)+'\n')
print(json.dumps(dict(passed=True,eligible=len(rows),refs=[r['ref']for r in rows],first=rows[:10])))
