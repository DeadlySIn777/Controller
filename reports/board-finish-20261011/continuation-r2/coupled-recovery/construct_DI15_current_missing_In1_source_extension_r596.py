"""Focused additive DI15 reference construction from frozen R594 paths.

No existing copper or power proposal is removed. Original same-domain
native fill retreat is only nominated with an exact overlap ledger.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,math,uuid
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import restore_field_current_mixed_precision_states_r366 as MS
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI15-current-missing-In1-actual-source-extension-r596';LG='/LOGIC_GND'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def pieces(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for x in getattr(s,'geoms',[])for p in pieces(x)]
def inf(s):return{'type':s.geom_type,'empty':s.is_empty,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,v=None):
  p=Path(p);s=sha(p);assert v is None or s==v;pins[str(p.resolve())]=s;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes());MS.restore_bound_field_current_precision_states(b,q)
 cache=pickle.loads(pin(H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592/bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl').read_bytes());paths=json.loads(pin(H/'DI15-saved-current-In2-transport-exact-wall-diagnosis-r594/independent-physical-reference-transport-diagnosis.json').read_bytes());options=json.loads(pin(H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592/source-and-target-continuous-ordinary-pair-options.json').read_bytes())
 original=K.C.inventory(pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a').read_bytes())[3]
 win=box(116,85,134,115);rec,trees=K.F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda net:.15 if dom[K.L.norm(net)]==dom[LG]else .6
 obs=[];ledger=[]
 for i in trees['In1.Cu'].query(win.buffer(1),predicate='intersects'):
  r=rec['In1.Cu'][int(i)]
  if K.L.norm(r['net'])==LG:continue
  req=max(.25,gap(r['net']))+.030;mask=K.Z.bounded_buffer(r['shape'],req);obs.append(mask);ledger.append({'kind':r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'guarded_mm':req,'mask':mask})
 retreat=[]
 for z in c['zones']:
  if K.L.norm(z['net'])==LG:continue
  req=max(.25,float(z['clearance_mm']),gap(z['net']))+.030
  for s in K.L.poly(z['fills'].get('In1.Cu',[])):
   if s.envelope.disjoint(win.buffer(1)):continue
   mask=K.Z.bounded_buffer(s,req)
   if z['uuid']in original and gap(z['net'])==.15:retreat.append((z,s));continue
   obs.append(mask);ledger.append({'kind':'current_foreign_fill_HARD','UUID':z['uuid'],'raw_net':z['net'],'guarded_mm':req,'mask':mask})
 for z in q:
  if z['layer']!='In1.Cu' or K.L.norm(z['net'])==LG:continue
  req=max(.25,float(z['clearance_mm']),gap(z['net']))+.030
  for role in('shape','zone_outline_shape'):
   mask=K.Z.bounded_buffer(z[role],req);obs.append(mask);ledger.append({'kind':'current_owned_positive_HARD','UUID':z['uuid'],'raw_net':z['net'],'role':role,'guarded_mm':req,'mask':mask})
 for v in h['vias']:
  if K.L.norm(v['net'])!=LG and not Point(v['x'],v['y']).envelope.disjoint(win.buffer(1)):obs.append(K.Z.bounded_disk(v,v['drill']/2+.280))
 for p in h['pads']:
  if K.L.norm(p['net'])!=LG or p['npth']:
   obs.extend(K.Z.bounded_buffer(s,.280)for s in K.L.poly(p.get('hole')or[])if not s.envelope.disjoint(win.buffer(1)))
 reserve,exempt=K.A.reservations()
 for area in h['rule_areas']:
  if 'In1.Cu'in area['layers']and area.get('no_zones'):obs.extend(K.Z.bounded_buffer(s,.030)for s in K.L.poly(area['outline']))
 for area in reserve['keepouts']:
  if 'In1.Cu'in area['layers']and LG not in exempt.get(area['name'],set()):obs.extend(K.Z.bounded_buffer(s,.030)for s in K.L.poly(area['outline']))
 legal=win.difference(unary_union(obs));before=cache['reference'];attempts=[];chosen=None
 for idx,row in enumerate(paths):
  pts=row['physical_only']['points_mm'];line=LineString(pts);body=K.Z.bounded_buffer(line,.105);desired=K.Z.bounded_buffer(line,.275);missing=body.difference(before);patch=set_precision(desired.intersection(legal).buffer(-.000025,quad_segs=128),.000001)
  used=[s for s in pieces(patch)if not s.intersection(missing).is_empty];patch=unary_union(used);union=before.union(patch);remain=body.difference(union);attachments=[{'WKB_SHA256':K.C.sha(s.wkb),'area_mm2':s.area,'overlap_actual_BEFORE_root_mm2':s.intersection(before).area}for s in used];blockers=[]
  for ob in ledger:
   overlap=ob['mask'].intersection(missing)
   if not overlap.is_empty:blockers.append({k:v for k,v in ob.items()if k!='mask'}|{'actual_missing_body_overlap':inf(overlap)})
  withdrawn=[{'UUID':z['uuid'],'raw_net':z['net'],'same_domain_original_native_only':True,'exact_before_fill_WKB_SHA256':K.C.sha(s.wkb),'candidate_geometric_overlap_mm2':s.intersection(patch).area}for z,s in retreat if not s.intersection(patch).is_empty]
  attempt={'index':idx,'signal_source_mm':row['source'],'signal_target_mm':row['target'],'In2_points_mm':pts,'before_body_gap':inf(missing),'new_patch':inf(patch),'after_body_gap':inf(remain),'new_reference_actual_source_attachments':attachments,'exact_HARD_blockers_to_missing_body':blockers,'original_same_domain_native_fill_retreat_obligations':withdrawn,'all_ground_plane_contact_current_oldref_native_SI_gates':'OPEN'};attempts.append(attempt)
  (OUT/(str(idx)+'-missing-body.wkb')).write_bytes(missing.wkb);(OUT/(str(idx)+'-new-patch.wkb')).write_bytes(patch.wkb);(OUT/(str(idx)+'-remaining-body-gap.wkb')).write_bytes(remain.wkb)
  print('R596_PATCH',idx,patch.area,remain.area,len(blockers),flush=True)
  if remain.is_empty and all(a['overlap_actual_BEFORE_root_mm2']>.005 for a in attachments):chosen={'attempt':attempt,'shape':patch};break
 cacheout=OUT/'only-NEW-reference-shape-nomination-and-exact-legal-mask.pkl';cacheout.write_bytes(pickle.dumps({'chosen':chosen,'legal':legal,'before_root':before,'attempts':attempts},protocol=5));put(OUT/'missing-body-source-extension-and-blocker-ledger.json',attempts);put(OUT/'receipt.json',{'verdict':'NEW_DI15_IN1_REFERENCE_EXTENSION_SOURCE_NOMINATED_INDEPENDENT_OPEN'if chosen else'NEW_DI15_IN1_REFERENCE_EXTENSION_EXACT_HARD_BLOCKER_INCOMPLETE','selected_attempt_index':chosen['attempt']['index']if chosen else None,'input_SHA256':pins,'only_NEW_reference_nomination_SHA256':sha(cacheout),'old_Cu_or_power_removed':0,'newholes_or_signalCu_emitted':0,'native_jobs':0,'adopted':False,'all_full_source_drilled_body_contacts_zero_oldref_native_current_qualification':'OPEN','elapsed_seconds':time.monotonic()-st});print('R596_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
