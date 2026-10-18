"""New four Source27 loops plus explicit C87 rebind; keep all historical groups."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck,dependencies
from hardware_route_owned_bypass_loops_r02 import actual_receiving_return_anchors
from hardware_route_logic_return import identity
B=Path('reports/motherboard-power-entry-20261001/Source27-closer-bypass-native-proof-r596/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');P=Path('reports/motherboard-power-entry-20261001/Source27-four-bypass-correct-orientation-r582/actual-Cu.json');K=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-minimal-cell-r350/receipt.json');H=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/final-binding-r02/current110-bypass-manifest.json');OWN=Path('reports/motherboard-bypass-owners-20261001/complete727-source27-staged-r04/capacitor-owners.json');O=Path('reports/motherboard-power-entry-20261001/Source27-five-bypass-current-manifest-r618');assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p)for p in[B,P,K,H,OWN,Path(__file__)]};old=json.loads(H.read_text());model=json.loads(OWN.read_text());owners={r['ref']:r for r in model['capacitors']};p=json.loads(P.read_text());bank=json.loads(K.read_text());b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();ts={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()}
groups=[]
for ref,owner in [('C11089','U11035'),('C11090','U11036'),('C11091','U11037'),('C11092','U11038')]:
 roles=['Short exact owning-VDD local bypass '+ref,'Short actual cap feed '+ref,'Actual local bypass supply transfer '+ref]
 ids=[r['uuid']for r in p['new_Cu']if r['role']in roles];assert len(ids)==3
 groups.append(dict(ref=ref,category='local_bypass',owner=owner,new_UUIDs=ids,retained=True,disposition='Actual new POR/Schmitt owning VDD receiving loop; separate long RAW source feed is excluded from local HF claim'))
c87=[r['uuid']for r in bank['exact_added_copper']if r['role']in['B_clock_buffer_actual_own_bypass','B_clock_buffer_actual_own_return']]
assert c87 and all(u in ts for u in c87)
groups.append(dict(ref='C11087',category='local_bypass',owner='U11033',new_UUIDs=c87,retained=True,disposition='Explicit bank B moved clock-buffer local-loop rebind; former five native objects retired and preserved in historical receipt'))
composed=[g for g in old['owned_loops']if g['ref']!='C11087']+groups;assert len(composed)==114;assert len({g['ref']for g in composed})==114
manifest=dict(owned_loops=composed,actual_filled_supply_branch_return_reviews=[],board_sha256=sha(B),owners_sha256=sha(OWN),Source27_staged_only=True,retained_previous_groups=109,explicit_rebound_previous_groups=['C11087'],new_groups=['C11089','C11090','C11091','C11092'],note='Must compose forthcoming ROOT104 ten added groups before adoption; this manifest binds current ROOT103-based report candidate only')
(O/'current114-local-loop-manifest.json').write_text(json.dumps(manifest,indent=2));reviews=[];anchor_reviews=[];checker=NativeCollectedAnnulusCheck(b,{})
for group in groups:
 ref=group['ref'];row=owners[ref];fp=fps[ref];supply=next(q.GetNetname()for q in fp.Pads()if q.GetNumber()==row['cap_power']);ret=next(q.GetNetname()for q in fp.Pads()if q.GetNumber()==row['cap_return']);decl=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10);checker.rows={supply:decl};checker.audits={}
 for uid in group['new_UUIDs']:
  t=ts[uid]
  if t.GetNetname()!=supply:continue
  try:q=checker.via(t,decl)if isinstance(t,pcbnew.PCB_VIA)else checker.segment(t,decl);reviews.append(dict(ref=ref,uuid=uid,passed=True,actual=identity(t),proof=q))
  except ValueError as e:reviews.append(dict(ref=ref,uuid=uid,passed=False,actual=identity(t),reason=str(e)))
 try:q=actual_receiving_return_anchors(b,{'owned_loops':[group]},model);anchor_reviews.append(dict(ref=ref,passed=True,actual=q))
 except ValueError as e:anchor_reviews.append(dict(ref=ref,passed=False,reason=str(e)))
assert all(sha(Path(p))==h for p,h in inputs.items());result=dict(input_hashes=inputs,frozen_dependencies=dependencies(),board_sha256=sha(B),actual_five_loop_reviews=reviews,actual_receiving_anchor_reviews=anchor_reviews,passed=all(q['passed']for q in reviews+anchor_reviews),signal_items_passed=sum(q['passed']for q in reviews),signal_items_rejected=sum(not q['passed']for q in reviews),reference_or_power_qualification_not_implied_by_native_DRC=True,manufacturing_ready=False);(O/'focused-five-loop-screen.json').write_text(json.dumps(result,indent=2));print('FIVE_LOOP_SCREEN',result['passed'],result['signal_items_passed'],result['signal_items_rejected'],[(q['ref'],q['passed'])for q in anchor_reviews],flush=True)
