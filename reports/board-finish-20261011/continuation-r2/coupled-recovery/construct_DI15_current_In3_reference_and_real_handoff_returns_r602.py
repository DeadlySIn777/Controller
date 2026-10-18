"""Focused new In3 reference and real ordinary handoffs for DI15 In2.

Old DI13/FAULT/power remains hard. Exact current/native source intersection
is nomination authority only; no generic reference-union acceptance.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,math
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import restore_field_current_mixed_precision_states_r366 as MS
import construct_DI15_current_ordinary_F_In2_F_pairs_r592 as R
import tri_route as T
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI15-current-In3-reference-real-handoff-return-constructor-r602';LG='/LOGIC_GND';NET=R.NET
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return{'type':s.geom_type,'empty':s.is_empty,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def allparts(s):
 if s.is_empty:return[]
 if s.geom_type in('Polygon','LineString','Point'):return[s]
 return[p for x in getattr(s,'geoms',[])for p in allparts(x)]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,v=None):
  p=Path(p);s=sha(p);assert v is None or s==v;pins[str(p.resolve())]=s;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes());MS.restore_bound_field_current_precision_states(b,q)
 ca=pickle.loads(pin(H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592/bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl').read_bytes());opts=json.loads(pin(H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592/source-and-target-continuous-ordinary-pair-options.json').read_bytes());cn=pickle.loads(pin(H/'DI15-actual-R157-current-native-port-return-census-r590/exact-current-DI15-physical-groups-and-actual_NATIVE-J1-reference-primitives-NOMINATION_ONLY.pkl','85ec65a59757706be27b5a329d27f4c4a56f9dc337b77d55c2130dc58f320f93').read_bytes());banks=pickle.loads(pin(H/'DI6-current-independent-all-contacts-source-reference-r580/actual-before-and-after-ten-source-bank-primitives.pkl').read_bytes())['after'][LG]
 win=box(116,85,135,116);clip=win.buffer(1);refs={ly:unary_union([r['shape'].intersection(clip)for r in banks if r['kind']=='fill'and r['layer']==ly and not r['shape'].envelope.disjoint(clip)]).intersection(cn['native_refs'][ly].intersection(clip))for ly in('In1.Cu','In4.Cu')};native3=unary_union([r['shape'].intersection(clip)for r in cn['nativeLGroot']if r['kind']=='fill'and r['layer']=='In3.Cu'and not r['shape'].envelope.disjoint(clip)]);host3=unary_union([r['shape'].intersection(clip)for r in banks if r['kind']=='fill'and r['layer']=='In3.Cu'and not r['shape'].envelope.disjoint(clip)]);before3=native3.intersection(host3)
 orig=K.C.inventory(pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a').read_bytes())[3];rec,trees=K.F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda n:.15 if dom[K.L.norm(n)]==dom[LG]else .6;obs=[];obligations=[]
 for i in trees['In3.Cu'].query(clip,predicate='intersects'):
  r=rec['In3.Cu'][int(i)]
  if K.L.norm(r['net'])==LG:continue
  req=max(.25,gap(r['net']))+.030;cut=K.Z.bounded_buffer(r['shape'],req);obs.append(cut);obligations.append({'kind':r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'requirement_mm':req,'mask':cut})
 for z in c['zones']:
  if K.L.norm(z['net'])==LG:continue
  if z['uuid']in orig and gap(z['net'])==.15:continue
  req=max(.25,float(z['clearance_mm']),gap(z['net']))+.030
  for s in K.L.poly(z['fills'].get('In3.Cu',[])):
   if s.envelope.disjoint(clip):continue
   cut=K.Z.bounded_buffer(s,req);obs.append(cut);obligations.append({'kind':'foreign_actual_fill_HARD','UUID':z['uuid'],'raw_net':z['net'],'requirement_mm':req,'mask':cut})
 for z in q:
  if z['layer']!='In3.Cu'or K.L.norm(z['net'])==LG:continue
  req=max(.25,float(z['clearance_mm']),gap(z['net']))+.030
  for role in('shape','zone_outline_shape'):
   cut=K.Z.bounded_buffer(z[role],req);obs.append(cut);obligations.append({'kind':'owned_positive_HARD','UUID':z['uuid'],'raw_net':z['net'],'role':role,'requirement_mm':req,'mask':cut})
 for v in h['vias']:
  if K.L.norm(v['net'])!=LG and not Point(v['x'],v['y']).envelope.disjoint(clip):obs.append(K.Z.bounded_disk(v,v['drill']/2+.280))
 for p in h['pads']:
  if K.L.norm(p['net'])!=LG or p['npth']:obs.extend(K.Z.bounded_buffer(s,.280)for s in K.L.poly(p.get('hole')or[])if not s.envelope.disjoint(clip))
 reserve,exempt=K.A.reservations()
 for a in h['rule_areas']:
  if 'In3.Cu'in a['layers']and a.get('no_zones'):obs.extend(K.Z.bounded_buffer(s,.030)for s in K.L.poly(a['outline']))
 for a in reserve['keepouts']:
  if 'In3.Cu'in a['layers']and LG not in exempt.get(a['name'],set()):obs.extend(K.Z.bounded_buffer(s,.030)for s in K.L.poly(a['outline']))
 legal=win.difference(unary_union(obs));potential=refs['In1.Cu'].union(before3).union(legal);inner=ca['free'][NET,'In2.Cu'].intersection(potential.buffer(-.105025,quad_segs=128));retregion=ca['via'][LG].intersection(refs['In1.Cu']).intersection(refs['In4.Cu']);attempts=[];chosen=None
 for a in opts['source']:
  for z in opts['target']:
   row={'source':a['signal'],'target':z['signal']};attempts.append(row);parts=[s for s in R.pieces(inner)if s.covers(Point(a['signal']))and s.covers(Point(z['signal']))];row['source_reference_potential_common_components']=len(parts)
   if not parts:continue
   pts,search=T.route(parts[0],tuple(a['signal']),tuple(z['signal']));pts=[[round(x,6),round(y,6)]for x,y in pts]
   if len(pts)<2 or not parts[0].covers(LineString(pts)):continue
   line=LineString(pts);body=K.Z.bounded_buffer(line,.105);missing=body.difference(refs['In1.Cu'].union(before3));desired=K.Z.bounded_buffer(line,.300);patch=set_precision(desired.intersection(legal).buffer(-.000025,quad_segs=128),.000001);ps=[p for p in R.pieces(patch)if not p.intersection(missing).is_empty];patch=unary_union(ps);remain=body.difference(refs['In1.Cu'].union(before3).union(patch));handoffs=[]
   # True source-plane changes, with two ordinary returns at each new patch span.
   for part in ps:
    hit=[s for s in allparts(line.intersection(part.buffer(-.105025,quad_segs=128)))if s.geom_type=='LineString'and s.length>0]
    if not hit:continue
    ds=sorted(line.project(Point(pt))for s in hit for pt in(s.coords[0],s.coords[-1]));ends=[ds[0],ds[-1]]
    for role,d in zip(('entry','exit'),ends):
     hand=line.interpolate(max(0,min(line.length,d)));sig=[round(hand.x,6),round(hand.y,6)];ring=Point(sig).buffer(.999,quad_segs=128).difference(Point(sig).buffer(.901,quad_segs=128));area=retregion.intersection(ring);choices=[]
     for at in R.sites(area,[sig[0]-.925,sig[1]],12):
      if not .9<=math.dist(at,sig)<=1:continue
      # A real source branch must fit on In3 and enter the new plane annularly.
      source=Point(at);ann=source.buffer(.25,quad_segs=128).difference(source.buffer(.1,quad_segs=128));contact={ly:ann.buffer(-.025,quad_segs=128).intersection(refs[ly])for ly in refs}
      if not all(s.area>.005 for s in contact.values()):continue
      rootattach=nearest_points(part.buffer(-.15,quad_segs=128),source)[0];branch=K.Z.bounded_buffer(LineString([list(rootattach.coords)[0],at]),.15)
      if legal.covers(branch)and branch.intersection(part).area>.005:choices.append({'at_mm':at,'distance_mm':math.dist(at,sig),'actual_J1_before_annuli_mm2':{ly:s.area for ly,s in contact.items()},'In3_branch_points_mm':[list(rootattach.coords)[0],at],'branch':branch})
     handoffs.append({'part_WKB_SHA256':K.C.sha(part.wkb),'role':role,'signal_reference_handoff_at_mm':sig,'ordinary_return_options':[{k:v for k,v in r.items()if k!='branch'}for r in choices]})
   row.update({'In2_points_mm':pts,'length_mm':line.length,'search':search,'new_patch':info(patch),'new_body_union_gap':info(remain),'actual_entry_exit_handoff_returns':handoffs})
   (OUT/(str(len(attempts)-1)+'-new-In3-patch.wkb')).write_bytes(patch.wkb)
   if remain.is_empty and handoffs and all(r['ordinary_return_options']for r in handoffs):chosen={'operation':row,'shape':patch,'source_pair':a,'target_pair':z};break
  if chosen:break
 file=OUT/'NEW-In3-reference-path-and-real-return-nomination.pkl';file.write_bytes(pickle.dumps({'chosen':chosen,'attempts':attempts,'legal':legal,'before_refs':refs,'before3':before3,'mask_ledger':obligations},protocol=5));put(OUT/'exact-path-and-real-handoff-return-attempts.json',attempts);put(OUT/'receipt.json',{'verdict':'DI15_NEW_IN3_REFERENCE_REAL_ORDINARY_HANDOFFS_NOMINATED_OPEN'if chosen else'DI15_NEW_IN3_REFERENCE_REAL_ORDINARY_HANDOFFS_BOUNDED_INCOMPLETE','chosen':chosen['operation']if chosen else None,'input_SHA256':pins,'nomination_file':str(file.resolve()),'nomination_SHA256':sha(file),'old_DI13_FAULT_and_power_Cu_changed':0,'pair_window_mm':[.9,1.0],'max_signal_layer_legs':3,'union_only_is_NOT_electrical_reference_qualification':True,'full_actual_drill_source_contact_current_oldref_newbody_native_SI':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R602_COMPLETE',sha(OUT/'receipt.json'),'chosen',bool(chosen),flush=True)
if __name__=='__main__':main()
