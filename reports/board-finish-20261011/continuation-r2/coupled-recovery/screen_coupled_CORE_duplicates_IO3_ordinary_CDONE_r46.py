"""Screen only the authorized duplicate CORE detour and ordinary IO3 escape."""
from pathlib import Path
import sys, json, pickle, hashlib, math, time
H=Path(__file__).resolve().parent; ROOT=H.parent
for p in (H,ROOT/'field-power',ROOT/'sbc-power'): sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import tri_route
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
OUT=H/'FPGA-CDONE-authorized-two-CORE-duplicate-detour-ordinary-IO3-screen-r46'
CORE='/mc_local_power/CORE_5V'; IO='/IO_3V3'; SG='/fpga_core/FPGA_CDONE'; LG='/LOGIC_GND'
WALL={'233cfa24-bc17-4dfa-9617-321c8db03618','b1e1f4cd-cfe9-421c-8c66-6662888515d5'}
IV='0f88a8b6-67a2-4f38-b7cf-6b33a89cf99e'; ISTUB='75d7c648-ecac-4737-91c0-d51a6e01d011'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x): (OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s): return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds) if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def pieces(s):
 if s.is_empty:return []
 return [q for p in s.geoms for q in pieces(p)] if hasattr(s,'geoms') else [s]
def loadreceipt(p):
 r=json.loads(p.read_bytes()); f=Path(r['cache_file']); assert sha(f)==r['cache_SHA256']; return r,f,pickle.loads(f.read_bytes())
