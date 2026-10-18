"""Attribute the saved R592 missing transport to exact current primitives.

Read-only diagnostic, no repeated site grid, clearance waiver or old Cu edit.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import restore_field_current_mixed_precision_states_r366 as MS
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI15-saved-current-In2-transport-exact-wall-diagnosis-r594'
NET='/motherboard_di/DI15_LOGIC'
def pieces(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for x in getattr(s,'geoms',[])for p in pieces(x)]
def info(s):return{'type':s.geom_type,'empty':s.is_empty,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,expected=None):
  p=Path(p);v=sha(p);assert expected is None or v==expected;pins[str(p.resolve())]=v;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793')
 g,h,b,q,c=pickle.loads(mp.read_bytes());MS.restore_bound_field_current_precision_states(b,q)
 cp=pin(H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592/bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl')
 cache=pickle.loads(cp.read_bytes());op=pin(H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592/source-and-target-continuous-ordinary-pair-options.json');options=json.loads(op.read_bytes())
 refsafe=cache['reference'].intersection(box(114,85,137,119)).buffer(-.105)
 physical=cache['free'][NET,'In2.Cu'];inner=cache['inner'];phys=pieces(physical);refs=pieces(refsafe);joined=pieces(inner)
 summary=[]
 for role in('source','target'):
  for row in options[role]:
   p=Point(row['signal']);summary.append({'role':role,**row,'physical_component_indices':[i for i,s in enumerate(phys)if s.covers(p)],'reference_component_indices':[i for i,s in enumerate(refs)if s.covers(p)],'joint_component_indices':[i for i,s in enumerate(joined)if s.covers(p)],'distance_to_physical_mm':p.distance(physical),'distance_to_reference_mm':p.distance(refsafe)})
 put(OUT/'exact-saved-port-components.json',summary)
 rec,trees=K.F.build({**h,'zones':[]});dom=h['domains_normalized'];n=NET
 gap=lambda other:.15 if dom[K.L.norm(other)]==dom[n]else .6
 original=K.C.inventory(pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a').read_bytes())[3]
 paths=[]
 for sa in options['source']:
  for ta in options['target']:
   a=Point(sa['signal']);z=Point(ta['signal']);row={'source':sa['signal'],'target':ta['signal']}
   pc=[s for s in phys if s.covers(a)and s.covers(z)];rc=[s for s in refs if s.covers(a)and s.covers(z)];ic=[s for s in joined if s.covers(a)and s.covers(z)]
   row.update({'physical_common':len(pc),'reference_common':len(rc),'joint_common':len(ic)})
   # One finite path for each independent physical/reference hypothesis.
   for label,parts in(('physical_only',pc),('reference_only',rc)):
    if not parts:continue
    pts,search=T.route(parts[0],tuple(sa['signal']),tuple(ta['signal']));pts=[[round(x,6),round(y,6)]for x,y in pts]
    if len(pts)<2:continue
    center=LineString(pts);body=K.Z.bounded_buffer(center,.105);blockers=[]
    if label=='reference_only':
     for i in trees['In2.Cu'].query(body.buffer(.7),predicate='intersects'):
      r=rec['In2.Cu'][int(i)]
      if K.L.norm(r['net'])==n:continue
      req=gap(r['net'])+.030;d=r['shape'].distance(body)
      if d<req:blockers.append({'kind':r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'distance_body_mm':d,'guarded_requirement_mm':req,'exact_shape_WKB_SHA256':K.C.sha(r['shape'].wkb)})
     for owned in q:
      if owned['layer']!='In2.Cu' or K.L.norm(owned['net'])==n:continue
      req=max(float(owned['clearance_mm']),gap(owned['net']))+.030
      for role in('shape','zone_outline_shape'):
       if owned[role].distance(body)<req:blockers.append({'kind':'owned_positive_HARD','UUID':owned['uuid'],'raw_net':owned['net'],'role':role,'distance_body_mm':owned[role].distance(body),'guarded_requirement_mm':req,'exact_shape_WKB_SHA256':K.C.sha(owned[role].wkb)})
     for zone in c['zones']:
      if K.L.norm(zone['net'])==n or(zone['uuid']in original and gap(zone['net'])==.15):continue
      req=max(float(zone['clearance_mm']),gap(zone['net']))+.030
      for sh in K.L.poly(zone['fills'].get('In2.Cu',[])):
       if sh.distance(body)<req:blockers.append({'kind':'current_filled_HARD','UUID':zone['uuid'],'raw_net':zone['net'],'distance_body_mm':sh.distance(body),'guarded_requirement_mm':req,'exact_shape_WKB_SHA256':K.C.sha(sh.wkb)})
    row[label]={'points_mm':pts,'length_mm':center.length,'search':search,'body_WKB_SHA256':K.C.sha(body.wkb),'actual_source_reference_gap':info(body.difference(cache['reference'])),'physical_blockers':blockers,'nomination_only':True}
    (OUT/(str(len(paths))+'-'+label+'-body.wkb')).write_bytes(body.wkb)
   # Diagnose nearest separate referenced free components when neither independent path exists.
   aa=[s for s in joined if s.covers(a)];zz=[s for s in joined if s.covers(z)]
   if aa and zz and not ic:
    x,y=nearest_points(aa[0],zz[0]);row['nearest_joint_component_gap_mm']={'at_mm':[list(x.coords)[0],list(y.coords)[0]],'distance_mm':x.distance(y)}
   paths.append(row)
   print('R594_PATH',sa['signal'],ta['signal'],len(pc),len(rc),len(ic),flush=True)
 put(OUT/'independent-physical-reference-transport-diagnosis.json',paths)
 put(OUT/'receipt.json',{'verdict':'SAVED_DI15_TRANSPORT_CAUSAL_DIAGNOSIS_ONLY','exact_port_components':summary,'diagnosed_pairs':len(paths),'input_SHA256':pins,'all_original_and_positive_current_Cu_fixed':True,'no_test_restart_or_native_job':True,'physical_reference_body_contacts_current_SI_acceptance':'OPEN','elapsed_seconds':time.monotonic()-st})
 print('R594_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
