"""Construct an actual-J1-attached In1 shadow and new no-via XF F path.

All foreign current/actual plane pieces stay HARD. No old copper, negative
outline or holes are emitted. Positive output is a nomination only.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,uuid
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import R157_native_selected_actual_conversion_r673 as N
import tri_route as T
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
OUT=H/'XF-actual-J1-positive-In1-shadow-no-drill-F-path-r618';NET='/motherboard_operator/XF_REQUEST_BUFFER';LG='/LOGIC_GND'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for x in getattr(s,'geoms',[])for p in parts(x)]
def inf(s):return{'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes());cache=pickle.loads(pin(H/'XF-current-no-via-F-actual-J1-reference-path-r608/exact-current-source-and-hard-F-regions-NOMINATION_ONLY.pkl').read_bytes());before=cache['source'];sp=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');raw=sp.read_bytes();identity=K.A.N.SourceNets(raw);original=K.C.inventory(raw)[3];N.assert_R157_actual_before();gf=pin(N.R157/'actual-full-refill-geometry.json','421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b');ng=json.loads(gf.read_bytes())
 a=next(p for p in h['pads']if p['uuid']=='a0011950-a497-4019-b265-c0ce2da0a4fe');z=next(p for p in h['pads']if p['uuid']=='d9a84fa6-7211-4e66-bbd7-bb0d180d00a8');start=[a['x'],a['y']];end=[z['x'],z['y']];win=box(286,82,310,121);clip=win.buffer(1);rec,trees=K.F.build({**h,'zones':[]});dom=h['domains_normalized'];domain_gap=lambda n,net:.15 if dom[K.L.norm(n)]==dom[net]else .6;reservation,exempt=K.A.reservations();ledger=[];planeobs=[];fobs=[]
 for ly,net,out in(('F.Cu',NET,fobs),('In1.Cu',LG,planeobs)):
  for i in trees[ly].query(clip,predicate='intersects'):
   r=rec[ly][int(i)]
   if K.L.norm(r['net'])==net:continue
   req=domain_gap(r['net'],net)+.025+(.105 if ly=='F.Cu'else 0);mask=K.Z.bounded_buffer(r['shape'].intersection(clip),req);out.append(mask);ledger.append({'kind':r['kind'],'UUID':r['uuid'],'layer':ly,'net':r['net'],'guarded_mm':req,'mask':mask})
  for zone in c['zones']:
   if K.L.norm(zone['net'])==net:continue
   if ly=='F.Cu'and zone['uuid']in original and domain_gap(zone['net'],net)==.15:continue
   req=max(float(zone['clearance_mm']),domain_gap(zone['net'],net),.15)+.025+(.105 if ly=='F.Cu'else 0)
   for sh in K.L.poly(zone['fills'].get(ly,[])):
    if sh.envelope.disjoint(clip):continue
    mask=K.Z.bounded_buffer(sh.intersection(clip),req);out.append(mask);ledger.append({'kind':'current_foreign_fill_HARD','UUID':zone['uuid'],'layer':ly,'net':zone['net'],'guarded_mm':req,'mask':mask})
  for zone in q:
   if zone['layer']!=ly or K.L.norm(zone['net'])==net:continue
   req=max(float(zone['clearance_mm']),domain_gap(zone['net'],net),.15)+.025+(.105 if ly=='F.Cu'else 0)
   for role in('shape','zone_outline_shape'):
    if zone[role].envelope.disjoint(clip):continue
    mask=K.Z.bounded_buffer(zone[role].intersection(clip),req);out.append(mask);ledger.append({'kind':'owned_positive_HARD','UUID':zone['uuid'],'layer':ly,'role':role,'net':zone['net'],'guarded_mm':req,'mask':mask})
  for area in h['rule_areas']:
   if ly in area['layers']and area.get('no_tracks'if ly=='F.Cu'else'no_zones'):out.extend(K.Z.bounded_buffer(sh,.130 if ly=='F.Cu'else .025)for sh in K.L.poly(area['outline']))
  for area in reservation['keepouts']:
   if ly in area['layers']and net not in exempt.get(area['name'],set()):out.extend(K.Z.bounded_buffer(sh,.130 if ly=='F.Cu'else .025)for sh in K.L.poly(area['outline']))
 # Fresh FULL native foreign In1 fill is additional HARD authority, not an
 # unselected or older cached substitute. Every old body stays unchanged.
 for zone in ng['zones']:
  if K.L.norm(zone['net'])==LG:continue
  oldzone=next(z for z in c['zones']if z['uuid']==zone['uuid']);req=max(.15,float(oldzone['clearance_mm']),domain_gap(zone['net'],LG))+.025
  for sh in K.L.poly(N.O.polys(zone['fills'].get('In1.Cu',[]))):
   if sh.envelope.disjoint(clip):continue
   mask=K.Z.bounded_buffer(sh.intersection(clip),req);planeobs.append(mask);ledger.append({'kind':'FULL_native_foreign_In1_fill_HARD','UUID':zone['uuid'],'layer':'In1.Cu','net':zone['net'],'guarded_mm':req,'mask':mask})
 holes,_=K.hole_context(h);fobs.extend(K.Z.bounded_buffer(sh,.380)for sh in holes if not sh.envelope.disjoint(clip))
 for v in h['vias']:
  if Point(v['x'],v['y']).envelope.disjoint(clip):continue
  planeobs.append(K.Z.bounded_disk(v,v['drill']/2 if K.L.norm(v['net'])==LG else max(v['drill']/2+.275,v['d']/2+domain_gap(v['net'],LG)+.025)))
 for p in h['pads']:
  for sh in K.L.poly(p.get('hole')or[]):
   if not sh.envelope.disjoint(clip):planeobs.append(sh if K.L.norm(p['net'])==LG and not p['npth']else K.Z.bounded_buffer(sh,.275))
 legal=win.difference(unary_union(planeobs));ff=win.difference(unary_union(fobs));potential=before.intersection(clip).union(legal).buffer(-.105025,quad_segs=128);free=ff.intersection(potential);common=[p for p in parts(free)if p.covers(Point(start))and p.covers(Point(end))];attempts=[];chosen=None
 print('R618_REGIONS',legal.area,'source',free.covers(Point(start)),'target',free.covers(Point(end)),'common',len(common),flush=True)
 for component in common:
  pts,search=T.route(component,tuple(start),tuple(end));pts=[[round(x,6),round(y,6)]for x,y in pts]
  if len(pts)<2 or not component.covers(LineString(pts)):continue
  line=LineString(pts);body=K.Z.bounded_buffer(line,.1);desired=K.Z.bounded_buffer(line,.30);patch=set_precision(desired.intersection(legal).buffer(-.000025,quad_segs=128),.000001);used=[p for p in parts(patch)if not p.intersection(body.difference(before)).is_empty];patch=unary_union(used);branches=[];branchfree=legal.buffer(-.150025,quad_segs=128)
  for part in used:
   if part.intersection(before).area>.005:continue
   found=False
   for face in parts(branchfree):
    pp=part.buffer(-.150025,quad_segs=128).intersection(face);ss=before.intersection(face).buffer(-.025,quad_segs=128)
    if pp.is_empty or ss.is_empty:continue
    x,y=nearest_points(pp,ss);bp,rs=T.route(face,tuple(x.coords[0]),tuple(y.coords[0]));bp=[[round(x,6),round(y,6)]for x,y in bp]
    if len(bp)<2 or not face.covers(LineString(bp)):continue
    branch=set_precision(K.Z.bounded_buffer(LineString(bp),.15),.000001)
    if not legal.covers(branch)or branch.intersection(part).area<=.005 or branch.intersection(before).area<=.005:continue
    branches.append({'points_mm':bp,'shape':branch,'search':rs,'overlap_actual_J1_mm2':branch.intersection(before).area});found=True;break
   if not found:break
  final=unary_union([patch]+[r['shape']for r in branches]);remaining=body.difference(before.union(final));attachments=[{'shape_WKB_SHA256':K.C.sha(p.wkb),'actual_J1_overlap_mm2':p.intersection(before).area}for p in parts(final)];row={'points_mm':pts,'search':search,'length_mm':line.length,'positive_patch':inf(final),'full_body_remaining_gap':inf(remaining),'source_attachments':attachments,'branches':[{k:v for k,v in r.items()if k!='shape'}for r in branches]};attempts.append(row)
  (OUT/(str(len(attempts))+'-positive-LG-In1-shadow.wkb')).write_bytes(final.wkb);(OUT/(str(len(attempts))+'-remaining-body-gap.wkb')).write_bytes(remaining.wkb)
  if remaining.is_empty and attachments and all(r['actual_J1_overlap_mm2']>.005 for r in attachments):chosen={'operation':row,'shape':final};break
 nt=[];chunks={};positive=None
 if chosen:
  for x,y in zip(chosen['operation']['points_mm'],chosen['operation']['points_mm'][1:]):
   uid,ch=identity.serial_segment(NET,'F.Cu',x,y,.2);assert uid not in original;chunks[uid]=ch;nt.append({'uuid':uid,'net':identity.raw(NET),'layer':'F.Cu','a':x,'b':y,'w':.2})
  identity.assert_chunks(chunks);uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'Controller/XF/R618/actual-J1-In1-positive-shadow/'+K.C.sha(chosen['shape'].wkb)));positive={'uuid':uid,'net':identity.raw(LG),'layer':'In1.Cu','shape':chosen['shape'],'zone_outline_shape':chosen['shape'],'priority':127,'clearance_mm':.15,'min_thickness_mm':.15,'island_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.30,'source_root_selector':['J11001','2'],'native_AFTER_actual_fill_masks_current_all_old_contact_reference':'OPEN'}
 file=OUT/'only-NEW-XF-F-and-positive-LG-In1-NOMINATION_ONLY.pkl';file.write_bytes(pickle.dumps({'tracks':nt,'vias':[],'exact_new_chunks':chunks,'original_deletes':{},'positive':positive,'chosen':chosen,'mask_ledger':ledger,'before_actual_current_J1':before,'legal_positive_mask':legal,'free_F':ff},protocol=5));blockers=[]
 for p in(start,end):
  disk=Point(p).buffer(.105,quad_segs=128);blockers.append({'at_mm':p,'LG_shadow_endpoint_HARD_masks':[ {k:v for k,v in r.items()if k!='mask'}for r in ledger if r['layer']=='In1.Cu'and r['mask'].intersects(disk)]})
 (OUT/'receipt.json').write_text(json.dumps({'verdict':'XF_NEW_SOURCE_J1_IN1_POSITIVE_SHADOW_NO_DRILL_F_NOMINATED_OPEN'if chosen else'XF_NEW_SOURCE_J1_IN1_POSITIVE_SHADOW_NO_DRILL_F_BOUNDED_INCOMPLETE','input_SHA256':pins,'common_physical_plus_reference_potential_components':len(common),'attempts':attempts,'endpoint_shadow_blockers':blockers,'sparse_packet_file':str(file.resolve()),'sparse_packet_SHA256':sha(file),'new_tracks':len(nt),'new_positive_LG_In1_shapes':int(positive is not None),'old_Cu_or_foreign_fill_changed':0,'new_vias':0,'native_jobs':0,'adopted':False,'all_actual_source_drill_oldcontacts_reference_minfeature_current_native_SI':'OPEN','elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R618_COMPLETE',sha(OUT/'receipt.json'),bool(chosen),len(nt),flush=True)
if __name__=='__main__':main()
