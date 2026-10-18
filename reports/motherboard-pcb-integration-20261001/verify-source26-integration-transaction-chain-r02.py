"""Reconcile every literal native transaction from adopted ROOT87 to ROOT101.

This proves the stated edit scope, not electrical qualification or adoption.
Fresh current power, circuit, source-connectivity, native and regression proof
remain mandatory. Failed trials are retained as failed trials.
"""
from pathlib import Path
import sys,json,collections,hashlib
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write,pad_template,footprint_name
from hardware_route_logic_return import identity
from hardware_merge_bounded_pcb_delta import pad_nets,sha_text
from hardware_stitch_owned_return_planes import definitions

root=Path(__file__).parent
out=root/'source26-root87-to101-transaction-chain-r02'
assert not out.exists();out.mkdir()
base=root/'source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb'
assert sha(base)=='0a9e4975b2d9cd90f7853884d626427fb089809c45ae5ed749472c68235e2d13'
source=Path('hardware/motherboard/design.json');netlist=Path('hardware/motherboard/netlist.xml')
assert sha(source)=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
assert sha(netlist)=='9f2c3c7b1e1b8f8cf108d0460dd0f709033f6ebdbf7f7a1b596abf1190eec633'
steps=[
 ('source26-motor-bank-A-merged-native-r88','merged'),
 ('source26-motor-bank-A-RAW-repair-trial-r89','RAW'),
 ('source26-BankA-RAW-and-sliver-repair-trial-r90','merged'),
 ('source26-BankA-health-supply-merged-trial-r91','merged'),
 ('source26-BankA-health-duplicate-via-repair-r92','duplicate'),
 ('source26-BankA-C11087-health-merged-r93','merged'),
 ('source26-BankA-health-DI7-merged-r94','merged'),
 ('source26-BankA-IO3-cleanup-merged-trial-r95b','merged'),
 ('source26-BankA-three-ordinary-merged-trial-r96','merged'),
 ('source26-BankA-three-bypass-merged-trial-r97','merged'),
 ('source26-BankA-health-U19-merged-trial-r98','merged'),
 ('source26-BankA-complete-IO3-cleanup-merged-trial-r99b','merged'),
 ('source26-BankA-health-U25-merged-trial-r100','merged'),
 ('source26-BankA-health-U25-C19033-merged-trial-r101','merged')]
frozen={str(p.resolve()):sha(p)for p in (base,source,netlist,Path(__file__))}
rows=[];before=pcbnew.LoadBoard(str(base));oldzones=definitions(base);before_path=base
for folder,kind in steps:
 p=root/folder;board=p/'motherboard-bounded-merged-candidate.kicad_pcb'
 assert board.exists()
 if kind=='RAW':
  proof=p/'proposed-exact-delta.json';scopepath=p/'bounded-scope.json'
  proposal=json.loads(proof.read_text());scope=json.loads(scopepath.read_text())
  assert proposal['before_board_sha256']==sha(before_path)
  frozen[str(scopepath.resolve())]=sha(scopepath)
 elif kind=='duplicate':
  proof=p/'receipt.json';receipt=json.loads(proof.read_text())
  assert receipt['passed'] and receipt['before_sha256']==sha(before_path) and receipt['board_sha256']==sha(board)
  assert receipt['exact_native_barrel_primitive_except_UUID_preserved'] and receipt['geometric_union_of_barrels_unchanged']
  scope=dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[receipt['removed_exact_duplicate_UUID']],reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exact duplicate barrel retirement; retained coincident actual physical barrel verified separately.')
 else:
  proof=p/'receipt.json';receipt=json.loads(proof.read_text());scope=receipt['scope']
  assert receipt['board_sha256']==sha(board)
  # A receipt must name this actual predecessor as an unchanged input.
  assert any(Path(k).resolve()==before_path.resolve() and h==sha(before_path) for k,h in receipt['input_sha256'].items())
 assert scope['electrical_source_unchanged'] and scope['reviewed_scope_reason']
 frozen[str(proof.resolve())]=sha(proof);frozen[str(board.resolve())]=sha(board)
 for suffix in ('.kicad_pro','.kicad_dru'):
  assert sha(base.with_suffix(suffix))==sha(board.with_suffix(suffix))
  frozen[str(board.with_suffix(suffix).resolve())]=sha(board.with_suffix(suffix))
 after=pcbnew.LoadBoard(str(board));newzones=definitions(board)
 oldcu={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};newcu={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
 actual_delta={u for u in set(oldcu)|set(newcu)if oldcu.get(u)!=newcu.get(u)}
 assert actual_delta==set(scope['reviewed_copper_delta_UUIDs']),(folder,'Copper outside exact scope')
 oldfp={f.GetReference():f for f in before.GetFootprints()};newfp={f.GetReference():f for f in after.GetFootprints()}
 assert set(oldfp)==set(newfp) and len(oldfp)==2688
 pose=lambda f:(tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())
 changed=[]
 for ref,first in oldfp.items():
  last=newfp[ref]
  assert first.m_Uuid.AsString()==last.m_Uuid.AsString() and footprint_name(first)==footprint_name(last) and pad_nets(first)==pad_nets(last)
  assert first.GetValue()==last.GetValue()
  if pose(first)!=pose(last):
   changed.append(ref);assert ref in scope['reviewed_footprint_references']
   if first.GetLayer()!=last.GetLayer():first.Flip(first.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
   first.SetPosition(last.GetPosition());first.SetOrientationDegrees(last.GetOrientationDegrees())
  assert collections.Counter(pad_template(q)for q in first.Pads())==collections.Counter(pad_template(q)for q in last.Pads()),(folder,ref,'Manufacturer lands changed')
 assert set(changed)==set(scope['reviewed_footprint_references'])
 assert set(oldzones)<=set(newzones)
 added=set(newzones)-set(oldzones);changedzones={u for u in oldzones if oldzones[u]!=newzones[u]}
 assert added==set(scope['reviewed_added_zone_UUIDs'])
 reviewed={r['uuid']:r for r in scope.get('reviewed_existing_zone_outline_deltas',[])}
 assert changedzones==set(reviewed)
 for u,r in reviewed.items():
  assert r['electrical_outline_correction_reason']
  assert sha_text(oldzones[u])==r['before_definition_sha256'] and sha_text(newzones[u])==r['after_definition_sha256']
 rows.append(dict(folder=folder,before_sha256=sha(before_path),board_sha256=sha(board),exact_changed_footprints=sorted(changed),exact_added_Cu=sorted(set(newcu)-set(oldcu)),exact_retired_Cu=sorted(set(oldcu)-set(newcu)),exact_modified_Cu=sorted(u for u in set(oldcu)&set(newcu)if oldcu[u]!=newcu[u]),exact_added_zones=sorted(added),exact_changed_zone_outlines=sorted(changedzones),manufacturer_lands_and_pin_nets_preserved=True,project_rules_unchanged=True))
 print(json.dumps({k:rows[-1][k]for k in ('folder','board_sha256')}),flush=True)
 before=after;oldzones=newzones;before_path=board
assert all(sha(Path(p))==h for p,h in frozen.items())
write(out/'receipt.json',dict(passed=True,scope='Literal complete native edit chain only; all electrical/current-board acceptance remains separate',input_sha256=frozen,adopted_baseline_sha256=sha(base),final_board_sha256=sha(before_path),steps=rows,source_population=2688,source_unchanged=True,manufacturing_ready=False,adopted=False))
print(json.dumps(dict(passed=True,steps=len(rows),final_board_sha256=sha(before_path))),flush=True)
