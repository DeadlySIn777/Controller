"""Read-only current Source26 U20/U26 circuit and bypass reconciliation.

This uses actual fitted endpoints rather than coordinate targets. It composes
the adopted 106-loop manifest with only the two actual receiving-cell loops;
every original loop conductor must remain, and every Source remains unchanged.
"""
from pathlib import Path
import argparse,sys,json,subprocess
sys.path[:0]=[str(Path.cwd()/'tools')]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import mm

ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
B=a.board;O=a.out;assert not O.exists();O.mkdir()
M=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/current106-bypass-manifest.json')
OWN=Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json')
S=Path('hardware/motherboard');assert sha(S/'design.json')=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
R20=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-control-A-r236/receipt.json')
R26=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-Source-pending-r235/receipt.json')
inputs={str(q):sha(q)for q in[B,M,OWN,S/'design.json',S/'netlist.xml',R20,R26,Path(__file__)]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();co=b.GetConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()};pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()}
def pair(aa,bb,role):
 p,q=pads[aa],pads[bb];assert p.GetNetname()==q.GetNetname();joined=q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in co.GetConnectedItems(p)}
 return dict(role=role,start=list(aa),end=list(bb),literal_net=p.GetNetname(),start_mm=mm(p.GetPosition()),end_mm=mm(q.GetPosition()),passed=joined)
rows=[]
for src,recv in [('U11019','U11020'),('U11025','U11026')]:
 for s,e in [('6','1'),('4','3')]:rows.append(pair((src,s),(recv,e),'actual_private_health_control'))
for owner,target in [('U11020','U11022'),('U11026','U11028')]:rows.append(pair((owner,'6'),(target,'2'),'actual_LED_POWER_sink_contact'))
for owner,target in [('U11020','U11024'),('U11026','U11030')]:rows.append(pair((owner,'4'),(target,'2'),'actual_LED_POWER_sink_contact'))
for owner,cap,source in [('U11020','C11079','U11019'),('U11026','C11081','U11025')]:
 rows.extend([pair((cap,'1'),(owner,'5'),'actual_receiving_bypass_VCC'),pair((cap,'2'),(owner,'2'),'actual_receiving_bypass_Ground'),pair((owner,'2'),(source,'2'),'actual_Source_Ground_continuity'),pair((owner,'5'),(source,'5'),'actual_Source_supply_continuity')])
write(O/'actual-fitted-endpoint-circuit-proof.json',dict(passed=all(r['passed']for r in rows),board_sha256=sha(B),rows=rows,Source26_unchanged=True,no_empty_coordinate_targets=True,LED_paths_explicitly_power=True,physical_timing_or_all_temperature_current_qualified=False))
assert all(r['passed']for r in rows),'A fitted Source/control/LED/bypass endpoint is unjoined'
manifest=json.loads(M.read_text());assert len([g for g in manifest['owned_loops']if g['retained']])==106
for group in manifest['owned_loops']:
 if group['retained']:assert all(u in cu for u in group['new_UUIDs']),'Retained106 loop conductor retired without explicit rebind: '+group['ref']
owners={r['ref']:r for r in json.loads(OWN.read_text())['capacitors']}
for owner,cap,rp in [('U11020','C11079',R20),('U11026','C11081',R26)]:
 peer=json.loads(rp.read_text());ids=[]
 for row in peer['exact_added_copper']:
  if row['uuid']not in cu:continue
  role=row['role']
  if role in(owner+'_local_positive_transfer',owner+'_own_positive_F',owner+'_own_positive_B',owner+'_local_Source_return_stitch',owner+'_actual_ground_pin_transfer')or role.startswith(owner+'_own_ground'):ids.append(row['uuid'])
 positive=[u for u in ids if cu[u].GetNetname()==pads[(owner,'5')].GetNetname()];assert len(positive)==3
 assert not any(g['ref']==cap for g in manifest['owned_loops'])
 manifest['owned_loops'].append(dict(ref=cap,category=owners[cap]['category'],owner=owner,retained=True,new_UUIDs=sorted(set(ids)),Source_actual_receiver=True,LED_power_not_part_of_signal_loop=True))
manifest.update(board_sha256=sha(B),scope='Actual adopted106 local loops plus U20/C11079 and U26/C11081 receiving loops; complete current physical native proof required',current_native_proof_required=True)
write(O/'current108-bypass-manifest.json',manifest)
cmd=[sys.executable,'tools/hardware_verify_owned_bypass_batch.py','--board',str(B),'--owners',str(OWN),'--receipt',str(O/'current108-bypass-manifest.json'),'--out',str(O/'actual-current108-bypass-proof.json')]
run=subprocess.run(cmd,capture_output=True,text=True);(O/'actual-current108-command.txt').write_text(run.stdout+run.stderr);assert run.returncode==0,'Current108 strict receiving/reference proof failed'
for q,h in inputs.items():assert sha(q)==h
write(O/'receipt.json',dict(passed=True,board_sha256=sha(B),input_sha256=inputs,actual_fitted_endpoint_rows=len(rows),actual_loops=108,Source27_adopted=False,manufacturing_ready=False,global_power_capacity_qualified=False));print(json.dumps(dict(passed=True,actual_fitted_endpoints=len(rows),loops=108)),flush=True)
