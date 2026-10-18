"""One exact-current XF F path screen using actual J1 reference.

The saved XF coupled trail was incomplete. This distinct no-drill screen
preserves its power-enable wall and every source Cu/hole/plane role.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
OUT=H/'XF-current-no-via-F-actual-J1-reference-path-r608';NET='/motherboard_operator/XF_REQUEST_BUFFER';LG='/LOGIC_GND'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pieces(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for x in getattr(s,'geoms',[])for p in pieces(x)]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes())
 nf=pin(H/'DI15-actual-R157-current-native-port-return-census-r590/exact-current-DI15-physical-groups-and-actual_NATIVE-J1-reference-primitives-NOMINATION_ONLY.pkl','85ec65a59757706be27b5a329d27f4c4a56f9dc337b77d55c2130dc58f320f93');actual=pickle.loads(nf.read_bytes())['native_refs']['In1.Cu']
 bf=pin(H/'DI6-current-independent-all-contacts-source-reference-r580/actual-before-and-after-ten-source-bank-primitives.pkl','e0c15f2c848566be8eac647e02fac80a6eead17cff97c64cdd2bf8268cb77371');bank=pickle.loads(bf.read_bytes())['after'][LG];source=unary_union([r['shape']for r in bank if r['kind']=='fill'and r['layer']=='In1.Cu']).intersection(actual)
 sp=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');identity=K.A.N.SourceNets(sp.read_bytes());old=K.C.inventory(sp.read_bytes())[3]
 a=next(p for p in h['pads']if p['uuid']=='a0011950-a497-4019-b265-c0ce2da0a4fe');z=next(p for p in h['pads']if p['uuid']=='d9a84fa6-7211-4e66-bbd7-bb0d180d00a8');assert(a['ref'],str(a['num']),K.L.norm(a['net']))==('U14016','4',NET);assert(z['ref'],str(z['num']),K.L.norm(z['net']))==('U14019','2',NET);start=[a['x'],a['y']];end=[z['x'],z['y']];win=box(286,82,310,121);clip=win.buffer(1)
 rec,trees=K.F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda n:.15 if dom[K.L.norm(n)]==dom[NET]else .6;obs=[];ledger=[]
 for i in trees['F.Cu'].query(clip,predicate='intersects'):
  r=rec['F.Cu'][int(i)]
  if K.L.norm(r['net'])==NET:continue
  req=gap(r['net'])+.025+.105;obs.append(K.Z.bounded_buffer(r['shape'].intersection(clip),req));ledger.append({'kind':r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'centre_requirement_mm':req})
 for zone in c['zones']:
  if K.L.norm(zone['net'])==NET or (zone['uuid']in old and gap(zone['net'])==.15):continue
  for sh in K.L.poly(zone['fills'].get('F.Cu',[])):
   if sh.envelope.disjoint(clip):continue
   req=max(gap(zone['net']),float(zone['clearance_mm']))+.025+.105;obs.append(K.Z.bounded_buffer(sh.intersection(clip),req));ledger.append({'kind':'current_foreign_fill_HARD','UUID':zone['uuid'],'raw_net':zone['net'],'centre_requirement_mm':req})
 for zone in q:
  if zone['layer']!='F.Cu'or K.L.norm(zone['net'])==NET:continue
  req=max(gap(zone['net']),float(zone['clearance_mm']))+.025+.105
  for role in('shape','zone_outline_shape'):
   if zone[role].envelope.disjoint(clip):continue
   obs.append(K.Z.bounded_buffer(zone[role].intersection(clip),req));ledger.append({'kind':'owned_positive_HARD','UUID':zone['uuid'],'role':role,'raw_net':zone['net'],'centre_requirement_mm':req})
 holes,_=K.hole_context(h);obs.extend(K.Z.bounded_buffer(sh,.380)for sh in holes if not sh.envelope.disjoint(clip));reservation,exempt=K.A.reservations()
 for area in h['rule_areas']:
  if 'F.Cu'in area['layers']and area.get('no_tracks'):obs.extend(K.Z.bounded_buffer(sh,.130)for sh in K.L.poly(area['outline']))
 for area in reservation['keepouts']:
  if 'F.Cu'in area['layers']and NET not in exempt.get(area['name'],set()):obs.extend(K.Z.bounded_buffer(sh,.130)for sh in K.L.poly(area['outline']))
 free=win.difference(unary_union(obs)).intersection(source.intersection(clip).buffer(-.105005,quad_segs=128));common=[p for p in pieces(free)if p.covers(Point(start))and p.covers(Point(end))];selected=None;tracks=[];chunks={};attempts=[]
 for part in common:
  pts,search=T.route(part,tuple(start),tuple(end));pts=[[round(x,6),round(y,6)]for x,y in pts]
  if len(pts)<2 or not part.covers(LineString(pts)):attempts.append({'search':search,'points_mm':pts,'verdict':'NO_EXACT_COMMON_PATH'});continue
  body=K.Z.bounded_buffer(LineString(pts),.1);raw=body.difference(source);row={'search':search,'points_mm':pts,'length_mm':LineString(pts).length,'literal_full_body_In1_source_gap_empty':raw.is_empty,'literal_full_body_gap_WKB_SHA256':K.C.sha(raw.wkb)};attempts.append(row)
  if not raw.is_empty:continue
  selected=row
  for x,y in zip(pts,pts[1:]):
   uid,ch=identity.serial_segment(NET,'F.Cu',x,y,.2);assert uid not in old;chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(NET),'layer':'F.Cu','w':.2,'a':x,'b':y})
  identity.assert_chunks(chunks);break
 file=OUT/'only-NEW-XF-F-no-drill-NOMINEE.pkl';file.write_bytes(pickle.dumps({'tracks':tracks,'vias':[],'exact_new_chunks':chunks,'original_deletes':{},'selected':selected,'reference_layer':'In1.Cu'},protocol=5));cache=OUT/'exact-current-source-and-hard-F-regions-NOMINATION_ONLY.pkl';cache.write_bytes(pickle.dumps({'source':source,'free':free,'obstacles':ledger},protocol=5));(OUT/'receipt.json').write_text(json.dumps({'verdict':'XF_NEW_NO_DRILL_F_REFERENCE_PATH_NOMINATED_OPEN'if selected else'XF_NEW_NO_DRILL_F_REFERENCE_PATH_BOUNDED_INCOMPLETE','input_SHA256':pins,'exact_pad_UUIDs':[a['uuid'],z['uuid']],'source_F_component_count':sum(p.covers(Point(start))for p in pieces(free)),'target_F_component_count':sum(p.covers(Point(end))for p in pieces(free)),'common_components':len(common),'attempts':attempts,'selected':selected,'sparse_packet_file':str(file.resolve()),'sparse_packet_SHA256':sha(file),'cached_region_SHA256':sha(cache),'native_jobs':0,'old_items_changed':0,'adopted':False,'full_current_native_source_old_contacts_reference_SI':'OPEN','elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R608_COMPLETE',sha(OUT/'receipt.json'),bool(selected),flush=True)
if __name__=='__main__':main()