def main():
 st=time.monotonic(); assert not OUT.exists(); OUT.mkdir(); pins={}
 def pin(p,expected=None):
  p=Path(p); value=sha(p); assert expected is None or value==expected; pins[str(p.resolve())]=value; return p
 wr=pin(H/'FPGA-CDONE-authorized-IO3-barrel-real-source-integer-pose-profile-and-wide-ROI-r38/receipt.json'); _,wf,wide=loadreceipt(wr);pin(wf)
 c=wide['prior']['context']; full=c['full_before']; local=wide['wide_current']; dom=full['domains_normalized']
 rp=pin(H/'FPGA-CDONE-exact-IO3-barrel-controlled-move-ordinary-escape-screen-r40/receipt.json');_,rf,old=loadreceipt(rp);pin(rf)
 sat=[154.798402,94.439904]; start=[155.29,94.877]
 rr=pin(H/'FPGA-CDONE-own-T1-native-ground-dogbone-and-ordinary-offpad-port-screen-r27/receipt.json');_,rrf,own=loadreceipt(rr);pin(rrf); circle=own['actual_FPGA_circle_pad_math']
 sp=pin(ROOT/'sbc-power/CM-alternate-pose-only-new-ground-blocker-and-original-CORE233-binding-r447/original-CORE233-actual-BEFORE-SOURCE-direct-native-contact-scope.json'); contact=json.loads(sp.read_bytes()); assert contact['SOURCE_before_layer_keys']==8306
 native=pin(c['current_native_source'],'7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'); nativechunks=K.C.inventory(native.read_bytes())[3]
 coretracks=[t for t in local['tracks'] if t['uuid'] in WALL]; assert len(coretracks)==2
 for t in coretracks:
  assert t['a']==[148.65,90.65] and t['b']==[154.65,96.65] and t['w']==1.25 and K.L.norm(t['net'])==CORE
  assert b'(locked yes)' in nativechunks[t['uuid']]
 base={**local,'tracks':[t for t in local['tracks'] if t['uuid'] not in WALL|{ISTUB}], 'vias':[v for v in local['vias'] if v['uuid']!=IV]}
 rec,trees=K.F.build(base); window=wide['window']; court=c['courtyard']; io_old=wide['prior']['IO3']; ip=next(p for p in base['pads'] if p['ref']=='C1028' and str(p['num'])=='1'); ips=unary_union(K.L.poly(ip['layers']['B.Cu']))
 def req(net): return .175 if dom[K.L.norm(net)]==dom[CORE] else .625
 def expanded(q,r):
  if q['kind']=='via': v=q['source']; return K.Z.bounded_disk(v,v['d']/2+r)
  if q['kind']=='track': t=q['source'];return K.Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+r)
  if q['kind']=='pad' and q['uuid'] in circle:
   z=circle[q['uuid']];return K.Z.bounded_disk({'x':z['at'][0],'y':z['at'][1]},z['radius']+r)
  return K.Z.bounded_buffer(q['shape'],r+(.005 if q['kind']=='pad' else 0))
 reserve,exempt=K.A.reservations()
 def trackblocks(net,layer,radius):
  out=[expanded(q,radius+req(q['net'])) for q in rec[layer] if K.L.norm(q['net'])!=net]
  for v in base['vias']:
   if K.L.norm(v['net'])!=net:out.append(K.Z.bounded_disk(v,v['drill']/2+.275+radius))
  for p in base['pads']:
   if p.get('npth') or K.L.norm(p['net'])!=net:
    out.extend(K.Z.bounded_buffer(s,.275+radius) for s in K.L.poly(p.get('hole') or []))
  for r in full['rule_areas']:
   if r.get('no_tracks') and layer in r['layers']:out.extend(K.Z.bounded_buffer(s,radius+.025) for s in K.L.poly(r['outline']))
  for r in reserve['keepouts']:
   if net not in exempt.get(r['name'],set()):out.extend(K.Z.bounded_buffer(s,radius+.025) for s in K.L.poly(r['outline']))
  for z in wide['current_native_intents']:
   if z['rule_area'] or layer not in z['layers'] or K.L.norm(z['raw_net']) in (net,LG):continue
   out.extend(K.Z.bounded_buffer(Polygon(rs[0],rs[1:]),radius+req(z['raw_net'])) for rs in z['outline_mm_exact_native_IU_div_1e6'])
  return out
 iv=Point(io_old['x'],io_old['y']).buffer(3,quad_segs=128)
 for ly,rows in rec.items():
  for q in rows:
   if K.L.norm(q['net'])!=IO:iv=iv.difference(expanded(q,.3+req(q['net'])))
 for p in base['pads']:
  if p['smd']:
   for ly,rs in p['layers'].items():
    if ly not in ('F.Cu','B.Cu'):continue
    for s in K.L.poly(rs):
     z=circle.get(p['uuid']); cut=K.Z.bounded_disk({'x':z['at'][0],'y':z['at'][1]},z['radius']+.425) if z else K.Z.bounded_buffer(s,.430)
     iv=iv.difference(cut)
  for s in K.L.poly(p.get('hole') or []):iv=iv.difference(K.Z.bounded_buffer(s,.425))
 for v in base['vias']:iv=iv.difference(K.Z.bounded_disk(v,v['drill']/2+.425))
 outside=iv.difference(court)
 for v in base['vias']:outside=outside.difference(K.Z.bounded_disk(v,.815))
 iv=iv.intersection(court).union(outside).difference(K.Z.bounded_disk({'x':sat[0],'y':sat[1]},.725))
 iv=iv.intersection(wide['IO3_source_fills']['In2.Cu'].buffer(-.300004)); rawiv=iv
 protected=[]
 for t in base['tracks']:
  shape=K.L.body(t)
  if shape.disjoint(iv.buffer(1)):continue
  supported=shape.intersection(c['source_refs'][K.MAP[t['layer']]])
  if not supported.is_empty:protected.append(supported)
 if protected:iv=iv.difference(K.Z.bounded_buffer(unary_union(protected),.550004))
 # Keep each actual old SOURCE-ground primitive's normal direct fill contact.
 lgfills={ly:unary_union([r['shape'] for r in c['ground_SOURCE'] if r['kind']=='fill' and r['layer']==ly]) for ly in K.LAYERS}
 contactguards=[]
 for p in c['ground_SOURCE']:
  if p['kind']=='fill' or p['shape'].disjoint(rawiv.buffer(1)):continue
  direct=p['shape'].intersection(lgfills[p['layer']])
  if not direct.is_empty:contactguards.append(K.Z.bounded_buffer(direct,.55 if p['layer'] in ('In1.Cu','In4.Cu') else .45))
 if contactguards:iv=iv.difference(unary_union(contactguards))
 for r in full['rule_areas']:
  if r.get('no_vias'):
   for s in K.L.poly(r['outline']):iv=iv.difference(K.Z.bounded_buffer(s,.325))
 for r in reserve['keepouts']:
  if IO not in exempt.get(r['name'],set()):
   for s in K.L.poly(r['outline']):iv=iv.difference(K.Z.bounded_buffer(s,.325))
 bblocks=trackblocks(IO,'B.Cu',.125);bblocks.append(K.Z.bounded_disk({'x':sat[0],'y':sat[1]},.55));bfree=window.difference(unary_union(bblocks));bparts=[p for p in pieces(bfree) if not p.intersection(ips).is_empty];bcell=unary_union(bparts);reachable=iv.intersection(bcell)
 put('status.json',{'phase':'COUPLED_ORDINARY_IO3_WITH_PRESERVED_SOURCE_CONTACTS','ordinary_region':info(rawiv),'strict_region':info(iv),'B_supply_reachable':info(reachable)})
 print(json.dumps({'phase':'IO3_REGIONS','ordinary':info(rawiv),'strict':info(iv),'B_reachable':info(reachable)}),flush=True)
 fblocks=trackblocks(CORE,'F.Cu',.625);fblocks.append(K.Z.bounded_disk({'x':sat[0],'y':sat[1]},1.05));core_geo=window.difference(unary_union(fblocks));A=[148.65,90.65];B=[154.65,96.65]
 retained=[p for p in contact['direct_same_net_native_F_contacts'] if p['uuid'] not in WALL]; assert len(retained)==16
 oldbody=K.L.body(coretracks[0]); contacts=[(p,oldbody.intersection(K.L.body(p['exact_current_native_original_geometry']))) for p in retained]
 branch=next(g for p,g in contacts if p['uuid']=='a72621ad-3c77-4ab2-9703-4d31121c0e01'); waypoint=list(branch.centroid.coords[0]); trials=[];accepted=[]
 points=[]
 for part in pieces(reachable):
  if part.geom_type!='Polygon':continue
  for p in (part.representative_point(),part.centroid):
   if part.covers(p):
    q=[round(x,6) for x in p.coords[0]]
    if q not in points:points.append(q)
 for at in points:
  owncap=Point(at).buffer(.575,quad_segs=256);io_cut=K.Z.bounded_disk({'x':at[0],'y':at[1]},.55);sg_cut=K.Z.bounded_disk({'x':sat[0],'y':sat[1]},.5)
  bsource=c['source_refs']['In4.Cu'].difference(io_cut.union(sg_cut));ballow=bsource.union(owncap).buffer(-.125004);bf=bfree.intersection(ballow);bp=next((p for p in pieces(bf) if p.covers(Point(at)) and not p.intersection(ips.buffer(-.005)).is_empty),None)
  row={'IO3_at':at,'power_B_source_route':False,'CORE_geometry_route':False,'CORE_strict_source_route':False}
  if bp is None:trials.append(row);continue
  port=bp.intersection(ips.buffer(-.005)).representative_point();port=[round(x,6) for x in port.coords[0]];bpath,bmeta=tri_route.route(bp,port,at);bpath=[[round(x,6) for x in q] for q in bpath];bbody=K.Z.bounded_buffer(LineString(bpath),.125);bgap=bbody.difference(owncap).difference(bsource)
  row.update(power_B_source_route=bgap.is_empty,power_B_path=bpath,power_B_literal_source_gap=info(bgap))
  if not bgap.is_empty:trials.append(row);continue
  geom=core_geo.difference(K.Z.bounded_disk({'x':at[0],'y':at[1]},1.10));src=c['source_refs']['In1.Cu'].difference(io_cut.union(sg_cut));strict=geom.intersection(src.buffer(-.625004));route=None;strictpass=False
  for free,isstrict in ((strict,True),(geom,False)):
   part=next((p for p in pieces(free) if p.covers(Point(A)) and p.covers(Point(B)) and p.covers(Point(waypoint))),None)
   if part is None:continue
   left,meta1=tri_route.route(part,A,waypoint);right,meta2=tri_route.route(part,waypoint,B);route=left+right[1:];route=[[round(x,6) for x in q] for q in route];strictpass=isstrict;break
  if route is None:trials.append(row);continue
  body=K.Z.bounded_buffer(LineString(route),.625);missing=body.difference(src);loss=[]
  for old,contact_shape in contacts:
   gap=contact_shape.difference(body)
   if not gap.is_empty:loss.append({'UUID':old['uuid'],'raw_literal_contact_loss':info(gap)})
  row.update(CORE_geometry_route=True,CORE_strict_source_route=strictpass,CORE_path=route,CORE_new_whole_body_SOURCE_gap=info(missing),all16_retained_literal_contact_losses=loss,CORE_old_length_mm=math.dist(A,B),CORE_new_length_mm=LineString(route).length)
  row['CORE_conditional_delta_R_25um_Cu_125C_ohm']=1.724e-5*(1+.00393*(125-20))*(row['CORE_new_length_mm']-row['CORE_old_length_mm'])/(1.25*.025)
  if missing.is_empty and not loss:accepted.append(row)
  trials.append(row)
  print(json.dumps({'phase':'COUPLED_TRIAL','at':at,'B_source':True,'CORE_route':True,'CORE_source_gap_empty':missing.is_empty,'literal_contacts_lost':len(loss)}),flush=True)
 put('all-coupled-ordinary-IO3-CORE-source-contact-trials.json',trials)
 cache=OUT/'coupled-only-authorized-CORE-duplicates-IO3-ordinary-CDONE-screen-context.pkl';cache.write_bytes(pickle.dumps({'wide':wide,'c':c,'own':own,'CORE_before':coretracks,'CORE_contacts':contact,'ordinary_IO3_region':iv,'B_supply_reachable':reachable,'CORE_geometry_free':core_geo,'trials':trials,'accepted':accepted,'signal_at':sat},protocol=5))
 result={'verdict':'COUPLED_DUPLICATE_CORE_ORDINARY_IO3_SOURCE_CONTACT_SCREEN_POSITIVE_ALL_GRAPH_CURRENT_NATIVE_OPEN' if accepted else 'COUPLED_DUPLICATE_CORE_ORDINARY_IO3_BOUNDED_SCREEN_NO_FULL_POSITIVE','raw_ordinary_IO3_region':info(rawiv),'strict_all_old_reference_direct_contact_guarded_IO3_region':info(iv),'B_supply_reachable_IO3_region':info(reachable),'trials':len(trials),'accepted':len(accepted),'best':min(accepted,key=lambda q:q['CORE_new_length_mm']) if accepted else None,'only_original_CORE_owners':sorted(WALL),'all17_contact_treatment':'16 untouched literal contact areas hard; the seventeenth is the controlled paired duplicate and must remain coincident after replacement','other_controlled_material':[IV,ISTUB],'VIPPO_registry_changes':0,'full_old_all_net_SOURCE_groups_current_planes_native_masks_current_IR_thermal_PDN_SI':'OPEN; no native adoption or job','native_jobs':0,'adopted':False,'cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k] for k in ('verdict','trials','accepted','best','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
