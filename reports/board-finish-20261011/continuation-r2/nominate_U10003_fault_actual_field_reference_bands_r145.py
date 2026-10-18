"""Nominate true FG bands for the frozen physical fault detour; no waiver.

Foreign original filled planes may need explicit remove-only masks later.
All actual discrete copper, owned planes and native isolation remain hard.
No candidate is adopted by this geometric nomination.
"""
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
OUT=H/'U10003-fault-actual-field-reference-band-nominees-r145'
NET='/motherboard_motors/FIELD_GND'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polys(s):return [p for p in([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if p.geom_type=='Polygon'and not p.is_empty]
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h,b,z,full=pickle.loads(mp.read_bytes());rp=H/'U10003-unqualified-physical-fault-detour-r130/receipt.json';r=json.loads(rp.read_bytes());assert r['parent_model_sha256']==sha(mp);repair=r['repair'];ts=repair['tracks'];assert len(ts)==2;body=unary_union([C.body(t)for t in ts]);signal=C.norm(ts[0]['net']);ports=repair['existing_native_barrels'];caps=unary_union([Point(v['x'],v['y']).buffer(.575,quad_segs=256)for v in ports]);outside=body.difference(caps);win=body.envelope.buffer(2.);groups=pickle.loads(mp.with_name('groups.pkl').read_bytes());root=next(xs for xs in groups[NET]if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs));records,trees=F.build({**h,'zones':[]});rows=[];new=[]
 for layer in('In1.Cu','In4.Cu'):
  src=unary_union([q['shape']for q in root if q['layer']==layer and q['kind']=='fill']);obs=[];hardrows=[]
  for j in trees[layer].query(win.buffer(1.),predicate='intersects'):
   q=records[layer][int(j)]
   if C.norm(q['net'])==NET:continue
   gap=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET]else.6)+.025
   cut=N.bounded_buffer(q['shape'].intersection(win.buffer(1.)),gap);obs.append(cut);hardrows.append({'kind':q['kind'],'UUID':q['uuid'],'raw_net':q['net'],'required':gap,'body_reference_gap_intersection_mm2':outside.intersection(cut).area})
  for q in z:
   if q['layer']!=layer or C.norm(q['net'])==NET or not q['shape'].intersects(win):continue
   gap=max(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET]else.6,float(q.get('clearance_mm',.15)))+.025
   cut=N.bounded_buffer(q['shape'].intersection(win.buffer(1.)),gap);obs.append(cut);hardrows.append({'kind':'OWNED_ROLE','UUID':q['uuid'],'raw_net':q['net'],'required':gap,'body_reference_gap_intersection_mm2':outside.intersection(cut).area})
  for p in h['pads']:
   for sh in C.poly(p.get('hole')or[]):
    if sh.intersects(win):obs.append(N.bounded_buffer(sh,.275))
  for v in h['vias']:
   if C.norm(v['net'])!=NET and win.covers(Point(v['x'],v['y'])):obs.append(N.bounded_disk(v,v['drill']/2+.275))
  for a in h['rule_areas']:
   if a['no_zones']and layer in a['layers']:obs.extend(N.bounded_buffer(s,.025)for s in C.poly(a['outline'])if s.intersects(win))
  allowed=win.difference(unary_union(obs));routeband=set_precision(body.buffer(.15,quad_segs=128).intersection(allowed),1e-6)
  # Keep only actual-root-contacting components; isolated pieces never gain source credit.
  rooted=[p for p in polys(routeband)if p.intersection(src).area>0 and not p.buffer(-.075).is_empty];physical=unary_union(rooted);needed=outside.difference(src);missing=needed.difference(physical)
  holes=[]
  for q in full['zones']:
   if C.norm(q['net'])==NET:continue
   sh=unary_union(C.poly(q['fills'].get(layer,[])));over=physical.intersection(sh)
   if not over.is_empty:holes.append({'native_or_owned_UUID':q['uuid'],'raw_net':q['net'],'overlap_mm2':over.area,'exact_before_filled_WKB_sha256':hashlib.sha256(sh.wkb).hexdigest(),'actual_remove_only_contact_source_strict_old_reference_gate':'OPEN'})
  uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U10003-field-fault-reference-r145/'+layer));q={'uuid':uid,'net':ts[0]['net'].replace('DOA_FLT_N_FIELD','FIELD_GND'),'layer':layer,'shape':physical,'zone_outline_shape':physical,'clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','priority':126,'island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3}
  # Serialized token must come from the literal native FG source, never guessed.
  q['net']=next(p['net']for p in h['pads']if(p['ref'],p['num'])==('J11003','2'));new.append(q);path=OUT/(layer+'-physical.wkb');path.write_bytes(physical.wkb)
  row={'layer':layer,'new_UUID':uid,'new_area_mm2':physical.area,'actual_prior_root_overlap_mm2':physical.intersection(src).area,'outside_exact_old_.575_caps_original_gap_mm2':needed.area,'remaining_unfilled_reference_gap_mm2':missing.area,'remaining_gap_empty':missing.is_empty,'physical_sha256':sha(path),'real_hard_blockers':[x for x in hardrows if x['body_reference_gap_intersection_mm2']>0],'overlapping_foreign_actual_fill_withdrawal_obligations':holes,'old_port_aperture_support_not_qualified':True};rows.append(row);print(json.dumps(row),flush=True)
 (OUT/'new-reference-zone-nominees.pkl').write_bytes(pickle.dumps(new,protocol=5));receipt={'verdict':'NEW_FG_REFERENCE_BAND_NOMINATION_ALL_CONTACT_CURRENT_OLD_REFERENCE_NATIVE_GATES_OPEN'if all(x['remaining_gap_empty']for x in rows)else'FG_REFERENCE_BANDS_PHYSICALLY_INCOMPLETE_NO_ACCEPTED_REPAIR','model_sha256':sha(mp),'physical_fault_detour_receipt_sha256':sha(rp),'rows':rows,'new_zone_nominees_sha256':sha(OUT/'new-reference-zone-nominees.pkl'),'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R145',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
