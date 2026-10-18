"""Process-gated C1028.1 VIPPO option; registry and native board untouched."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math,csv,io
H=Path(__file__).resolve().parent;ROOT=H.parent
for p in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
OUT=H/'FPGA-CDONE-C1028-1-only-new-explicit-VIPPO-process-controlled-IO3-nominee-r43'
IO='/IO_3V3';NET='/fpga_core/FPGA_CDONE';UID='0f88a8b6-67a2-4f38-b7cf-6b33a89cf99e';STUB='75d7c648-ecac-4737-91c0-d51a6e01d011'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def pieces(s):return [q for x in s.geoms for q in pieces(x)]if hasattr(s,'geoms')else[s]if not s.is_empty else[]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();wp=H/'FPGA-CDONE-authorized-IO3-barrel-real-source-integer-pose-profile-and-wide-ROI-r38/receipt.json';wr=json.loads(wp.read_bytes());wf=Path(wr['cache_file']);assert sha(wf)==wr['cache_SHA256'];wide=pickle.loads(wf.read_bytes());local=wide['wide_current'];prior=wide['prior'];c=prior['context'];full=c['full_before'];cp=H/'FPGA-CDONE-exact-IO3-barrel-controlled-move-ordinary-escape-screen-r40/receipt.json';cr=json.loads(cp.read_bytes());cf=Path(cr['cache_file']);assert sha(cf)==cr['cache_SHA256'];signalctx=pickle.loads(cf.read_bytes());sat=[round(x,6)for x in signalctx['trials'][0]['ordinary_new_SG_at']];rr=H/'FPGA-CDONE-own-T1-native-ground-dogbone-and-ordinary-offpad-port-screen-r27/receipt.json';rs=json.loads(rr.read_bytes());rd=pickle.loads(Path(rs['cache_file']).read_bytes());circle=rd['actual_FPGA_circle_pad_math'];pad=next(p for p in local['pads']if p['ref']=='C1028'and str(p['num'])=='1');ps=unary_union(K.L.poly(pad['layers']['B.Cu']));base={**local,'vias':[v for v in local['vias']if v['uuid']!=UID],'tracks':[t for t in local['tracks']if t['uuid']!=STUB]};rec,trees=K.F.build(base);dom=full['domains_normalized'];gap=lambda net:.175 if dom[K.L.norm(net)]==dom[IO]else .625
 def obstacle(q,r):
  if q['kind']=='via':v=q['source'];return K.Z.bounded_disk(v,v['d']/2+r)
  if q['kind']=='track':t=q['source'];return K.Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+r)
  if q['kind']=='pad'and q['uuid']in circle:z=circle[q['uuid']];return K.Z.bounded_disk({'x':z['at'][0],'y':z['at'][1]},z['radius']+r)
  return K.Z.bounded_buffer(q['shape'],r+(.005 if q['kind']=='pad'else 0))
 region=ps.buffer(-.155004);initial=region;geometryloss=[]
 for ly,rows in rec.items():
  for q in rows:
   if K.L.norm(q['net'])==IO:continue
   cut=obstacle(q,.3+gap(q['net']));lost=region.intersection(cut)
   if not lost.is_empty:geometryloss.append({'kind':'foreign_Cu','UUID':q['uuid'],'layer':ly,'net':q['net'],'removed':info(lost)})
   region=region.difference(cut)
 region=region.difference(K.Z.bounded_disk({'x':sat[0],'y':sat[1]},.725))
 for p in local['pads']:
  if p['uuid']==pad['uuid']:continue
  if p['smd']:
   for ly,rs in p['layers'].items():
    if ly not in('F.Cu','B.Cu'):continue
    for s in K.L.poly(rs):
     z=circle.get(p['uuid']);cut=K.Z.bounded_disk({'x':z['at'][0],'y':z['at'][1]},z['radius']+.425)if z else K.Z.bounded_buffer(s,.43);region=region.difference(cut)
  for s in K.L.poly(p.get('hole')or[]):region=region.difference(K.Z.bounded_buffer(s,.425))
 for v in base['vias']:region=region.difference(K.Z.bounded_disk(v,v['drill']/2+.425))
 geometry_region=region;support=[]
 for t in base['tracks']:
  b=K.L.body(t)
  if b.disjoint(initial.buffer(.8)):continue
  s=b.intersection(c['source_refs'][K.MAP[t['layer']]])
  if not s.is_empty:support.append(s)
 protected=unary_union(support);region=region.difference(K.Z.bounded_buffer(protected,.550004));region=region.intersection(wide['IO3_source_fills']['In2.Cu'].buffer(-.300004));reserve,exempt=K.A.reservations()
 for r in full['rule_areas']:
  if r.get('no_vias'):
   for s in K.L.poly(r['outline']):region=region.difference(K.Z.bounded_buffer(s,.325))
 for r in reserve['keepouts']:
  if IO not in exempt.get(r['name'],set()):
   for s in K.L.poly(r['outline']):region=region.difference(K.Z.bounded_buffer(s,.325))
 trials=[]
 for s in pieces(region):
  if s.geom_type!='Polygon':continue
  p=s.representative_point();at=[round(x,6)for x in p.coords[0]];hole=K.Z.bounded_disk({'x':at[0],'y':at[1]},.15);ann=Point(at).buffer(.3,quad_segs=128).difference(Point(at).buffer(.15,quad_segs=128));src=ann.intersection(wide['IO3_source_fills']['In2.Cu']);contact=ann.intersection(ps);assert ps.buffer(-.005).covers(hole)and src.area>0 and contact.area>0;trials.append({'controlled_same_UUID_IO3_at':at,'native_IO3_diameter_drill_mm':[.6,.3],'new_ordinary_signal_at':sat,'signal_to_moved_IO3_mm':math.dist(at,sat),'ground_return_for_signal':rd['own_T1_return']['return_via']['uuid'],'finite_own_C1028_1_annular_pad_contact':info(contact),'finite_true_before_own_In2_SOURCE_annulus':info(src),'drill_fully_contained_inside_own_pad_with_5um_export_bound':True,'new_intentional_VIPPO_pad':{'ref':'C1028','pin':'1','UUID':pad['uuid'],'layer':'B.Cu'},'retire_only_redundant_native_IO3_B_stub':STUB,'additional_power_stem_tracks':0,'all_native_after_source_graph_oldrefs_contacts_current_thermal_PDN_SI':'OPEN'})
 registry=Path('Z:/pcb-runs/fab-check/assembly/vippo.csv');regraw=registry.read_bytes();rows=list(csv.DictReader(io.StringIO(regraw.decode('utf-8-sig'))));assert len(rows)==291 and not any(x['via_uuid']==UID for x in rows);put('exact-new-VIPPO-process-location-NOMINEE-not-registered.json',{'existing_registry_SHA256':sha(registry),'existing_locations':291,'original_IO3_UUID_already_registered':False,'proposed_total_if_explicitly_qualified':292 if trials else 291,'nominee_locations':trials,'required_treatment':'VIPPO: IPC-4761 Type VII resin fill, planarize, copper cap (both sides)','existing_registry_modified':False,'own_land_exception_authority':'OPEN exact location-specific process qualification; never an ordinary-hole waiver'});put('raw-foreign-current-Cu-subtractions.json',geometryloss);put('source-protected-new-process-geometry-nominee-sites.json',trials);cache=OUT/'explicit-new-C1028-VIPPO-only-process-gated-source-geometry-context.pkl';cache.write_bytes(pickle.dumps({'wide':wide,'signal_scope':signalctx,'pad':pad,'initial':initial,'geometry_region':geometry_region,'SOURCE_protected_region':region,'trials':trials},protocol=5));result={'verdict':'EXPLICIT_NEW_C1028_VIPPO_PROCESS_GATED_CONTROLLED_IO3_SOURCE_GEOMETRY_NOMINEE_POSITIVE'if trials else'NEW_C1028_VIPPO_PROCESS_GATED_CONTROLLED_IO3_BOUNDED_SCREEN_NO_POSITIVE','initial_hole_contained_own_B_land_region':info(initial),'foreign_Cu_and_all_other_hole_guarded_region':info(geometry_region),'untouched_old_SOURCE_body_protected_source_In2_region':info(region),'nominee_sites':len(trials),'existing_registry_locations':291,'proposed_added_process_locations':1 if trials else 0,'native_board_or_VIPPO_registry_writes':0,'adopted':False,'source_and_process_current_thermal_SI_native_AFTER_qualification':'OPEN','cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'inputs':{str(p.resolve()):sha(p)for p in(wp,wf,cp,cf,registry)},'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','foreign_Cu_and_all_other_hole_guarded_region','untouched_old_SOURCE_body_protected_source_In2_region','nominee_sites','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
