"""Freeze an exact subsequent return-only native transaction from interim2af."""
import argparse,collections,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_merge_bounded_pcb_delta import objects,parse,without_generated_fills,dump,reference,zone_definition
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
ap=argparse.ArgumentParser();ap.add_argument('--donor',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
base=Path('reports/motherboard-return-zoning-20261001/interim-full-plane-delta-r02/motherboard-interim-own-reference-candidate.kicad_pcb');donor=a.donor;out=a.out
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir(parents=True);(out/'inputs').mkdir();inputs=[base,donor,donor.parent/'receipt.json',Path(__file__)];frozen={str(p.resolve()):sha(p)for p in inputs}
for p in inputs:shutil.copy2(p,out/'inputs'/('before.kicad_pcb'if p==base else p.name))
dest=out/'motherboard-second-own-reference-candidate.kicad_pcb';shutil.copy2(donor,dest)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(donor.with_suffix(suffix),dest.with_suffix(suffix))
for p in donor.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
 elif p.name=='fp-lib-table':shutil.copy2(p,out/p.name)
trees=[parse(without_generated_fills(p.read_text()))for p in(base,donor)]
fps=[{reference(f):dump(f)for f in tree if isinstance(f,list)and f[0]=='footprint'}for tree in trees]
if fps[0]!=fps[1]:raise ValueError('Unreviewed SOURCE footprint change')
oldzones,newzones=[objects(tree,'zone')for tree in trees]
if set(oldzones)!=set(newzones)or any(zone_definition(oldzones[u])!=zone_definition(newzones[u])for u in oldzones):raise ValueError('Second-only plane bridge transaction changed zone definitions')
changed=[];added=[];retired=[];derived=[]
for kind in('segment','via','arc'):
 old,new=[objects(tree,kind)for tree in trees]
 changed.extend(u for u in set(old)&set(new)if dump(old[u])!=dump(new[u]));added.extend(set(new)-set(old));retired.extend(set(old)-set(new))
 for u in set(old)&set(new):
  if dump(old[u])==dump(new[u]):continue
  if kind!='via':raise ValueError('Existing non-via copper unexpectedly changed')
  norm=lambda v:dump([r for r in v if not(isinstance(r,list)and r[0]=='zone_layer_connections')])
  if norm(old[u])!=norm(new[u]):raise ValueError('Old via changed beyond derived annulus metadata')
  derived.append(dict(uuid=u,before=dump(old[u]),after=dump(new[u]),reason='Native regenerated annulus-layer cache only; actual old geometry/net/drill/UUID unchanged.'))
allowed_retire={'22bb7970-7f8a-48b1-a00d-ced6aec2c839','6d6b64a9-595a-4566-a9f8-a9cba473219f','d55efe31-b2c5-4c4e-9a3e-8afa1e4a95f2','e8edfcc1-8545-4351-9ce0-ba50977e6e83'}
if set(retired)!=allowed_retire:raise ValueError('Unexpected retirement outside exact redundant new transfer scope')
boards=[pcbnew.LoadBoard(str(p))for p in(base,donor)];pads=[{p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}for b in boards]
if pads[0]!=pads[1]:raise ValueError('Native source pads/pins/poses changed')
nets={p.GetNetname()for p in boards[0].GetPads()if p.GetNumber()};clusters=[native_pad_clusters(b,nets)for b in boards];passed=clusters_survive(*clusters)
write(out/'all-source-pad-cluster-proof.json',dict(before=clusters[0],after=clusters[1],passed=passed))
if not passed:raise ValueError('A previous source-pad cluster split')
scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Exact follow-on transaction from interim2af: low-current own-domain inner return bridge tracks, any explicitly SOURCE-connected two-layer plated ground transfers, four exact new redundant-transfer retirements and derived native annulus metadata. No original source Cu/lands/poses/zone definitions changed. Later ROOT current-entry copper requires independent final rebase/native verification; current source26 properties/fuses remain owned by ROOT.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(changed+added+retired),reviewed_added_zone_UUIDs=[])
write(out/'bounded-scope.json',scope);write(out/'native-annulus-metadata-only.json',derived)
donor_receipt=json.loads((donor.parent/'receipt.json').read_text());receipt=dict(before_board=str(base.resolve()),before_board_sha256=sha(base),board_sha256=sha(dest),new_copper=len(added),retired_exact_new_transfer_UUIDs=sorted(retired),derived_annulus_only_changes=len(derived),old_SOURCE_pads_pin_nets_poses_zone_definitions_and_clusters_preserved=True,native_errors=donor_receipt['native_errors'],native_DRC_types=donor_receipt['native_DRC_types'],ignored_checks=donor_receipt['ignored_checks'],remaining_unanchored_resources=donor_receipt['remaining_unanchored_resources'],scope_sha256=sha(out/'bounded-scope.json'),actual_current_source26_rebase_qualified=False,passed=False,manufacturing_ready=False,input_sha256=frozen)
if any(sha(Path(p))!=v for p,v in frozen.items()):raise ValueError('Frozen second-transaction input changed')
write(out/'receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k!='input_sha256'},indent=2))
