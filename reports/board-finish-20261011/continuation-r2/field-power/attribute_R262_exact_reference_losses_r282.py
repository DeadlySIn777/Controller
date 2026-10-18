"""Read-only exact residual-reference attribution, no projection or waivers."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,sys
from pathlib import Path
from shapely.ops import unary_union
from shapely import from_wkb,set_precision,get_precision
import contact_layout as C
from inventory import sha
H=Path(__file__).resolve().parent;ROOT=H.parent;B=H/'R54-native-wider-IO3-monitor-joint-audit-r214';N=H/'REG-seven-cached-exact-analytic-guard-audit-r262';O=H/'R262-exact-residual-reference-attribution-r282'
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def digest(g):return hashlib.sha256(g.wkb).hexdigest()
def main():
 assert not O.exists();O.mkdir();assert sha(N/'receipt.json')=='683f426012983f3157ea59aee95edb394227c62d7c5d32acc46fb0078c38ae53';_,h0,_,z0,c0=pickle.loads((B/'model.pkl').read_bytes());_,h1,_,z1,c1=pickle.loads((N/'model.pkl').read_bytes());before=pickle.loads((B/'groups.pkl').read_bytes());after=pickle.loads((N/'groups.pkl').read_bytes());refs=json.loads((N/'reference-rows.json').read_text());guards=json.loads((N/'native-actual-fill-vs-new-required-guard-checks.json').read_text());oldz={q['uuid']:q for q in z0};newz={q['uuid']:q for q in z1};tracks={q['uuid']:q for q in h0['tracks']};roots={'/LOGIC_GND':'J11001','/motherboard_motors/FIELD_GND':'J11003','/motherboard_do/FIELD_B_0V':'J11005'};rows=[]
 for row in refs:
  net=row['ground'];ref=roots[net];root=lambda gs:next(xs for xs in gs if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));a=root(before[net]);b=root(after[net])
  for bad in row['retained_outer_reference_losses']:
   t=tracks[bad['uuid']];layer='In1.Cu' if t['layer']=='F.Cu' else 'In4.Cu';oldfill=[q for q in a if q['kind']=='fill' and q['layer']==layer];newfill=[q for q in b if q['kind']=='fill' and q['layer']==layer];oldref=unary_union([q['shape'] for q in oldfill]);newref=unary_union([q['shape'] for q in newfill]);body=C.body(t);lost=body.intersection(oldref).difference(newref);assert abs(lost.area-bad['prior_source_reference_lost_mm2'])<1e-12;f=O/(bad['uuid']+'-exact-required-lost-reference.wkb');f.write_bytes(lost.wkb);contrib=[]
   for uid in sorted({q['uuid'] for q in oldfill}|{q['uuid'] for q in newfill}):
    x=unary_union([q['shape'] for q in oldfill if q['uuid']==uid]);y=unary_union([q['shape'] for q in newfill if q['uuid']==uid]);rm=x.difference(y);part=lost.intersection(rm)
    if part.area<=1e-14:continue
    ginfo=[]
    for gu in guards:
     if gu['native_zone_UUID']!=uid or gu['layer']!=layer:continue
     positive=[]
     for disk in gu.get('explicit_additive_analytic_guard_disks',[]):
      sh=from_wkb(bytes.fromhex(disk['disk_WKB_hex']));hit=part.intersection(sh).area
      if hit>1e-14:positive.append({'iteration':disk['iteration'],'actual_lost_mask_overlap_mm2':hit,'circle_sha256':disk['outward256edge_disk_sha256'],'owned_body_point_mm':disk['exact_owned_body_point_mm'],'guard_radius_mm':disk['guard_disk_radius_mm'],'unchanged_required_gap_mm':disk['unchanged_required_gap_mm']})
     if positive:ginfo.append({'foreign_key':gu['foreign_key'],'supplementary_actual_guard_disks_intersecting_loss':positive})
    owned=uid in oldz or uid in newz;q0=oldz.get(uid);q1=newz.get(uid);contrib.append({'fill_UUID':uid,'belongs_owned_NEW_plane':owned,'old_effective_rooted_fill_SHA256':digest(x),'new_effective_rooted_fill_SHA256':digest(y),'oldfill_removed_mm2':rm.area,'required_old_reference_loss_overlap_mm2':part.area,'overlap_bounds_mm':list(part.bounds),'old_owned_physical_WKB_sha256':digest(q0['shape']) if q0 else None,'new_owned_physical_WKB_sha256':digest(q1['shape']) if q1 else None,'owned_physical_role_WKB_unchanged':q0 is not None and q1 is not None and q0['shape'].wkb==q1['shape'].wkb,'actual_additive_guard_disk_attribution':ginfo})
   zclear=[]
   for q in z1:
    if q['layer']!=layer or C.norm(q['net'])==net:continue
    if q['shape'].distance(lost)<.65:zclear.append({'UUID':q['uuid'],'net_raw':q['net'],'distance_to_exact_lost_old_reference_mm':q['shape'].distance(lost),'unchanged_from_R214':q['uuid'] in oldz and q['shape'].wkb==oldz[q['uuid']]['shape'].wkb,'shape_sha256':digest(q['shape']),'clearance_mm':q.get('clearance_mm',.15)})
   result={**bad,'ground':net,'reference_layer':layer,'exact_lost_reference_bounds_mm':list(lost.bounds),'lost_reference_WKB_file':str(f.resolve()),'lost_reference_WKB_sha256':sha(f),'retained_native_track':t,'atomic_effective_source_fill_removal_attribution':contrib,'nearby_owned_foreign_planes':zclear,'old_source_reference_GE0S_grid_mm':get_precision(oldref),'new_source_reference_GE0S_grid_mm':get_precision(newref),'no_ref_loss_waiver':True};rows.append(result);write(O/'checkpoint.json',rows);print(json.dumps({'ground':net,'old_track_UUID':t['uuid'],'area_mm2':lost.area,'bounds_mm':list(lost.bounds),'causal_fill_UUIDs':[v['fill_UUID'] for v in contrib],'nearby_owned_UUIDs':[v['UUID'] for v in zclear]}),flush=True)
 rec={'verdict':'EXACT_R262_OLD_REFERENCE_FAILURE_ATTRIBUTED_NO_REPAIR_OR_ACCEPTANCE','R214_model_sha256':sha(B/'model.pkl'),'rejected_R262_receipt_sha256':sha(N/'receipt.json'),'rejected_R262_model_sha256':sha(N/'model.pkl'),'rows':rows,'source_byte_files_unmodified':True,'projection_not_repeated':True,'board_written':False,'native_jobs':0,'adopted':False};write(O/'receipt.json',rec);print(sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
