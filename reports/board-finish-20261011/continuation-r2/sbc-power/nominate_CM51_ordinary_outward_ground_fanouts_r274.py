"""Finite CM51 ordinary ground fanouts, actual source annuli; no current credit.

Uses a frozen diagnostic head only. Original native planes/rules/poses are
immutable; all intersected foreign fills/owned roles become explicit local
antipad obligations for the later current-head constructor and full proof.
"""
import hashlib,json,math,pickle,sys,uuid,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
O=H/'sbc-power/CM51-ordinary-outward-ground-fanout-nominations-r274'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def literal(s):
 x=set_precision(s,0);assert x.wkb==s.wkb;return x
def main():
 assert not O.exists();O.mkdir()
 base=H/'sbc-power/R270-true-literal-DOB-current-filled-alignment-requalification-r271/T4-plus-R7';mp=base/'model.pkl'
 assert sha(mp)=='3d086d6f0935cd1760dc95c383049f04e86a31b2c4fb00d925e1d1c43d0be006'
 g,h,b,q,c=pickle.loads(mp.read_bytes());gp=base/'actual-drilled-groups.pkl';groups=pickle.loads(gp.read_bytes());root=K.root(groups['/LOGIC_GND'],'J11001','2');refs={l:literal(s)for l,s in K.source_refs(root).items()}
 sr=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sr)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';ident=A.N.SourceNets(sr.read_bytes());assert ident.raw('/LOGIC_GND')=='/LOGIC_GND'
 dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get('/LOGIC_GND')else .6
 rec,trees=F.build({**c,'zones':[]});fills,filltrees=F.build({**c,'pads':[],'tracks':[],'vias':[],'shapes':[]})
 holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])]
 ht=STRtree([s for uid,n,s in holes]);smd=[(p,s)for p in h['pads']if p['smd']for l,ps in p['layers'].items()if l in('F.Cu','B.Cu')for s in L.poly(ps)];st=STRtree([s for p,s in smd]);vps=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vps)
 reserved,exempt=A.reservations();outline=unary_union(L.poly(h['outline'])).buffer(-.525)
 cm=sorted([p for p in h['pads']if p['ref']in('J15001','J15002')and p['net']=='/LOGIC_GND'],key=lambda p:(p['ref'],p['y'],p['x']));assert len(cm)==51
 results=[];accepted=[];tracks=[];vias=[]
 for p in cm:
  sign=-1 if p['y']in(167.175,201.175)else 1;variants=[]
  for off in(.75,1.,1.25,1.5,1.75,2.,2.5,3.,4.,5.,7.5,10.):
   xy=[p['x'],round(p['y']+sign*off,6)];pt=Point(xy);axis=LineString([[p['x'],p['y']],xy]);vb=literal(Z.bounded_buffer(pt,.25));tb=literal(Z.bounded_buffer(axis,.1));errors=[];checks=[];cuts=[]
   for layer in K.LAYERS:
    for j in trees[layer].query(vb.buffer(.8),predicate='intersects'):
     r=rec[layer][int(j)]
     if L.norm(r['net'])=='/LOGIC_GND':continue
     if r['kind']=='track':t=r['source'];d=pt.distance(LineString([t['a'],t['b']]))-.25-t['w']/2
     elif r['kind']=='via':v=r['source'];d=pt.distance(Point(v['x'],v['y']))-.25-v['d']/2
     else:d=pt.distance(r['shape'])-.25
     row={'kind':'via_to_'+r['kind'],'layer':layer,'foreign_UUID':r['uuid'],'net':r['net'],'true_gap_mm':d,'required_native_mm':gap(r['net']),'required_planner_mm':gap(r['net'])+.025};checks.append(row)
     if d<gap(r['net'])+.025:errors.append(row)
   for j in trees['F.Cu'].query(tb.buffer(.8),predicate='intersects'):
    r=rec['F.Cu'][int(j)]
    if L.norm(r['net'])=='/LOGIC_GND':continue
    if r['kind']=='track':t=r['source'];d=axis.distance(LineString([t['a'],t['b']]))-.1-t['w']/2
    elif r['kind']=='via':v=r['source'];d=axis.distance(Point(v['x'],v['y']))-.1-v['d']/2
    else:d=axis.distance(r['shape'])-.1
    row={'kind':'track_to_'+r['kind'],'layer':'F.Cu','foreign_UUID':r['uuid'],'net':r['net'],'true_gap_mm':d,'required_native_mm':gap(r['net']),'required_planner_mm':gap(r['net'])+.025};checks.append(row)
    if d<gap(r['net'])+.025:errors.append(row)
   si=int(st.nearest(pt));hi=int(ht.nearest(pt));vi=int(vt.nearest(pt));guard={'all_SMD_guarded_mm':pt.distance(smd[si][1])-.105,'nearest_SMD_UUID':smd[si][0]['uuid'],'all_hole_guarded_mm':pt.distance(holes[hi][2])-.105,'nearest_hole_UUID':holes[hi][0],'ordinary_existing_via_pitch_mm':pt.distance(vps[vi]),'nearest_existing_via_UUID':h['vias'][vi]['uuid'],'new_nominee_via_pitch_mm':min([math.dist(xy,[v['x'],v['y']])for v in vias],default=None)}
   if guard['all_SMD_guarded_mm']<.275 or guard['all_hole_guarded_mm']<.275 or guard['ordinary_existing_via_pitch_mm']<.815 or(guard['new_nominee_via_pitch_mm']is not None and guard['new_nominee_via_pitch_mm']<.815):errors.append({'kind':'ordinary_hole_SMD_pitch','guards':guard})
   for j in ht.query(tb.buffer(.285),predicate='intersects'):
    uid,n,sh=holes[int(j)]
    if L.norm(n)!='/LOGIC_GND'and axis.distance(sh)-.105<.275:errors.append({'kind':'track_foreign_hole','UUID':uid,'guarded_gap_mm':axis.distance(sh)-.105})
   for obj,body,kind,layers in((p,tb,'track',['F.Cu']),(p,vb,'via',K.LAYERS)):
    if not outline.covers(body):errors.append({'kind':kind+'_edge'})
    for rule in h['rule_areas']:
     if rule.get('no_vias'if kind=='via'else'no_tracks')and set(layers)&set(rule['layers'])and any(body.distance(s)<.025 for s in L.poly(rule['outline'])):errors.append({'kind':kind+'_rule_area','UUID':rule['uuid']})
    for rule in reserved['keepouts']:
     if '/LOGIC_GND'not in exempt.get(rule['name'],set())and set(layers)&set(rule['layers'])and any(body.distance(s)<.025 for s in L.poly(rule['outline'])):errors.append({'kind':kind+'_frozen_reservation','name':rule['name']})
   hd=literal(Z.bounded_buffer(pt,.10000002));existing=[holes[int(i)][2]for i in ht.query(tb,predicate='intersects')];actual=tb.difference(unary_union([hd,*existing]));rg=actual.difference(refs['F.Cu']);ann=vb.difference(hd);annareas={l:sum(ann.intersection(r['shape']).area for r in root if r['layer']==l and r['kind']=='fill'and r['shape'].intersects(ann))for l in K.LAYERS};sourcefinite=any(x>0 for x in annareas.values())
   if not sourcefinite:errors.append({'kind':'no_finite_actual_source_root_fill_annulus'})
   if not rg.is_empty:errors.append({'kind':'actual_drilled_new_track_fullbody_source_reference','gap_mm2':rg.area,'gap_is_empty':False})
   for layer in K.LAYERS:
    for j in filltrees[layer].query(vb.buffer(.9),predicate='intersects'):
     r=fills[layer][int(j)]
     if L.norm(r['net'])=='/LOGIC_GND':continue
     if pt.distance(r['shape'])-.25<gap(r['net'])+.025:cuts.append({'kind':'current_filled_via_antipad','zone_UUID':r['uuid'],'layer':layer,'net':r['net'],'record':r['contour'],'normal_required_Cu_gap_mm':gap(r['net'])+.025,'original_record_WKB_sha256':hashlib.sha256(r['shape'].wkb).hexdigest()})
   for z in q:
    if L.norm(z['net'])!='/LOGIC_GND'and vb.distance(z['shape'])<max(float(z['clearance_mm']),gap(z['net']))+.025:cuts.append({'kind':'owned_role_via_antipad','zone_UUID':z['uuid'],'layer':z['layer'],'net':z['net'],'physical_WKB_sha256':hashlib.sha256(z['shape'].wkb).hexdigest(),'intended_WKB_sha256':hashlib.sha256(z['zone_outline_shape'].wkb).hexdigest()})
   row={'outward_offset_mm':off,'via_xy_mm':xy,'error_count':len(errors),'errors':errors,'true_discrete_check_count':len(checks),'ordinary_guards':guard,'actual_root_fill_annulus_mm2_by_layer':annareas,'actual_drilled_track_body_reference_gap_mm2':rg.area,'actual_drilled_track_body_reference_gap_is_empty':rg.is_empty,'foreign_normal_antipad_obligations':cuts};variants.append(row)
   if not errors:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'CM51-R274-via:'+p['uuid']));v={'uuid':uid,'net':'/LOGIC_GND','x':xy[0],'y':xy[1],'d':.5,'drill':.2,'flashed':K.LAYERS};t={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM51-R274-stub:'+p['uuid'])),'net':'/LOGIC_GND','layer':'F.Cu','w':.2,'a':[p['x'],p['y']],'b':xy};row['via']=v;row['track']=t;accepted.append({'ref':p['ref'],'pin':p['num'],'pad_UUID':p['uuid'],**row});tracks.append(t);vias.append(v);break
  results.append({'ref':p['ref'],'pin':p['num'],'actual_pad_UUID':p['uuid'],'pose_mm':[p['x'],p['y']],'variants':variants,'accepted':not variants[-1]['errors']});put(O/'finite-matrix-progress.json',results);print('R274_PAD',p['ref'],p['num'],len(variants),len(variants[-1]['errors']),len(accepted),flush=True)
 put(O/'receipt.json',{'verdict':'CM51_ALL_ORDINARY_FULLWIDTH_SOURCE_ANNULUS_NOMINEES_PENDING_CURRENT_CONSTRUCTION_AND_FULL_PROOF'if len(accepted)==51 else'CM51_PARTIAL_FINITE_NOMINATION_NO_FULL_RETURN_CREDIT','bound_model_sha256':sha(mp),'actual_drilled_groups_sha256':sha(gp),'native_source_board_sha256':sha(sr),'actual_pad_count':51,'accepted_count':len(accepted),'unaccepted_count':51-len(accepted),'matrix_file':'finite-matrix-progress.json','accepted':accepted,'generated_zone_or_native_filled_cuts_executed':False,'original_native_discrete_planes_rules_poses_untouched':True,'every_pad_individually_bound_no_equal_share_current_credit':True,'signed_CM_return_A':3.5593046439628484,'full_signed_LG_source_proof_drop_capacity_current_native_fault':'OPEN','inherited_CORE_body_and_R7_extra_planner_FAIL_retained':True,'native_jobs':0,'board_written':False,'adopted':False,'script_sha256':sha(__file__)})
 (O/'partial-only-nominated-discrete.pkl').write_bytes(pickle.dumps({'tracks':tracks,'vias':vias,'removed_original_track_UUIDs':[]},protocol=5));print('R274_COMPLETE',len(accepted),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
