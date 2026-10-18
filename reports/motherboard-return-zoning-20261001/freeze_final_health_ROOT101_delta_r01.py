"""Freeze exact current health delta for merger composition on ROOT102, retaining its two-cap increment."""
from pathlib import Path
import argparse,sys,hashlib,json
sys.path.insert(0,str(Path.cwd()/'tools'))
from hardware_map_motherboard_domains import sha,write
from hardware_build_assembly import parse,dump,children
from hardware_merge_bounded_pcb_delta import objects,without_generated_fills,reference,zone_definition,unchanged_properties
p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists();a.out.mkdir()
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/motherboard-bounded-merged-candidate.kicad_pcb');assert sha(B)=='81c0d8c2f4cc70140deff90266c92fd693e9c34923da62610eee49305f413226'
M102=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-same-side-bypass-restored-r06/current108-bypass-manifest.json');C102=M102.parent/'motherboard-two-same-side-bypass-candidate.kicad_pcb';assert sha(C102)=='769541d11876ea0050240ec065f6b0b85bff19c7c8324f1c26b9b637212a8af5'
inputs={str(q):sha(q)for q in(B,a.board,a.manifest,C102,M102,Path(__file__))};before=parse(without_generated_fills(B.read_text()));after=parse(without_generated_fills(a.board.read_text()))
bf={reference(f):f for f in children(before,'footprint')};af={reference(f):f for f in children(after,'footprint')};assert set(bf)==set(af);poses=[]
for ref in bf:
 if dump(bf[ref])!=dump(af[ref]):assert unchanged_properties(bf[ref])==unchanged_properties(af[ref]);poses.append(ref)
assert set(poses)=={'U11019','C11078','U11020','C11079','U11026','C11081'}
cu=[]
for kind in('segment','via','arc'):
 old=objects(before,kind);new=objects(after,kind)
 for u in sorted(set(old)|set(new)):
  first,last=old.get(u),new.get(u)
  if first is not None and last is not None and dump(first)==dump(last):continue
  cu.append(dict(kind=kind,uuid=u,disposition='added'if first is None else 'retired'if last is None else 'modified',before=dump(first)if first is not None else None,after=dump(last)if last is not None else None))
bz=objects(before,'zone');az=objects(after,'zone');assert set(bz)<=set(az);added=sorted(set(az)-set(bz));zd=[]
def non_outline(z):
 import copy
 z=copy.deepcopy(z)
 for row in list(children(z,'filled_polygon'))+list(children(z,'polygon')):z.remove(row)
 return dump(z)
for uid in sorted(bz):
 first,last=zone_definition(bz[uid]),zone_definition(az[uid])
 if first!=last:
  assert non_outline(bz[uid])==non_outline(az[uid]);zd.append(dict(uuid=uid,before_definition_sha256=hashlib.sha256(first.encode()).hexdigest(),after_definition_sha256=hashlib.sha256(last.encode()).hexdigest(),electrical_outline_correction_reason='Compose only the separately frozen exact Source-free literal native fragment cuts; all actual Source pads, prior source clusters, current110 reference/control/bypass scopes and native annuli must pass on the merged board. No area exemption or net/layer/pour-rule change.'))
scope=dict(electrical_source_unchanged=True,reviewed_footprint_references=sorted(poses),reviewed_copper_delta_UUIDs=[r['uuid']for r in cu],reviewed_added_zone_UUIDs=added,reviewed_existing_zone_outline_deltas=zd,reviewed_scope_reason='Complete actual four health receiver/cap cells: exact six manufacturer-preserving poses, Source-preserving Cu and narrowly clipped own-return/unused-pour geometry. Apply this ROOT101 bounded delta onto ROOT102, retaining C13006/C13007 poses and six added conductors; repeat all current110, independent Source/native/power/cut proofs before adoption. Source27/ratings/physical timing remain unqualified.')
write(a.out/'literal-delta.json',dict(input_sha256=inputs,before_board=str(B),before_board_sha256=sha(B),board=str(a.board),board_sha256=sha(a.board),exact_pose_references=poses,Cu_delta=cu,added_zone_UUIDs=added,existing_zone_outline_deltas=zd));write(a.out/'bounded-scope.json',scope)
health=json.loads(a.manifest.read_text());prior=json.loads(M102.read_text());actual=[g for g in health['owned_loops']if g['retained']];extras=[g for g in prior['owned_loops']if g['retained']and g['ref']in('C13006','C13007')];assert len(actual)==108 and len(extras)==2;assert not {g['ref']for g in actual}&{g['ref']for g in extras};composed=dict(health,owned_loops=actual+extras,board_sha256=None,current_native_proof_required=True,composition_input_sha256={str(a.manifest):sha(a.manifest),str(M102):sha(M102)},scope='Current110 on future ROOT102 bounded health composition.108 exact health groups plus unchanged C13006/C13007 loops, all old receiver/circuit paths preserved. Exact final merged-board hash must bind this manifest before native reproof.');write(a.out/'current110-unbound-composition-manifest.json',composed)
assert all(sha(Path(q))==h for q,h in inputs.items());print(json.dumps(dict(before=str(B),donor=str(a.board),poses=len(poses),Cu_dispositions={kind:sum(r['disposition']==kind for r in cu)for kind in('added','retired','modified')},added_zones=len(added),outline_deltas=len(zd))))
