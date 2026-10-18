"""Route only NEW .25 B supply stem to the controlled ordinary IO3 pose."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math,uuid
H=Path(__file__).resolve().parent;ROOT=H.parent
for p in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from verify_source import parse,children,child,atom
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
import tri_route
OUT=H/'FPGA-CDONE-ordinary-IO3-source-supply-B-stem-controlled-barrel-route-r41'
IO='/IO_3V3';NET='/fpga_core/FPGA_CDONE';LG='/LOGIC_GND';UID='0f88a8b6-67a2-4f38-b7cf-6b33a89cf99e'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def pieces(s):return [q for x in s.geoms for q in pieces(x)]if hasattr(s,'geoms')else[s]if not s.is_empty else[]
def read(receipt):
 r=json.loads(receipt.read_bytes());p=Path(r['cache_file']);assert sha(p)==r['cache_SHA256'];return r,p,pickle.loads(p.read_bytes())
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();rp=H/'FPGA-CDONE-exact-IO3-barrel-controlled-move-ordinary-escape-screen-r40/receipt.json';r,cp,d=read(rp);wr=H/'FPGA-CDONE-authorized-IO3-barrel-real-source-integer-pose-profile-and-wide-ROI-r38/receipt.json';w,wp,wide=read(wr);c=d['context'];full=c['full_before'];local=wide['wide_current'];base={**local,'vias':[v for v in local['vias']if v['uuid']!=UID]};rec,trees=K.F.build(base);dom=full['domains_normalized'];pad=next(p for p in local['pads']if p['ref']=='C1028'and str(p['num'])=='1');assert K.L.norm(pad['net'])==IO;padshape=unary_union(K.L.poly(pad['layers']['B.Cu']));inputnative=Path(c['current_native_source']);native=K.C.inventory(inputnative.read_bytes())[3];profile=[]
 for z in wide['current_native_intents']:
  if z['rule_area']:continue
  if not any(Polygon(rings[0],rings[1:]).intersects(wide['window'])for rings in z['outline_mm_exact_native_IU_div_1e6']):continue
  ast=parse(native[z['UUID']].decode());connect=child(ast,'connect_pads');fill=child(ast,'fill');row={k:z[k]for k in('UUID','raw_net','layers','local_clearance_IU','priority')};row.update(exact_native_connect_pads=connect,exact_native_fill_options=[x for x in fill[1:]if isinstance(x,list)],native_chunk_SHA256=hashlib.sha256(native[z['UUID']]).hexdigest());profile.append(row)
 assert any(q['raw_net']==IO and'In2.Cu'in q['layers']and q['exact_native_connect_pads'][1]=='yes'for q in profile);put('current-native-solid-own-IO3-versus-foreign-antipad-connection-profiles.json',profile)
 court=c['courtyard'];results=[];winners=[]
 for trial in d['trials']:
  sat=[round(x,6)for x in trial['ordinary_new_SG_at']];vat=[round(x,6)for x in trial['prospective_IO3_at']];centre=Point(vat);sg=Point(sat);blocks=[]
  for q in rec['B.Cu']:
   if K.L.norm(q['net'])==IO:continue
   gap=.175 if dom[K.L.norm(q['net'])]==dom[IO]else .625
   if q['kind']=='via':v=q['source'];block=K.Z.bounded_disk(v,v['d']/2+.125+gap)
   elif q['kind']=='track':t=q['source'];block=K.Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+.125+gap)
   else:block=K.Z.bounded_buffer(q['shape'],.125+gap+(.005 if q['kind']=='pad'else 0))
   blocks.append(block)
  blocks.append(K.Z.bounded_disk({'x':sat[0],'y':sat[1]},.25+.125+.175))
  reserve,exempt=K.A.reservations()
  for q in full['rule_areas']:
   if q.get('no_tracks')and'B.Cu'in q['layers']:blocks.extend(K.Z.bounded_buffer(s,.150)for s in K.L.poly(q['outline']))
  for q in reserve['keepouts']:
   if IO not in exempt.get(q['name'],set()):blocks.extend(K.Z.bounded_buffer(s,.150)for s in K.L.poly(q['outline']))
  # All untouched native B pour definitions remain literal. Only their
  # prospective clearance-driven fill channel may be ledgered later.
  for z in wide['current_native_intents']:
   if z['rule_area']or'B.Cu'not in z['layers']or K.L.norm(z['raw_net'])in(IO,LG):continue
   gap=.175 if dom[K.L.norm(z['raw_net'])]==dom[IO]else .625
   blocks.extend(K.Z.bounded_buffer(Polygon(rings[0],rings[1:]),.125+gap)for rings in z['outline_mm_exact_native_IU_div_1e6'])
  ref=c['source_refs']['In4.Cu'].difference(K.Z.bounded_disk({'x':sat[0],'y':sat[1]},.5)).difference(K.Z.bounded_disk({'x':vat[0],'y':vat[1]},.55));cap=centre.buffer(.575,quad_segs=256);allow=ref.union(cap).buffer(-.125004);free=wide['window'].difference(unary_union(blocks)).intersection(allow);component=next((p for p in pieces(free)if p.covers(centre)),None);ports=padshape.buffer(-.005).intersection(component)if component is not None else Point().buffer(0);row={'new_ordinary_SG_at':sat,'controlled_same_UUID_IO3_barrel_at':vat,'SOURCE_B_supply_port_region':info(ports),'source_caps_only_owned_new_IO3_nominal_575':True,'whole_B_source_without_old_hole_restoration':True}
  if not ports.is_empty:
   port=ports.representative_point();at=[round(x,6)for x in port.coords[0]];path,meta=tri_route.route(component,at,vat);path=[[round(x,6),round(y,6)]for x,y in path];axis=LineString(path);body=K.Z.bounded_buffer(axis,.125);rawgap=body.difference(cap).difference(ref);padcontact=body.intersection(padshape);length=axis.length;sourceann=centre.buffer(.3,quad_segs=128).difference(centre.buffer(.15,quad_segs=128)).intersection(wide['IO3_source_fills']['In2.Cu']);row.update(path=path,width_mm=.25,length_mm=length,route=meta,literal_SOURCE_In4_gap=info(rawgap),finite_C1028_1_pad_body_contact=info(padcontact),finite_own_In2_SOURCE_annulus=info(sourceann),conditional_added_trace_R_25um_Cu_125C_ohm=1.724e-5*(1+.00393*(125-20))*length/(.25*.025))
   if rawgap.is_empty and padcontact.area>0 and sourceann.area>0 and component.covers(axis):winners.append(row)
  results.append(row)
 put('four-controlled-ordinary-IO3-site-source-power-B-route-results.json',results);winner=min(winners,key=lambda x:x['length_mm'])if winners else None;cache=OUT/'only-controlled-IO3-and-CDONE-ordinary-source-B-supply-route-screen.pkl';cache.write_bytes(pickle.dumps({'current_scope':wide,'ordinary_CDONE_scope':d,'routes':results,'winner':winner},protocol=5));receipt={'verdict':'ORDINARY_CDONE_ESCAPE_AND_CONTROLLED_IO3_SUPPLY_B_SOURCE_BODY_SCREEN_PASS_JOINT_NATIVE_GEOMETRY_GRAPH_OPEN'if winner else'ORDINARY_CDONE_ESCAPE_CONTROLLED_IO3_SUPPLY_B_SOURCE_ROUTE_BOUNDED_NO_POSITIVE','source_power_B_positive_routes':len(winners),'selected':winner,'original_IO3_B_track':'75d7c648-ecac-4737-91c0-d51a6e01d011 retained literal; added stem touches its own C1028.1 pad','raw_mask_cu_profiles_old_all_SOURCE_graph_fill_B_contact_island_and_current_thermal_PDN_SI':'OPEN','new_VIPPO_locations':0,'native_jobs':0,'adopted':False,'cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'input_SHA256':{str(p.resolve()):sha(p)for p in(rp,cp,wr,wp,inputnative)},'elapsed_seconds':time.monotonic()-st};put('receipt.json',receipt);print(json.dumps({k:receipt[k]for k in('verdict','source_power_B_positive_routes','selected','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
