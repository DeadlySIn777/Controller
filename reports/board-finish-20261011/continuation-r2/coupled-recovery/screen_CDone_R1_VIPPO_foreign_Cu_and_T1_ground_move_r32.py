"""Bound ordinary R1 cell and measure exact controlled VIPPO/return option."""
from pathlib import Path
import sys,pickle,json,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for p in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
OUT=H/'FPGA-CDONE-R1-cell-ordinary-bound-and-explicit-VIPPO-T1-controlled-pose-screen-r32'
LG='/LOGIC_GND';NET='/fpga_core/FPGA_CDONE';RET='b1e1485b-fbb0-48dd-a58a-2262fbd55ce3'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def pieces(s):return [q for x in s.geoms for q in pieces(x)]if hasattr(s,'geoms')else[s]if not s.is_empty else[]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();rp=H/'FPGA-CDONE-continuous-ordinary-port-and-curved-F-source-search-r31/receipt.json';r=json.loads(rp.read_bytes());cf=Path(r['cache_file']);assert sha(cf)==r['cache_SHA256'];d=pickle.loads(cf.read_bytes());c=d['context'];local=c['local_current'];full=c['full_before'];rr=H/'FPGA-CDONE-own-T1-native-ground-dogbone-and-ordinary-offpad-port-screen-r27/receipt.json';cr=json.loads(rr.read_bytes());orig=pickle.loads(Path(cr['cache_file']).read_bytes());circle=orig['actual_FPGA_circle_pad_math'];producer=c['producer'];at=[producer['x'],producer['y']];ret=next(v for v in local['vias']if v['uuid']==RET);own=orig['own_T1_return'];pad=own['ground_pad_UUID'];tp=next(p for p in local['pads']if p['uuid']==pad);tpat=[tp['x'],tp['y']];rec,trees=K.F.build(local);dom=full['domains_normalized'];gap=lambda n:.175 if dom[K.L.norm(n)]==dom[NET]else .625
 def obstacle(row,extra):
  if row['kind']=='via':v=row['source'];return K.Z.bounded_disk(v,v['d']/2+extra)
  if row['kind']=='track':t=row['source'];return K.Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+extra)
  if row['kind']=='pad'and row['uuid']in circle:z=circle[row['uuid']];return K.Z.bounded_disk({'x':z['at'][0],'y':z['at'][1]},z['radius']+extra)
  return K.Z.bounded_buffer(row['shape'],extra+(.005 if row['kind']=='pad'else 0))
 def via_checks(point,net,skip=(),ownland=None):
  center=Point(point);err=[];pairs=[]
  for ly,rows in rec.items():
   for q in rows:
    if q['uuid']in skip or K.L.norm(q['net'])==net:continue
    if q['kind']=='via':v=q['source'];dist=center.distance(Point(v['x'],v['y']))-.25-v['d']/2
    elif q['kind']=='track':t=q['source'];dist=center.distance(LineString([t['a'],t['b']]))-.25-t['w']/2
    elif q['kind']=='pad'and q['uuid']in circle:z=circle[q['uuid']];dist=center.distance(Point(z['at']))-.25-z['radius']
    else:dist=center.distance(q['shape'])-.25-(.005 if q['kind']=='pad'else 0)
    req=gap(q['net']);row={'kind':'true_current_via_Cu','UUID':q['uuid'],'layer':ly,'net':q['net'],'gap_mm':dist,'required_mm':req};pairs.append(row)
    if dist<req:err.append(row)
  for p in local['pads']:
   if p['uuid']in skip:continue
   if p['smd']and p['uuid']!=ownland:
    for ly,rs in p['layers'].items():
     if ly not in('F.Cu','B.Cu'):continue
     for s in K.L.poly(rs):
      dist=center.distance(Point(circle[p['uuid']]['at']))-circle[p['uuid']]['radius']-.1 if p['uuid']in circle else center.distance(s)-.105
      if dist<.275:err.append({'kind':'SMD_hole','UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'layer':ly,'gap_mm':dist,'required_mm':.275})
   for s in K.L.poly(p.get('hole')or[]):
    if center.distance(s)-.1<.275:err.append({'kind':'old_pad_hole','UUID':p['uuid']})
  for v in local['vias']:
   if v['uuid']in skip:continue
   dist=math.dist(point,[v['x'],v['y']])-.1-v['drill']/2
   if dist<.275:err.append({'kind':'old_via_hole','UUID':v['uuid'],'gap_mm':dist,'required_mm':.275})
  return err,pairs
 # Full true-Cu producer F cell, independent of private-return envelope.
 region=d['F_component'];removed=[]
 for ly,rows in rec.items():
  for q in rows:
   if K.L.norm(q['net'])==NET:continue
   cut=obstacle(q,.25+gap(q['net']));lost=region.intersection(cut)
   if not lost.is_empty:removed.append({'kind':'via_Cu','UUID':q['uuid'],'layer':ly,'removed':info(lost)})
   region=region.difference(cut)
 before_own_land=region
 for p in local['pads']:
  if not p['smd']:continue
  for ly,rs in p['layers'].items():
   if ly not in('F.Cu','B.Cu'):continue
   for s in K.L.poly(rs):
    cut=K.Z.bounded_disk({'x':circle[p['uuid']]['at'][0],'y':circle[p['uuid']]['at'][1]},circle[p['uuid']]['radius']+.375)if p['uuid']in circle else K.Z.bounded_buffer(s,.38);lost=region.intersection(cut)
    if not lost.is_empty:removed.append({'kind':'all_SMD_ordinary_hole','UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'layer':ly,'removed':info(lost)})
    region=region.difference(cut)
 for v in local['vias']:region=region.difference(K.Z.bounded_disk(v,v['drill']/2+.375))
 original_err,_=via_checks(at,NET,ownland=producer['uuid']);after_ret_move_err,_=via_checks(at,NET,skip=(RET,),ownland=producer['uuid']);contained=Point(at).buffer(circle[producer['uuid']]['radius']-.1,quad_segs=128);contained_free=contained
 for ly,rows in rec.items():
  for q in rows:
   if K.L.norm(q['net'])!=NET:contained_free=contained_free.difference(obstacle(q,.25+gap(q['net'])))
 move_region=c['courtyard'].intersection(Point(at).buffer(1.2,quad_segs=256));skipstub=own['exact_owned_F_dogbone_track']['uuid']
 for ly,rows in rec.items():
  for q in rows:
   if q['uuid']in(RET,skipstub)or K.L.norm(q['net'])==LG:continue
   move_region=move_region.difference(obstacle(q,.25+gap(q['net'])))
 # The prospective SG itself is hard against relocated old ground via.
 move_region=move_region.difference(K.Z.bounded_disk({'x':at[0],'y':at[1]},.675))
 for p in local['pads']:
  if not p['smd']:continue
  for ly,rs in p['layers'].items():
   if ly not in('F.Cu','B.Cu'):continue
   for s in K.L.poly(rs):
    cut=K.Z.bounded_disk({'x':circle[p['uuid']]['at'][0],'y':circle[p['uuid']]['at'][1]},circle[p['uuid']]['radius']+.375)if p['uuid']in circle else K.Z.bounded_buffer(s,.38);move_region=move_region.difference(cut)
 for v in local['vias']:
  if v['uuid']!=RET:move_region=move_region.difference(K.Z.bounded_disk(v,v['drill']/2+.375))
 trials=[]
 for p in pieces(move_region):
  if p.geom_type!='Polygon':continue
  q=p.representative_point();target=[round(v,6)for v in q.coords[0]];err,_=via_checks(target,LG,skip=(RET,));axis=LineString([tpat,target]);body=K.Z.bounded_buffer(axis,.1)
  for row in rec['F.Cu']:
   if row['uuid']in(RET,skipstub)or K.L.norm(row['net'])==LG:continue
   if not body.disjoint(obstacle(row,gap(row['net']))):err.append({'kind':'new_owned_T1_ground_F_stub','UUID':row['uuid'],'net':row['net']})
  ann=Point(target).buffer(.25,quad_segs=128).difference(Point(target).buffer(.1,quad_segs=128));source={ly:ann.intersection(c['source_refs'][ly]).area for ly in('In1.Cu','In4.Cu')};trials.append({'retained_return_UUID':RET,'old_at':[ret['x'],ret['y']],'nominee_at':target,'source_annular_area_mm2':source,'same_part_T1_direct_ground_stub':{'a':tpat,'b':target,'w':.2},'SG_pair_distance':math.dist(at,target),'errors':err,'geometry_pass':not err,'requires_controlled_old_via_pose_and_one_owned_ground_stub_replay':True,'new_R1_VIPPO_process_location_required':True})
 ip=ROOT/'current-R753-all-native-zone-intents-read-only-r312/all-current-native-intended-zone-outlines-and-profiles.json';assert sha(ip)=='80452bcf08504313ac21195aba3d11ba11751bcd8943245c2404fb7c55e565c2';intents=json.loads(ip.read_bytes());near=[]
 for z in intents:
  for poly in K.L.poly(z['outline_mm_exact_native_IU_div_1e6']):
   if poly.intersects(c['courtyard']):near.append({k:z.get(k)for k in('UUID','raw_name','raw_net','layers','local_clearance_IU','priority','rule_area','no_tracks','no_vias')});break
 put('whole-R1-F-cell-ordinary-subtraction-ledger.json',removed);put('actual-centered-R1-VIPPO-foreign-failures.json',original_err);put('centered-R1-VIPPO-foreign-failures-excluding-only-T1-return-pose.json',after_ret_move_err);put('precisely-controlled-T1-ground-return-pose-trials.json',trials);put('current-native-zone-intents-overlapping-FPGA-courtyard.json',near)
 receipt={'verdict':'R1_PRODUCER_F_CELL_ORDINARY_EMPTY_CONTROLLED_RETURN_VIPPO_OPTION_SCREEN_ONLY','whole_F_cell_ordinary_region':info(region),'via_clear_region_before_own_SMD_drill':info(before_own_land),'hole_contained_R1_land_center_region_with_all_foreign_Cu':info(contained_free),'centered_R1_via_current_foreign_errors':len(original_err),'centered_R1_via_errors_excluding_only_retired_T1_return_pose':len(after_ret_move_err),'T1_return_continuous_discrete_geometry_move_region':info(move_region),'T1_return_move_trial_count':len(trials),'T1_return_move_geometry_positive_count':sum(t['geometry_pass']for t in trials),'overlapping_current_native_intents':len(near),'all_normal_antipad_old_SOURCE_body_ref_graph_contact_native_masks_thermal_current_SI_process_qualification':'OPEN','explicit_R1_VIPPO_own_land_and_controlled_T1_pose_authority':'PROSPECTIVE_REVIEW_NOMINEE_ONLY_NOT_ADOPTED','native_jobs':0,'adopted':False,'input_SHA256':{str(rp.resolve()):sha(rp),str(cf.resolve()):sha(cf),str(ip.resolve()):sha(ip)},'elapsed_seconds':time.monotonic()-st};put('receipt.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
