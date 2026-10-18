"""Literal old-hole authority from real rooted native outlines, with all other cuts."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import DIC_source_supported_own_apertures_r200 as OS
OUT=H/'U10003-actual-native-old-signal-own-aperture-qualification-r166'
FG='/motherboard_motors/FIELD_GND';FAULT='/motherboard_do/DOA_FLT_N_FIELD'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def main():
 assert not OUT.exists();OUT.mkdir()
 base=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';mp=H/'U10003-sparse-current-ground-fault-construction-r153/model.pkl'
 assert sha(base)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'and sha(mp)=='2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8'
 g,h0,b0,q0,before=pickle.loads(base.read_bytes());ng,h,b,q,after=pickle.loads(mp.read_bytes());assert g==ng
 parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';inv=OS.C.inventory(parent.read_bytes())
 print('R166_DRILLED_FG_SOURCE_GROUPS',flush=True)
 _,oldgroups=K.physical(before,FG,K.hole_context(before));_,newgroups=K.physical(after,FG,K.hole_context(after));oldroot=K.root(oldgroups,'J11003','2');newroot=K.root(newgroups,'J11003','2')
 records,trees=F.build({**h,'zones':[]});zoneheader={z['uuid']:z for z in before['zones']};oldvias={v['uuid']:v for v in h0['vias']};vias={v['uuid']:v for v in h['vias']}
 frozen=json.loads((H/'U10003-unqualified-physical-fault-detour-r130/receipt.json').read_bytes())['repair']['existing_native_barrels'];assert {v['uuid']for v in frozen}=={'2938cbdd-1d38-4238-9455-504b30f06e5e','1dfba07d-0355-46e7-abf9-ae2e8d1c9843'}
 oldids={t['uuid']for t in h0['tracks']};newbody=unary_union([K.A.shape({'kind':'segment',**t})for t in h['tracks']if t['uuid']not in oldids and L.norm(t['net'])==FAULT]);rows=[];credits={l:[]for l in ('In1.Cu','In4.Cu')}
 for v in frozen:
  uid=v['uuid'];assert oldvias[uid]==vias[uid]and(vias[uid]['x'],vias[uid]['y'],vias[uid]['d'],vias[uid]['drill'])==(v['x'],v['y'],.6,.3)
  rawdisk=Point(v['x'],v['y']).buffer(.575,quad_segs=256)
  for plane in ('In1.Cu','In4.Cu'):
   nativeids={r['uuid']for r in oldroot if r['kind']=='fill'and r['layer']==plane and r['shape'].distance(rawdisk)<.8};owners=[];ownerledger=[]
   for zid in sorted(nativeids):
    if zid not in inv[3]:continue
    ch=inv[3][zid]
    if OS.C.pcbtext.chunk_kind(ch)!='zone':continue
    plain,spans=OS.CACHE.strip_cache(ch);ast=OS.Q.parse(plain.decode());raw=OS.Q.atom(ast,'net');assert L.norm(raw)==FG
    ls=OS.Q.atom(ast,'layer');layers=[ls]if ls else OS.Q.child(ast,'layers')[1:]
    if plane not in layers:continue
    rings=[[(float(p[1]),float(p[2]))for p in OS.Q.child(pp,'pts')[1:]]for pp in OS.Q.children(ast,'polygon')];assert rings
    sh=Polygon(rings[0],rings[1:]);assert sh.is_valid
    if not sh.intersects(rawdisk):continue
    local=float(zoneheader[zid]['clearance_mm']);radius=.3+max(.15,local)+.025
    assert radius<=.575000000001
    owners.append(sh.intersection(Point(v['x'],v['y']).buffer(radius,quad_segs=256)));ownerledger.append({'actual_before_rooted_native_zone_UUID':zid,'native_chunk_sha256':hashlib.sha256(ch).hexdigest(),'uncached_native_definition_sha256':hashlib.sha256(plain).hexdigest(),'actual_local_clearance_mm':local,'derived_existing_own_aperture_radius_mm':radius,'no_native_outline_or_other_hole_removed':True})
   support=unary_union(owners).intersection(rawdisk);cuts=[];cutledger=[]
   def add(cut,kind,identifier,**more):
    if not cut.intersects(support):return
    cuts.append(cut);cutledger.append({'kind':kind,'UUID':identifier,'cut_WKB_sha256':hashlib.sha256(cut.wkb).hexdigest(),**more})
   if not support.is_empty:
    local=max(r['actual_local_clearance_mm']for r in ownerledger)
    for i in trees[plane].query(rawdisk.buffer(1),predicate='intersects'):
     r=records[plane][int(i)];other=L.norm(r['net'])
     if r['uuid']==uid or other==FG:continue
     gap=max(local,.15 if h['domains_normalized'][other]==h['domains_normalized'][FG]else.6)+.025
     add(Z.bounded_buffer(r['shape'],gap),'EVERY_OTHER_ACTUAL_REFERENCE_LAYER_CU',r['uuid'],raw_net=r['net'],clearance_mm=gap)
    for other in h['vias']:
     if other['uuid']!=uid:add(Z.bounded_disk(other,other['drill']/2+.005),'EVERY_OTHER_ACTUAL_DRILL',other['uuid'])
    for p in h['pads']:
     for hole in L.poly(p.get('hole')or[]):add(Z.bounded_buffer(hole,.005),'EVERY_OTHER_ACTUAL_PAD_HOLE',p['uuid'])
    for a in h['rule_areas']:
     if plane in a['layers']and a.get('no_zones'):
      for sh in L.poly(a['outline']):add(Z.bounded_buffer(sh,.025),'ACTUAL_NATIVE_NO_ZONES',a['uuid'])
    for zc in after['zones']:
     other=L.norm(zc['net'])
     if other==FG:continue
     for sh in L.poly(zc['fills'].get(plane,[])):
      if sh.distance(rawdisk)>1:continue
      gap=max(local,float(zc['clearance_mm']),.15 if h['domains_normalized'][other]==h['domains_normalized'][FG]else.6)+.025
      add(Z.bounded_buffer(sh,gap),'CURRENT_FOREIGN_ACTUAL_FILLED_COPPER',zc['uuid'],raw_net=zc['net'],clearance_mm=gap)
   allowed=support.difference(unary_union(cuts));credits[plane].append(allowed)
   (OUT/(uid+'-'+plane+'-allowed-own-hole.wkb')).write_bytes(allowed.wkb)
   rows.append({'signal_UUID':uid,'actual_reference_plane':plane,'old_actual_source_native_outline_authorities':ownerledger,'every_other_actual_boundary_cut_ledger':cutledger,'qualified_own_aperture_area_mm2':allowed.area,'other_void_denied_area_mm2':rawdisk.difference(allowed).area,'exact_before_native_flashes':v['flashed'],'return_transition_geometry_current_and_native_qualification':'OPEN'})
  print('R166_PORT',uid,flush=True)
 bodyrows=[]
 for plane in credits:
  actualref=unary_union([r['shape']for r in newroot if r['kind']=='fill'and r['layer']==plane]);credit=unary_union(credits[plane]);rawgap=newbody.difference(actualref);remaining=rawgap.difference(credit)
  (OUT/(plane+'-remaining-reference-gap.wkb')).write_bytes(remaining.wkb)
  bodyrows.append({'plane':plane,'raw_fullbody_gap_mm2':rawgap.area,'raw_fullbody_gap_empty':rawgap.is_empty,'exact_own_native_outline_supported_credit_mm2':rawgap.intersection(credit).area,'remaining_unqualified_gap_mm2':remaining.area,'remaining_unqualified_gap_empty':remaining.is_empty})
 result={'verdict':'LITERAL_OLD_NATIVE_OWN_APERTURE_CLASSIFICATION_ONLY_NO_RETURN_TRANSITION_PROMOTION','base_model_sha256':sha(base),'candidate_model_sha256':sha(mp),'native_parent_sha256':sha(parent),'rows':rows,'new_fault_body_rows':bodyrows,'raw_failed_reference_rows_preserved':True,'no_radius_expansion_area_waiver_or_source_shadow':True,'physical_or_native_geometry_changed':False,'actual_paired_source_returns_and_native_full_fill_DRC_current':'OPEN','native_jobs':0,'adopted':False,'manufacturing_ready':False}
 put(OUT/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(OUT/'receipt.json'),'rows':[{'signal_UUID':r['signal_UUID'],'plane':r['actual_reference_plane'],'owner_count':len(r['old_actual_source_native_outline_authorities']),'qualified_area_mm2':r['qualified_own_aperture_area_mm2']}for r in rows],'body_rows':bodyrows}),flush=True)
if __name__=='__main__':main()
