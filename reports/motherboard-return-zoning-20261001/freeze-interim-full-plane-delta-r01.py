"""Freeze the literal actual r46-to-reviewed-plane WIP transaction."""
import collections,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_merge_bounded_pcb_delta import objects,parse,without_generated_fills,dump,zone_definition,sha_text,reference
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_zone_motherboard_returns import LEGACY_ZONES

base=Path('reports/motherboard-pcb-integration-20261001/adc-cell-iso1212-entry-substrate-source25-r46/motherboard-bounded-merged-candidate.kicad_pcb')
donor=Path('reports/motherboard-return-zoning-20261001/source25-r46-short-source-escapes-r01/motherboard-short-source-return-candidate.kicad_pcb')
out=Path('reports/motherboard-return-zoning-20261001/interim-full-plane-delta-r02')
if out.exists():raise ValueError('Fresh report required')
out.mkdir();(out/'inputs').mkdir();shutil.copy2(base,out/'inputs'/'before-r46.kicad_pcb')
dest=out/'motherboard-interim-own-reference-candidate.kicad_pcb';shutil.copy2(donor,dest)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(donor.with_suffix(suffix),dest.with_suffix(suffix))
for p in donor.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
 elif p.name=='fp-lib-table':shutil.copy2(p,out/p.name)
first=parse(without_generated_fills(base.read_text()));last=parse(without_generated_fills(donor.read_text()))
oldfps={reference(f):dump(f)for f in first if isinstance(f,list)and f[0]=='footprint'};newfps={reference(f):dump(f)for f in last if isinstance(f,list)and f[0]=='footprint'}
if oldfps!=newfps:raise ValueError('A footprint changed outside the plane/Cu scope')
changed=[];added=[];retired=[];native_annulus_metadata=[]
for kind in('segment','via','arc'):
 old=objects(first,kind);new=objects(last,kind)
 for uid in set(old)&set(new):
  if dump(old[uid])==dump(new[uid]):continue
  changed.append(uid)
  if kind=='via':
   def no_annulus_cache(item):return dump([v for v in item if not(isinstance(v,list)and v[0]=='zone_layer_connections')])
   if no_annulus_cache(old[uid])==no_annulus_cache(new[uid]):native_annulus_metadata.append(dict(uuid=uid,before=dump(old[uid]),after=dump(new[uid]),review='Only native regenerated zone_layer_connections changed after actual owned-plane refill; position/drill/diameter/layers/net/UUID unchanged. Actual flashed annuli independently validated in source-anchor receipts.'))
 added.extend(set(new)-set(old));retired.extend(set(old)-set(new))
if retired:raise ValueError('Combined interim donor unexpectedly retires old copper')
oz=objects(first,'zone');nz=objects(last,'zone');zones_added=sorted(set(nz)-set(oz));zone_reviews=[]
for uid in oz:
 if uid not in nz:raise ValueError('Existing zone retired')
 if zone_definition(oz[uid])!=zone_definition(nz[uid]):
  if uid not in LEGACY_ZONES:raise ValueError('Non-authorized existing zone changed '+uid)
  zone_reviews.append(dict(uuid=uid,before_definition_sha256=sha_text(zone_definition(oz[uid])),after_definition_sha256=sha_text(zone_definition(nz[uid])),electrical_outline_correction_reason='Net-aware subtraction of foreign physical domain/package/raw/floating-SUB footprints, preserving net/layers/rules/UUID and all actual source-pad clusters; exact original five-zone authority plus proven empty generated-pocket cuts.'))
print(dict(changed_old_Cu=len(changed),native_regenerated_annulus_metadata=len(native_annulus_metadata),added_Cu=len(added),five_old_zones=len(zone_reviews)),flush=True)
if len(changed)-len(native_annulus_metadata)!=13 or len(zone_reviews)!=5:raise ValueError('Actual functional-barrier/five-plane transaction differs')
write(out/'exact-native-annulus-metadata-delta.json',native_annulus_metadata)
scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Exact r46 WIP delta: thirteen electrically necessary retained isolation-crossing corrections; actual per-side return polygons; exact five inherited net-aware plane outlines;306 SOURCE-owned CMOS stitches,4 quiet ADC branches,16 own-return transfers and21 short SOURCE-ground escapes. Every historical old copper/pad/pose/source cluster remains except the13 reviewed electrical geometry fixes. This remains an incomplete PCB with explicit isolated-return/global-feed warnings.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(changed+added),reviewed_added_zone_UUIDs=zones_added,reviewed_existing_zone_outline_deltas=zone_reviews)
write(out/'bounded-scope.json',scope)
boards=[pcbnew.LoadBoard(str(p))for p in(base,donor)];nets={p.GetNetname()for p in boards[0].GetPads()if p.GetNumber()};clusters=[native_pad_clusters(b,nets)for b in boards];passed=clusters_survive(*clusters)
write(out/'all-source-pad-cluster-proof.json',dict(before=clusters[0],after=clusters[1],passed=passed))
if not passed:raise ValueError('Combined interim donor loses an actual old source cluster')
pads=[{p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}for b in boards]
if pads[0]!=pads[1]:raise ValueError('Original copper lands/pin nets/poses changed')
for p in ['native-0.json','physical-reference-anchors.json','all-source-pad-cluster-proof.json','receipt.json']:
 shutil.copy2(donor.parent/p,out/'inputs'/('donor-'+p))
drc=json.loads((donor.parent/'native-0.json').read_text());receipt=dict(before_board_sha256=sha(base),board_sha256=sha(dest),before_board=str(base.resolve()),candidate=str(dest.resolve()),native_errors=sum(x['severity']=='error'for x in drc['violations']),native_DRC_types=dict(collections.Counter(x['type']for x in drc['violations'])),ignored_checks=drc['ignored_checks'],exact_existing_copper_geometry_changes=len(changed)-len(native_annulus_metadata),exact_native_annulus_metadata_changes=len(native_annulus_metadata),new_copper=len(added),new_zones=len(zones_added),exact_five_existing_zone_outline_reviews=zone_reviews,all_source_clusters_and_manufacturer_lands_and_source_pin_nets_and_poses_preserved=True,uncapped_missing_joins=boards[1].GetConnectivity().GetUnconnectedCount(False),scope_sha256=sha(out/'bounded-scope.json'),WIP_merge_approved_scope_only=True,all_reference_resources_qualified=False,manufacturing_ready=False)
write(out/'receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k!='exact_five_existing_zone_outline_reviews'},indent=2))
