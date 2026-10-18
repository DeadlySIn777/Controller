"""Exact primitive/union attribution; no projected-model adoption or guard waiver."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import regional_guarded_declared_projection_r140 as P
import guarded_declared_settings_projection_r58 as PG
import complete_geometry_r2 as G
import contact_layout as C
import fast_contacts as F
import physical_reference_losses_r1 as REF
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from inventory import sha
O=H/'REG-reference-cutter-union-precision-attribution-r229'

def primitive_rows(g,h,z,net,layer,local):
 changed=PG.changed_ids(g,h);rows={}
 for t in h['tracks']:
  if t['uuid'] in changed and t['layer']==layer and C.norm(t['net'])!=net:
   clear=max(G.gap(h,net,t['net']),local);rows[('track',t['uuid'])]=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear+.025)
 for v in h['vias']:
  if v['uuid'] in changed and C.norm(v['net'])!=net:
   clear=max(G.gap(h,net,v['net']),local);radius=v['drill']/2+.275
   if layer in v['flashed']:radius=max(radius,v['d']/2+clear+.025)
   rows[('via',v['uuid'])]=P.bounded_disk(v,radius)
 for pad in h['pads']:
  if pad['uuid'] in changed and C.norm(pad['net'])!=net:
   clear=max(G.gap(h,net,pad['net']),local)
   for i,sh in enumerate(C.poly(pad['layers'].get(layer,[]))):rows[('pad',pad['uuid'],i)]=P.bounded_buffer(sh,clear+.025)
 for q in z:
  if q['layer']==layer and C.norm(q['net'])!=net:
   clear=max(G.gap(h,net,q['net']),local,float(q.get('clearance_mm',.15)));rows[('zone',q['uuid'])]=P.bounded_buffer(q['shape'],clear+.025)
 return rows

def main():
 assert not O.exists();O.mkdir();before=H/'R54-native-wider-IO3-monitor-joint-audit-r214';after=H/'REG-safe-subset-on-current-R214-full-audit-r227';g,bh,bb,bz,bc=pickle.loads((before/'model.pkl').read_bytes());ag,ah,ab,az,ac=pickle.loads((after/'model.pkl').read_bytes());restore_bound_generated_precision_states(bb,bz);restore_bound_generated_precision_states(ab,az)
 bg=pickle.loads((before/'groups.pkl').read_bytes());aa=pickle.loads((after/'groups.pkl').read_bytes());root=lambda groups:next(xs for xs in groups['/LOGIC_GND'] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));br=root(bg);ar=root(aa);oldref=unary_union([q['shape'] for q in br if q['kind']=='fill' and q['layer']=='In1.Cu']);newref=unary_union([q['shape'] for q in ar if q['kind']=='fill' and q['layer']=='In1.Cu']);tmap={t['uuid']:t for t in bh['tracks']};refrow=next(r for r in json.loads((after/'reference-rows.json').read_text(encoding='utf-8')) if r['ground']=='/LOGIC_GND');pieces=[]
 for r in refrow['retained_outer_reference_losses']:
  t=tmap[r['uuid']];body=REF.A.shape({'kind':'segment',**t});pieces.append(body.intersection(oldref).difference(newref))
 lost=unary_union(pieces);(O/'exact-failed-reference-mask.wkb').write_bytes(lost.wkb);print('R229 exact lost mask',lost.area,flush=True)
 locals_=sorted({float(q['clearance_mm']) for q in bh['zones'] if C.norm(q['net'])=='/LOGIC_GND' and 'In1.Cu' in q['fills']});cache={};ledger=[]
 for local in locals_:
  old=primitive_rows(g,bh,bz,'/LOGIC_GND','In1.Cu',local);new=primitive_rows(ag,ah,az,'/LOGIC_GND','In1.Cu',local);modified=[];primitive_extra=[]
  for key,shape in new.items():
   prior=old.get(key)
   if prior is not None and P.digest(prior)==P.digest(shape):continue
   extra=shape.difference(prior) if prior is not None else shape;inter=lost.intersection(extra)
   modified.append({'key':list(key),'before_sha256':P.digest(prior) if prior is not None else None,'after_sha256':P.digest(shape),'extra_primitive_area_mm2':extra.area,'exact_lost_intersection_mm2':inter.area,'grid_mm':get_precision(shape)})
   if inter.area>1e-14:primitive_extra.append(inter)
  cache[local]=(old,new);ledger.append({'local_clearance_mm':local,'changed_or_added_primitives':modified,'all_lost_in_extra_individual_primitives_mm2':unary_union(primitive_extra).area})
  print('R229 primitives',local,len(old),len(new),len(modified),unary_union(primitive_extra).area,flush=True)
 native=[]
 for q in bh['zones']:
  if C.norm(q['net'])!='/LOGIC_GND' or 'In1.Cu' not in q['fills']:continue
  original=unary_union(C.poly(q['fills']['In1.Cu']))
  if original.intersection(lost).area<1e-14:continue
  old,new=cache[float(q['clearance_mm'])];old={k:s for k,s in old.items() if s.intersects(original)};new={k:s for k,s in new.items() if s.intersects(original)}
  oc=unary_union(list(old.values()));nc=unary_union(list(new.values()));oe=original.difference(oc);ne=original.difference(nc)
  zero_old=[];zero_new=[]
  for rows,dst in [(old,zero_old),(new,zero_new)]:
   for sh in rows.values():
    restored=set_precision(sh,0);assert restored.wkb==sh.wkb;dst.append(restored)
  oz=unary_union(zero_old);nz=unary_union(zero_new);oldremain=original.difference(oz);newremain=original.difference(nz)
  extra=nc.difference(oc);direct=lost.intersection(extra);zeroextra=nz.difference(oz);row={'original_zone_UUID':q['uuid'],'original_local_clearance_mm':q['clearance_mm'],'old_primitive_count':len(old),'new_primitive_count':len(new),'all_retained_primitive_hashes_unchanged':all(P.digest(s)==P.digest(new[k]) for k,s in old.items() if k in new),'current_union_before_sha256':P.digest(oc),'current_union_after_sha256':P.digest(nc),'current_exact_lost_intersection_in_union_added_mm2':direct.area,'current_direct_original_reference_difference_mm2':lost.intersection(oe).difference(ne).area,'zero_grid_exact_lost_intersection_in_union_added_mm2':lost.intersection(zeroextra).area,'zero_grid_direct_original_reference_difference_mm2':lost.intersection(oldremain).difference(newremain).area,'zero_grid_baseline_remaining_added_vs_current_mm2':oldremain.difference(oe).area,'zero_grid_baseline_remaining_removed_vs_current_mm2':oe.difference(oldremain).area,'primitive_geometry_WKB_and_required_guards_unchanged':True,'construction_grid_state_hypothesis_only':True};native.append(row);print('R229 native',json.dumps(row),flush=True)
 (O/'primitive-change-ledger.json').write_text(json.dumps(ledger,indent=1)+'\n',encoding='utf-8');(O/'original-zone-union-comparison.json').write_text(json.dumps(native,indent=1)+'\n',encoding='utf-8');(O/'receipt.json').write_text(json.dumps({'verdict':'EXACT_CUTTER_GRID_DIAGNOSTIC_NO_ADOPTION_OR_WAIVER','baseline_sha256':sha(before/'model.pkl'),'candidate_sha256':sha(after/'model.pkl'),'primitive_ledger_sha256':sha(O/'primitive-change-ledger.json'),'native_zone_comparison_sha256':sha(O/'original-zone-union-comparison.json'),'guard_primitives_geometry_and_required_distances_unchanged':True,'alternative_precision_policy_not_applied_to_candidate':True,'board_written':False,'native_jobs':0},indent=1)+'\n',encoding='utf-8');print('R229 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
