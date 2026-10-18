"""Concrete one-original-PG-track ordinary return escape nomination only."""
import sys,json,pickle,copy,math,time,uuid
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import restore_SAFE_generated_precision_states_r168 as PS
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
C=A.C;LAYERS=K.LAYERS;O=H/'U21003-exact-PG-single-track-return-nomination-r238'
PG='/motherboard_identity_io/FREQ_ID_POWER_GOOD_LOCAL';OLD='342f9640-d003-4d9f-8bee-e095302a3fbb'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir()
 d=H.parent/'sbc-power/U21003-cap-pullup-rotated-return-nominees-r245';rr=A.read(d/'receipt.json');assert C.sha(rr)=='2e8e7da3b72ea8f74bd0bd2b754cacc24df5164cd986c5bd41b6ce8f9ab875a2';raw=A.read(d/'owned-cap-translation-host-checkpoint.pkl');assert C.sha(raw)=='23b44e576fae6c55009434922f71a95e7ca706c44d3c7ca95266e32227e403c3';g,h,b,q,c=pickle.loads(raw);PS.restore_bound_generated_precision_states(b,q);assert C.sha(A.read(H.parent/'sbc-power/U21003-exact-margin-pose-independent-wall-scope-r246/receipt.json'))=='bcf745a97800bf6b84586e5badaf39a6ea698ec21f01f4209540b46afa784050';newpose=pickle.loads(A.read(d/'new-track-objects.pkl'));assert len(newpose)==6 and all(t in h['tracks']for t in newpose)
 old=next(t for t in h['tracks']if t['uuid']==OLD);assert old=={'uuid':OLD,'net':PG,'a':[332.05,145.85],'b':[335.85,142.049999],'w':.2,'layer':'In3.Cu','locked':True};native=A.read(H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb');assert C.sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';inventory=C.inventory(native);assert OLD in inventory[2];identity=A.N.SourceNets(native);assert identity.raw(PG)==PG and identity.raw('/LOGIC_GND')=='/LOGIC_GND';(O/'exact-original-PG-remove.chunk').write_bytes(inventory[2][OLD])
 ground={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'U21003-PG-return-r238:actual332.507772/145.5375')),'net':'/LOGIC_GND','x':332.507772,'y':145.5375,'d':.5,'drill':.2,'span':list(LAYERS),'flashed':list(LAYERS),'mask_provenance':'new ordinary conservative all6; native attestation OPEN'};vpoint=Point(ground['x'],ground['y']);retained={**h,'tracks':[t for t in h['tracks']if t['uuid']!=OLD]};rec,trees=F.build({**retained,'zones':[]});dom=h['domains_normalized'];gap=lambda a,b:.15 if dom.get(L.norm(a))==dom.get(L.norm(b))else .6
 checks=[];errors=[];planecuts=[];smd=[(p['uuid'],p['ref'],p['num'],sh)for p in h['pads']if p['smd']for layer,rs in p['layers'].items()if layer in('F.Cu','B.Cu')for sh in L.poly(rs)];st=STRtree([r[3]for r in smd]);holeitems=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];holeitems.append((ground['uuid'],Point(ground['x'],ground['y']).buffer(.1,quad_segs=128)));ht=STRtree([r[1]for r in holeitems])
 def check(kind,other,layer,actual,required):
  row={'kind':kind,'other_UUID':other,'layer':layer,'actual_gap_mm':actual,'required_mm':required};checks.append(row)
  if actual<required:errors.append(row)
 for layer in LAYERS:
  for j in trees[layer].query(vpoint.buffer(1.1),predicate='intersects'):
   r=rec[layer][int(j)]
   if L.norm(r['net'])=='/LOGIC_GND':continue
   if r['kind']=='via':t=r['source'];actual=vpoint.distance(Point(t['x'],t['y']))-(ground['d']+t['d'])/2
   elif r['kind']=='track'and not r['source'].get('m'):t=r['source'];actual=vpoint.distance(LineString([t['a'],t['b']]))-ground['d']/2-t['w']/2
   else:actual=vpoint.distance(r['shape'])-ground['d']/2
   check('new_return_true_all6_'+r['kind'],r['uuid'],layer,actual,gap(ground['net'],r['net'])+.025)
 nearest=smd[int(st.nearest(vpoint))];smgap=vpoint.distance(nearest[3])-.1-.005;drgap=min((vpoint.distance(sh)-.1-.005,uid)for uid,sh in holeitems if uid!=ground['uuid']);pitch=min((vpoint.distance(Point(v['x'],v['y'])),v['uuid'])for v in h['vias']);check('ordinary_return_SMD',nearest[0],'all6',smgap,.275);check('ordinary_return_every_hole',drgap[1],'all6',drgap[0],.275);check('ordinary_return_pitch',pitch[1],'all6',pitch[0],.815)
 for zone in c['zones']:
  if L.norm(zone['net'])=='/LOGIC_GND':continue
  required=max(float(zone['clearance_mm']),gap('/LOGIC_GND',zone['net']))+.025
  for layer,records in zone['fills'].items():
   shapes=L.poly(records)
   if not shapes:continue
   actual=vpoint.distance(unary_union(shapes))-.25
   if actual<required:planecuts.append({'zone_UUID':zone['uuid'],'raw_net':zone['net'],'layer':layer,'actual_gap_mm':actual,'required_mm':required,'prospective_outward_antipad_radius_mm':max(.3751,.25+required+.0001),'owned_or_native_actual_contacts_and_source_retention_before_cut':'OPEN; no retreat credited by nomination'})
 res,ex=A.reservations()
 for rule in h['rule_areas']:
  if rule.get('no_vias')and set(LAYERS)&set(rule['layers'])and any(vpoint.distance(sh)-.25<.025 for sh in L.poly(rule['outline'])):errors.append({'kind':'original_native_no_vias','rule_UUID':rule['uuid']})
 for rule in res['keepouts']:
  if '/LOGIC_GND'not in ex.get(rule['name'],set())and set(LAYERS)&set(rule['layers'])and any(vpoint.distance(sh)-.25<.025 for sh in L.poly(rule['outline'])):errors.append({'kind':'frozen_return_via_reservation','rule':rule['name']})
 # Actual source reference, independent of cached proxy plane-by-name credit.
 ctx=K.hole_context(c);_,lg=K.physical(c,'/LOGIC_GND',ctx);root=K.root(lg,'J11001','2');refs=K.source_refs(root);ann=vpoint.buffer(.25,quad_segs=128).difference(vpoint.buffer(.1,quad_segs=128));inner={plane:ann.intersection(refs[layer].buffer(-.075,quad_segs=128)).area for layer,plane in(('F.Cu','In1.Cu'),('B.Cu','In4.Cu'))};usedref=refs['In3.Cu'].difference(vpoint.buffer(.1,quad_segs=128));plans=[];positive=[]
 for y in(146.1,146.175,146.25,146.325):
  for x in(333.15,333.225,333.3,333.375):
   points=[old['a'],[332.05,y],[x,y],[max(x,333.35),145.05],[333.7,144.2],old['b']];tracks=[];bad=[];bodygaps=[]
   for i,(a,e)in enumerate(zip(points,points[1:])):
    t={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'U21003-PG-r238:'+str((x,y,i)))),'net':PG,'layer':'In3.Cu','w':.2,'a':a,'b':e,'locked':True};axis=LineString([a,e]);body=Z.bounded_buffer(axis,.1);tracks.append(t)
    for j in trees['In3.Cu'].query(body.buffer(.7),predicate='intersects'):
     r=rec['In3.Cu'][int(j)]
     if L.norm(r['net'])==PG:continue
     if r['kind']=='via':v=r['source'];actual=axis.distance(Point(v['x'],v['y']))-(.2+v['d'])/2
     elif r['kind']=='track'and not r['source'].get('m'):s=r['source'];actual=axis.distance(LineString([s['a'],s['b']]))-(.2+s['w'])/2
     else:actual=axis.distance(r['shape'])-.1
     required=gap(PG,r['net'])+.025
     if actual<required:bad.append({'kind':'new_true_PG_track_'+r['kind'],'segment':i,'other_UUID':r['uuid'],'other_net':r['net'],'actual_mm':actual,'required_mm':required})
    actual=axis.distance(vpoint)-.35
    if actual<.175:bad.append({'kind':'PG_to_new_ground_return','segment':i,'actual_mm':actual,'required_mm':.175})
    for j in ht.query(body.buffer(.3),predicate='intersects'):
     uid,hole=holeitems[int(j)];owner=next((v for v in h['vias']if v['uuid']==uid),None)
     if owner and L.norm(owner['net'])==PG:continue
     actual=body.distance(hole)-.005
     if actual<.275:bad.append({'kind':'PG_to_every_foreign_hole','segment':i,'other_UUID':uid,'actual_mm':actual,'required_mm':.275})
    for zone in q:
     if zone['layer']!='In3.Cu'or L.norm(zone['net'])==PG or body.distance(zone['shape'])>.8:continue
     actual=axis.distance(zone['shape'])-.1;required=max(float(zone['clearance_mm']),gap(PG,zone['net']))+.025
     if actual<required:bad.append({'kind':'PG_to_hard_current_owned_plane','segment':i,'other_UUID':zone['uuid'],'actual_mm':actual,'required_mm':required})
    bg=body.difference(usedref);bodygaps.append({'segment':i,'actual_J1_In4_body_gap_mm2':bg.area,'gap_empty':bg.is_empty})
    for rule in h['rule_areas']:
     if 'In3.Cu'in rule['layers']and rule.get('no_tracks')and any(body.distance(sh)<.025 for sh in L.poly(rule['outline'])):bad.append({'kind':'native_track_keepout','segment':i,'rule_UUID':rule['uuid']})
   row={'points':points,'tracks':tracks,'physical_errors':bad,'new_full_body_actual_J1_In4_gaps':bodygaps,'width_locked_endpoints_original_exact':True,'extra_signal_barrels':0,'source_return_contact_full_ALL77_current_old_reference_native_OPEN':True};plans.append(row)
   if not bad and not errors and all(v>.004 for v in inner.values()):positive.append(row)
 put(O/'ordinary-return-true-all6-checks.json',checks);put(O/'ordinary-return-true-all6-errors.json',errors);put(O/'ordinary-return-required-actual-plane-cut-obligations.json',planecuts);put(O/'all-exact-local-PG-route-plans.json',plans);(O/'concrete-physical-nominee-objects.pkl').write_bytes(pickle.dumps({'exact_original_delete':old,'new_return':ground,'plans':positive},protocol=5));result={'verdict':'POSITIVE_CONCRETE_PG_LOCAL_DISCRETE_GEOMETRY_NOMINATION_PLANE_CUTS_FULL_GATES_OPEN'if positive else'NO_DISCRETE_POSITIVE_IN_ENUMERATED_EXACT_PG_DETOURS','R245_checkpoint_sha256':C.sha(raw),'R245_receipt_sha256':C.sha(rr),'exact_original_PG_chunk_sha256':C.sha(inventory[2][OLD]),'owned_only_original_PG_delete_UUID':OLD,'exact_new_ground_return':ground,'actual_before_J1_In1_In4_finite_interior_annular_overlap_mm2':inner,'return_distance_to_original_IO3_62cc_mm':math.dist([331.75,145.1],[ground['x'],ground['y']]),'ordinary_return_SMD_gap_mm':smgap,'ordinary_return_every_hole_gap_mm':drgap,'ordinary_return_pitch':pitch,'true_return_errors':errors,'required_native_owned_plane_cut_obligations':planecuts,'enumerated_routes':len(plans),'discrete_positive_routes':len(positive),'all_new_body_refs_and_retained_reference_full_contact_source_core_peer_CURRENT_native':'OPEN; no old own aperture or plane-by-name credit','quiet_UV_R21005_all_other_original_Cu_FP_pose_rules_unchanged_from_exact_R245':True,'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',result);print(json.dumps({'receipt_sha256':C.sha((O/'receipt.json').read_bytes()),'positive_routes':len(positive),'return_errors':len(errors),'plane_cut_obligations':len(planecuts),'source_annuli':inner}),flush=True)
if __name__=='__main__':main()
