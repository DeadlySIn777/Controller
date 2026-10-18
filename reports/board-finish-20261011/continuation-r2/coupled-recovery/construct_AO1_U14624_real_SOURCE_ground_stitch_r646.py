"""Real SOURCE-ground stitch into U14624.3, no signal pairing/cap waiver."""
from pathlib import Path
import sys,json,pickle,hashlib,time,re
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_ao1_positive_operation_r4 as SERIAL
import construct_DI15_current_ordinary_F_In2_F_pairs_r592 as S
import R157_native_selected_actual_conversion_r673 as N
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
OUT=H/'AO1-U14624-three-real-SOURCE-COM-ordinary-ground-stitch-r646';COM='/motherboard_analog_output/AO1_COM'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 ca=pickle.loads(pin(H/'AO1-ENABLE-current-ordinary-F-In3-B-two-pair-constructor-r626/bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl').read_bytes());sf=pin(H/'AO1-COM-actual-full-native-current-source-and-two-residual-port-binding-r622/exact_actual_current_AO1_COM_source_and_ports_NOMINATION_ONLY.pkl','02e9ea37628b2dba138d1e57514a390f1c4419ef3ca8c66ed6f2653eecb6b72b');src=pickle.loads(sf.read_bytes());mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');_,h,_,_,_=pickle.loads(mp.read_bytes());ip=pin(H/'AO1-COM-six-actual-native-ground-islands-source-bridge-census-r632/actual-six-COM-islands-and-SOURCE-metals-NOMINATION_ONLY.pkl','3ed53fb76aaee578bee266481e72135e52bc0115d1caeb659b4db2e2196c409e');islands=pickle.loads(ip.read_bytes());p=next(p for p in h['pads']if p['uuid']=='19434a4b-d4ed-4193-90b1-b90a71062411');assert(p['ref'],str(p['num']),K.L.norm(p['net']))==('U14624','3',COM);start=[p['x'],p['y']];face=unary_union([r for r in S.pieces(ca['free'][COM,'F.Cu'])if r.covers(Point(start))]);sites=ca['via'][COM].intersection(face);win=box(347,137,384,160);clip=win.buffer(1);dom=h['domains_normalized'];gf=pin(N.R157/'actual-full-refill-geometry.json','421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b');ng=json.loads(gf.read_bytes());np=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb','3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38');native=K.C.inventory(np.read_bytes())[3];foreign=[]
 for zone in ng['zones']:
  if K.L.norm(zone['net'])==COM:continue
  m=re.search(rb'\(connect_pads(?:\s+[^()\s]+)?\s*\(clearance\s+([0-9.]+)\)',native[zone['uuid']]);assert m,zone['uuid'];gap=.15 if dom[K.L.norm(zone['net'])]==dom[COM]else .6;radius=.25+max(float(m.group(1)),gap)+.025
  for ly,rs in zone['fills'].items():
   for sh in K.L.poly(N.O.polys(rs)):
    if sh.envelope.disjoint(clip):continue
    foreign.append(K.Z.bounded_buffer(sh.intersection(clip),radius))
 sites=sites.difference(unary_union(foreign));references={ly:shape.intersection(clip)for ly,shape in src['references'].items()};attempts=[];selected=None;nt=[];nv=[];chunks={};sp=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');identity=K.A.N.SourceNets(sp.read_bytes());original=K.C.inventory(sp.read_bytes())[3]
 print('R646_REGIONS',face.area,sites.area,flush=True)
 for at in S.sites(sites,[356.5,143.5],40):
  ann=Point(at).buffer(.225,quad_segs=128).difference(Point(at).buffer(.125,quad_segs=128));contacts={ly:ann.intersection(s)for ly,s in references.items()};row={'ordinary_COM_ground_at_mm':at,'actual_BEFORE_SOURCE_annular_interiors_mm2':{ly:s.area for ly,s in contacts.items()}};attempts.append(row)
  if not all(s.area>.005 for s in contacts.values()):continue
  pts,search=T.route(face,tuple(start),tuple(at));pts=[[round(x,6),round(y,6)]for x,y in pts]
  if len(pts)<2 or not face.covers(LineString(pts)):continue
  row.update({'F_points_mm':pts,'width_mm':.20,'F_length_mm':LineString(pts).length,'search':search});selected=row
  uid,ch=SERIAL.serial_via(identity,COM,at);assert uid not in original;chunks[uid]=ch;nv.append({'uuid':uid,'net':identity.raw(COM),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS),'prospective_not_observed_actual_CPP_REQUIRED':True})
  for a,z in zip(pts,pts[1:]):uid,ch=identity.serial_segment(COM,'F.Cu',a,z,.20);assert uid not in original;chunks[uid]=ch;nt.append({'uuid':uid,'net':identity.raw(COM),'layer':'F.Cu','a':a,'b':z,'w':.20})
  identity.assert_chunks(chunks);break
 contactloss=[];gains=None
 if selected:
  before=islands['actual_ground_candidate'];after={**before,'tracks':before['tracks']+nt,'vias':before['vias']+nv};groups=K.physical(after,COM,K.hole_context(after))[1];root=K.root(groups,'U14619','7');contactloss=K.contact_losses([r['group']for r in islands['islands'].values()],groups)[1];assert not contactloss;assert any(r['kind']=='pad'and r['uuid']==p['uuid']for r in root);gains={'before_source_nonfill_keys':len(K.keys(islands['islands'][islands['source_group']]['group'])),'prospective_after_source_nonfill_keys':len(K.keys(root))}
 f=OUT/'only-NEW-COM-U14624-ground-stitch-and-F-stub-NOMINATION_ONLY.pkl';f.write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'exact_new_chunks':chunks,'original_deletes':{},'selected':selected,'source_gains':gains},protocol=5));(OUT/'receipt.json').write_text(json.dumps({'verdict':'REAL_COM_SOURCE_ORDINARY_GROUND_STITCH_TO_U14624_NOMINATED_INDEPENDENT_OPEN'if selected else'REAL_COM_SOURCE_ORDINARY_GROUND_STITCH_TO_U14624_BOUNDED_INCOMPLETE','input_SHA256':pins,'source_reachable_F_face_mm2':face.area,'all_layer_and_native_foreign_plane_preserving_new_via_region_mm2':sites.area,'attempts':attempts,'selected':selected,'prospective_source_key_gains':gains,'old_six_COM_contact_losses_prospective':contactloss,'packet_file':str(f.resolve()),'packet_SHA256':sha(f),'old_Cu_or_foreign_planes_changed':0,'new_vias':len(nv),'new_F_tracks':len(nt),'GROUND_only_no_SG_return_pair_or_SOURCE_shadow_waiver':True,'actual_after_CPP_masks_antipads_allcontacts_oldrefs_current_final_loop_native_SI':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R646_COMPLETE',sha(OUT/'receipt.json'),bool(selected),flush=True)
if __name__=='__main__':main()
