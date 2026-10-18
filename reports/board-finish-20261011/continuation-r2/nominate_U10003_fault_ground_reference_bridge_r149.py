"""Couple the exact fault restore, literal FG source barrel and ground bands.

Only a sparse nominated delta is written. The In4 seed comes through the
explicit new barrel to its tested prior In1 annulus, never a source alias.
Old filled-copper projection, all continuity/reference/current/native gates
remain required before integration or adoption.
"""
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
OUT=H/'U10003-fault-ground-source-barrel-reference-bridge-nominee-r149'
NET='/motherboard_motors/FIELD_GND';SITE=(216.04,142.95)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polys(s):return[p for p in([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if p.geom_type=='Polygon'and not p.is_empty]
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h,b,z,full=pickle.loads(mp.read_bytes());r=json.loads((H/'U10003-unqualified-physical-fault-detour-r130/receipt.json').read_bytes());siteproof=json.loads((H/'U10003-fault-coupled-ordinary-ground-barrel-nominees-r148/receipt.json').read_bytes());site=next(x for x in siteproof['sites_true_discrete_owned_hole_SMD_courtyard_native_and217_reservation_pass']if x['site_mm']==list(SITE));assert site['actual_prior_FG_source_annuli_mm2']['In1.Cu']>.16
 pad=next(p for p in h['pads']if(p['ref'],p['num'])==('U10003','9'));raw=pad['net'];assert C.norm(raw)==NET;via={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U10003-field-ground-r149/barrel')),'net':raw,'x':SITE[0],'y':SITE[1],'d':.5,'drill':.2,'flashed':list(h['copper_layers']),'prospective_not_native':True};ground={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U10003-field-ground-r149/Bstub')),'net':raw,'layer':'B.Cu','a':[pad['x'],pad['y']],'b':list(SITE),'w':.2,'prospective_not_native':True};tracks=r['repair']['tracks']+[ground];ids=set(r['removed_exact_old_track_UUIDs']);hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in ids]+r['repair']['tracks']};records,trees=F.build({**hard,'zones':[]});body=unary_union([C.body(t)for t in tracks]);ports=r['repair']['existing_native_barrels'];caps=unary_union([Point(v['x'],v['y']).buffer(.575,quad_segs=256)for v in ports]);fault=unary_union([C.body(t)for t in r['repair']['tracks']]);outside=fault.difference(caps);pt=Point(SITE);ann=pt.buffer(.25,quad_segs=256).difference(pt.buffer(.1,quad_segs=256));groups=pickle.loads(mp.with_name('groups.pkl').read_bytes());root=next(xs for xs in groups[NET]if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs));win=body.envelope.buffer(2.);new=[];rows=[]
 for layer in('In1.Cu','In4.Cu'):
  src=unary_union([q['shape']for q in root if q['layer']==layer and q['kind']=='fill']);obs=[]
  for j in trees[layer].query(win.buffer(1.),predicate='intersects'):
   q=records[layer][int(j)]
   if C.norm(q['net'])==NET:continue
   gap=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET]else.6)+.025;obs.append(N.bounded_buffer(q['shape'].intersection(win.buffer(1.)),gap))
  for q in z:
   if q['layer']!=layer or C.norm(q['net'])==NET or not q['shape'].intersects(win):continue
   gap=max(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET]else.6,float(q.get('clearance_mm',.15)))+.025;obs.append(N.bounded_buffer(q['shape'].intersection(win.buffer(1.)),gap))
  for p in h['pads']:
   for sh in C.poly(p.get('hole')or[]):
    if sh.intersects(win):obs.append(N.bounded_buffer(sh,.275))
  for v in h['vias']:
   if C.norm(v['net'])!=NET and win.covers(Point(v['x'],v['y'])):obs.append(N.bounded_disk(v,v['drill']/2+.275))
  for a in h['rule_areas']:
   if a['no_zones']and layer in a['layers']:obs.extend(N.bounded_buffer(s,.025)for s in C.poly(a['outline'])if s.intersects(win))
  allowed=win.difference(unary_union(obs));desired=body.buffer(.15,quad_segs=128).union(pt.buffer(.30,quad_segs=128));intended=set_precision(desired.intersection(allowed),1e-6);physical=set_precision(intended.difference(pt.buffer(.1,quad_segs=128)),1e-6);seed=src if layer=='In1.Cu'else ann;keep=[p for p in polys(physical)if p.intersection(seed).area>0 and not p.buffer(-.075).is_empty];physical=unary_union(keep);intended_parts=[p for p in polys(intended)if any(p.intersection(s).area>0 for s in keep)];intended=unary_union(intended_parts)
  # Union arms can still be disconnected. Each full fault/ground reference and
  # every actual source-rooted candidate component are reported literally.
  fgstub=C.body(ground);missing=outside.difference(src.union(physical));gndgap=fgstub.difference(src.union(physical));foreign=[]
  for q in full['zones']:
   if C.norm(q['net'])==NET:continue
   sh=unary_union(C.poly(q['fills'].get(layer,[])));over=physical.intersection(sh)
   if not over.is_empty:foreign.append({'UUID':q['uuid'],'net':q['net'],'area_mm2':over.area,'old_fill_contact_source_and_reference_preservation':'OPEN'})
  uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U10003-field-ground-r149/'+layer));q={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':intended,'clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','priority':126,'island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3};new.append(q);(OUT/(layer+'-physical.wkb')).write_bytes(physical.wkb);(OUT/(layer+'-intended.wkb')).write_bytes(intended.wkb)
  rows.append({'layer':layer,'UUID':uid,'components':len(polys(physical)),'area_mm2':physical.area,'exact_prior_FG_source_overlap_mm2':physical.intersection(src).area,'new_barrel_annular_overlap_mm2':physical.intersection(ann).area,'fault_outside_bound_old_caps_gap_mm2':missing.area,'fault_outside_caps_gap_empty':missing.is_empty,'ground_stub_raw_reference_gap_mm2':gndgap.area,'ground_stub_raw_reference_gap_empty':gndgap.is_empty,'foreign_effective_fill_overlap_obligations':foreign,'source_seed_kind':'ACTUAL_PRIOR_J11003_In1'if layer=='In1.Cu'else'PROSPECTIVE_SAME_ORDINARY_BARREL_TO_ITS_ACTUAL_PRIOR_In1_ANNULUS','raw_old_signal_port_support_qualification':'OPEN; no automatic cap credit'})
 # Check the physical ground stub against every actual retained B conductor.
 stub=C.body(ground);errors=[]
 for j in trees['B.Cu'].query(stub.buffer(.627),predicate='intersects'):
  q=records['B.Cu'][int(j)]
  if C.norm(q['net'])==NET:continue
  req=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET]else.6)+.025;actual=stub.distance(q['shape'])
  if actual<req:errors.append({'kind':q['kind'],'UUID':q['uuid'],'net':q['net'],'actual':actual,'required':req})
 (OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'tracks':tracks,'vias':[via]},protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(new,protocol=5));receipt={'verdict':'SPARSE_COUPLED_FAULT_GROUND_REFERENCE_NOMINEE_ALL_NATIVE_FILL_CONTACT_REFERENCE_CURRENT_GATES_OPEN','parent_model_sha256':sha(mp),'exact_original_fault_delete_UUIDs':sorted(ids),'new_ground_pad_UUID':pad['uuid'],'source_barrel':via,'B_ground_stub':ground,'B_ground_stub_true_Cu_errors':errors,'rows':rows,'old_signal_port_aperture_support_never_automatically_qualified':True,'native_effective_fills_not_projected':True,'new_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'new_zones_sha256':sha(OUT/'proposed-zones.pkl'),'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps({'receipt_sha256':sha(OUT/'receipt.json'),'B_stub_errors':errors,'rows':rows}),flush=True)
if __name__=='__main__':main()
