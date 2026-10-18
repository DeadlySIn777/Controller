"""Construct source-seeded new reference roles for the preserved-branch nominee.

This writes only a proposed sparse packet. All actual old-fill cuts, every
drilled contact/reference/clearance/current and native check remain mandatory.
"""
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'U10003-two-signal-port-source-seeded-ground-reference-nomination-r172';FG='/motherboard_motors/FIELD_GND';FAULT='/motherboard_do/DOA_FLT_N_FIELD'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def polys(s):return[p for p in([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if p.geom_type=='Polygon'and not p.is_empty]
def main():
 assert not OUT.exists();OUT.mkdir()
 mp=H/'U10003-sparse-current-ground-fault-construction-r153/model.pkl';assert sha(mp)=='2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8';g,h,b,z,full=pickle.loads(mp.read_bytes())
 packet=H/'U10003-additional-signal-port-old-In3-preserved-nomination-r171';assert sha(packet/'receipt.json')=='88fa4c3693b651a87814a691e790c70559fbd700c222d66f2e4bce7a72e02634';d=pickle.loads((packet/'proposed-sparse-delta.pkl').read_bytes());sig=d['new_ordinary_signal_via'];delete={t['uuid']for t in d['delete_tracks']};assert len(delete)==2
 central=next(v for v in h['vias']if C.norm(v['net'])==FG and(v['x'],v['y'])==(216.04,142.95));raw=central['net']
 ret={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'U10003-rooted-paired-return-A-r172')),'net':raw,'x':219.17568,'y':142.190789,'d':.5,'drill':.2,'span':list(h['copper_layers']),'flashed':list(h['copper_layers']),'prospective_not_native':True,'mask_provenance':'HOST_NEW_ORDINARY_RETURN_ONLY_FRESH_NATIVE_ALL6_AND_ANNULI_REQUIRED'}
 hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in delete]+d['tracks'],'vias':h['vias']+[sig,ret]};records,trees=F.build({**hard,'zones':[]})
 replace={'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}
 # Withdraw those exact old proposed ground records before deriving roots;
 # their old shapes are never used as phantom seed copper.
 sourceview={**full,'zones':[q for q in full['zones']if q['uuid']not in replace]};_,groups=K.physical(sourceview,FG,K.hole_context(sourceview));root=K.root(groups,'J11003','2')
 oldref={l:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==l])for l in ('In1.Cu','In4.Cu')}
 point=lambda v:Point(v['x'],v['y']);ann=lambda v:point(v).buffer(v['d']/2,quad_segs=256).difference(point(v).buffer(v['drill']/2,quad_segs=256))
 assert oldref['In1.Cu'].intersection(ann(central)).area>0
 oldsignal=next(v for v in h['vias']if v['uuid']=='2938cbdd-1d38-4238-9455-504b30f06e5e');sigports={oldsignal['uuid']:oldsignal,sig['uuid']:sig};groundports={central['uuid']:central,ret['uuid']:ret}
 bodies=unary_union([C.body(t)for t in d['tracks']]+[C.body(t)for t in h['tracks']if C.norm(t['net'])==FG and t.get('prospective_not_native')and t['layer']=='B.Cu'])
 desired=bodies.buffer(.20,quad_segs=128).union(LineString([point(central),point(ret)]).buffer(.25,quad_segs=128))
 for v in sigports.values():desired=desired.union(point(v).buffer(.7,quad_segs=128))
 for v in groundports.values():desired=desired.union(point(v).buffer(.35,quad_segs=128))
 win=desired.envelope.buffer(1.);rows=[];zones=[];in1_return_rooted=False
 for layer in ('In1.Cu','In4.Cu'):
  common=[];physical_only=[];ledger=[]
  def add(sh,kind,uid,own=False):
   if not sh.intersects(desired):return
   (physical_only if own else common).append(sh);ledger.append({'kind':kind,'UUID':uid,'physical_only_own_signal_or_ground_port':own,'WKB_sha256':hashlib.sha256(sh.wkb).hexdigest()})
  for j in trees[layer].query(win,predicate='intersects'):
   q=records[layer][int(j)];other=C.norm(q['net'])
   if other==FG:continue
   gap=(.15 if h['domains_normalized'][other]==h['domains_normalized'][FG]else.6)+.025
   add(N.bounded_buffer(q['shape'].intersection(win),gap),'ACTUAL_FOREIGN_REFERENCE_LAYER_CU',q['uuid'],q['uuid']in sigports)
  for q in z:
   other=C.norm(q['net'])
   if q['layer']!=layer or other==FG:continue
   gap=max(float(q['clearance_mm']),.15 if h['domains_normalized'][other]==h['domains_normalized'][FG]else.6)+.025
   add(N.bounded_buffer(q['shape'].intersection(win),gap),'CURRENT_OTHER_OWNED_POSITIVE',q['uuid'])
  for p in hard['pads']:
   for sh in C.poly(p.get('hole')or[]):
    if sh.intersects(win):add(N.bounded_buffer(sh,.275),'EVERY_ACTUAL_PAD_HOLE',p['uuid'])
  for v in hard['vias']:
   if not win.covers(point(v)):continue
   if C.norm(v['net'])==FG:
    add(N.bounded_disk(v,v['drill']/2),'ACTUAL_OWN_GROUND_PHYSICAL_BORE',v['uuid'],v['uuid']in groundports)
   else:add(N.bounded_disk(v,v['drill']/2+.275),'EVERY_OTHER_ACTUAL_VIA_DRILL',v['uuid'],v['uuid']in sigports)
  for a in h['rule_areas']:
   if a.get('no_zones')and layer in a['layers']:
    for sh in C.poly(a['outline']):
     if sh.intersects(win):add(N.bounded_buffer(sh,.025),'ACTUAL_NATIVE_NO_ZONES',a['uuid'])
  for q in full['zones']:
   other=C.norm(q['net'])
   if other==FG or h['domains_normalized'][other]==h['domains_normalized'][FG]:continue
   for sh in C.poly(q['fills'].get(layer,[])):
    if sh.intersects(win):add(N.bounded_buffer(sh.intersection(win),max(.6,float(q['clearance_mm']))+.025),'OTHER_DOMAIN_ACTUAL_NATIVE_FILLED_CU',q['uuid'])
  intended=set_precision(desired.difference(unary_union(common)),1e-6)
  physical=set_precision(intended.difference(unary_union(physical_only)),1e-6)
  seed=oldref[layer].union(ann(central))
  if layer=='In4.Cu'and in1_return_rooted:seed=seed.union(ann(ret))
  keep=[p for p in polys(physical)if p.intersection(seed).area>0 and not p.buffer(-.075).is_empty];physical=unary_union(keep)
  intended=unary_union([p for p in polys(intended)if any(p.intersection(q).area>0 for q in keep)])
  if layer=='In1.Cu':in1_return_rooted=physical.intersection(ann(ret)).area>0
  uid='9fe010df-73cf-5bfb-9f7a-bd227b701c3e'if layer=='In1.Cu'else'ee0efe05-1705-587c-ac86-49b1a7885ef9'
  q={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':intended,'priority':126,'clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3};zones.append(q)
  body=unary_union([C.body(t)for t in d['tracks']]);rawgap=body.difference(oldref[layer].union(physical));portcut=unary_union([N.bounded_disk(v,max(v['d']/2+.175,v['drill']/2+.275))for v in sigports.values()]);outside=rawgap.difference(portcut)
  rows.append({'layer':layer,'UUID':uid,'physical_area_mm2':physical.area,'intended_area_mm2':intended.area,'physical_components':len(keep),'new_return_A_real_annular_overlap_mm2':physical.intersection(ann(ret)).area,'existing_rooted_central_return_annular_overlap_mm2':physical.intersection(ann(central)).area,'new_signal_fullbody_raw_reference_gap_mm2':rawgap.area,'outside_exact_signal_port_antipads_gap_mm2':outside.area,'outside_gap_empty':outside.is_empty,'own_signal_port_void_credit_and_every_true_geometry_source_current_native_gate':'OPEN; no automatic credit'})
  put(OUT/(layer+'-actual-cut-authorities.json'),ledger);(OUT/(layer+'-physical.wkb')).write_bytes(physical.wkb);(OUT/(layer+'-intended.wkb')).write_bytes(intended.wkb)
 delta={**d,'new_ordinary_ground_return_via':ret,'replace_exact_two_unadopted_ground_roles':zones,'ground_roles_only_bound_local_negative_withdrawal_UUIDs':d['ground_owned_local_negative_withdrawal_UUIDs']};(OUT/'proposed-complete-sparse-delta.pkl').write_bytes(pickle.dumps(delta,protocol=5))
 receipt={'verdict':'PROPOSED_TWO_SIGNAL_PORT_REAL_SOURCE_SEEDED_REFERENCE_ROLES_ALL_PHYSICAL_NATIVE_CURRENT_GATES_OPEN','base_model_sha256':sha(mp),'signal_nomination_receipt_sha256':sha(packet/'receipt.json'),'rows':rows,'same_old_native_barrel_B_In3_geometry_untouched':True,'new_signal_and_return_A_diameter_drill_mm':[.5,.2],'proposed_sparse_delta_sha256':sha(OUT/'proposed-complete-sparse-delta.pkl'),'old_proposed_ground_roles_withdrawn_before_source_seed':True,'actual_original_source_seed_central_In1_overlap_mm2':oldref['In1.Cu'].intersection(ann(central)).area,'physical_geometry_changed':False,'every_old_contact_reference_signed_current_and_native_profile_gate':'OPEN','native_jobs':0,'adopted':False,'manufacturing_ready':False};put(OUT/'receipt.json',receipt);print(json.dumps({'receipt_sha256':sha(OUT/'receipt.json'),'rows':rows}),flush=True)
if __name__=='__main__':main()
