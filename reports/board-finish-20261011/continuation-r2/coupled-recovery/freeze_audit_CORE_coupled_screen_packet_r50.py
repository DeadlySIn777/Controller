"""Freeze exact, blocked CORE/IO3/CDONE fragments; never save a candidate PCB."""
from pathlib import Path
import sys,json,pickle,hashlib,math,time,re,uuid,csv,io
H=Path(__file__).resolve().parent;ROOT=H.parent
for p in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
OUT=H/'FPGA-CDONE-two-CORE-owner-coupled-exact-screened-fragments-BLOCKED-r50'
CORE='/mc_local_power/CORE_5V';IO='/IO_3V3';SG='/fpga_core/FPGA_CDONE';LG='/LOGIC_GND'
WALL={'233cfa24-bc17-4dfa-9617-321c8db03618','b1e1f4cd-cfe9-421c-8c66-6662888515d5'}
IV='0f88a8b6-67a2-4f38-b7cf-6b33a89cf99e';STUB='75d7c648-ecac-4737-91c0-d51a6e01d011'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();rp=H/'FPGA-CDONE-CORE-controlled-pose-optimization-and-actual-upstream-SOURCE-start-r49/receipt.json';r=json.loads(rp.read_bytes());cp=Path(r['cache_file']);assert sha(cp)==r['cache_SHA256'];saved=pickle.loads(cp.read_bytes());d=saved['prior'];c=d['c'];wide=d['wide'];local=wide['wide_current'];full=c['full_before'];best=r['best'];assert best and not best['literal_contact_losses'];path=best['CORE_path'];at=best['IO3_at'];sat=d['signal_at'];nativefile=Path(c['current_native_source']);assert sha(nativefile)=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2';raw=nativefile.read_bytes();inventory=K.C.inventory(raw)[3];head,chunks,tail=K.C.pcbtext.split(raw);exact={};tracks=[];owners={};ids=set(inventory)
 fmt=lambda x:format(x,'.6f').rstrip('0').rstrip('.')
 def subpoint(b,key,p):
  expression=rb'(\('+key.encode()+rb'\s+)[^\)]*(\))';b,n=re.subn(expression,lambda m:m[1]+(' '.join(fmt(x)for x in p)).encode()+m[2],b,count=1);assert n==1;return b
 def subatom(b,key,value):
  expression=rb'(\('+key.encode()+rb'\s+)[^\)]*(\))';b,n=re.subn(expression,lambda m:m[1]+value.encode()+m[2],b,count=1);assert n==1;return b
 for owner in sorted(WALL):
  template=inventory[owner];owned=[]
  for index,(a,b)in enumerate(zip(path,path[1:])):
   uid=owner if index==0 else str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller:CDONE:CORE-coupled-r50:{owner}:{index}'))
   assert uid not in exact and(index==0 or uid not in ids);chunk=subpoint(subpoint(template,'start',a),'end',b);chunk=subatom(chunk,'uuid',json.dumps(uid));assert b'(locked yes)'in chunk;exact[uid]=chunk;t={'uuid':uid,'net':d['CORE_before'][0]['net'],'layer':'F.Cu','a':a,'b':b,'w':1.25};tracks.append(t);owned.append(uid)
  owners[owner]=owned
 io_original=next(v for v in local['vias']if v['uuid']==IV);iov={**io_original,'x':at[0],'y':at[1]};exact[IV]=subpoint(inventory[IV],'at',at)
 signal_via_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller:CDONE:CORE-coupled-r50:signal-via'));signal_track_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller:CDONE:CORE-coupled-r50:signal-F'));signal_raw=c['producer']['net'];signal={'uuid':signal_via_id,'net':signal_raw,'x':sat[0],'y':sat[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)}
 sgchunk=subpoint(inventory[IV],'at',sat);sgchunk=subatom(sgchunk,'size','0.5');sgchunk=subatom(sgchunk,'drill','0.2');sgchunk=subatom(sgchunk,'uuid',json.dumps(signal_via_id));sgchunk=subatom(sgchunk,'net',json.dumps(signal_raw));exact[signal_via_id]=sgchunk
 sf={'uuid':signal_track_id,'net':signal_raw,'layer':'F.Cu','a':[155.29,94.877],'b':sat,'w':.2};tracks.append(sf);sfchunk=inventory[STUB];sfchunk=subpoint(subpoint(sfchunk,'start',sf['a']),'end',sf['b']);sfchunk=subatom(sfchunk,'layer',json.dumps('F.Cu'));sfchunk=subatom(sfchunk,'width','0.2');sfchunk=subatom(sfchunk,'uuid',json.dumps(signal_track_id));sfchunk=subatom(sfchunk,'net',json.dumps(signal_raw));exact[signal_track_id]=sfchunk
 vias=[iov,signal];removed=WALL|{STUB,IV};base={**local,'tracks':[t for t in local['tracks']if t['uuid']not in removed]+tracks,'vias':[v for v in local['vias']if v['uuid']not in removed]+vias};records,trees=K.F.build({**base,'zones':[]});dom=full['domains_normalized'];circle=d['own']['actual_FPGA_circle_pad_math'];pad=next(p for p in local['pads']if p['ref']=='C1028'and str(p['num'])=='1');padshape=unary_union(K.L.poly(pad['layers']['B.Cu']));checks=[];errors=[]
 def axis(x):return Point(x['x'],x['y'])if'd'in x else LineString([x['a'],x['b']])
 def rad(x):return x['d']/2 if'd'in x else x['w']/2
 def check(record,okay):
  checks.append(record)
  if not okay:errors.append(record)
 for item in tracks+vias:
  ax=axis(item);radius=rad(item);net=K.L.norm(item['net']);lys=K.LAYERS if'd'in item else[item['layer']]
  for ly in lys:
   for q in records[ly]:
    if q['uuid']==item['uuid']or K.L.norm(q['net'])==net:continue
    if q['kind']in('via','track'):distance=ax.distance(axis(q['source']))-radius-rad(q['source'])
    elif q['kind']=='pad'and q['uuid']in circle:
     z=circle[q['uuid']];distance=ax.distance(Point(z['at']))-radius-z['radius']
    else:distance=ax.distance(q['shape'])-radius-(.005 if q['kind']=='pad'else 0)
    required=.175 if dom[K.L.norm(q['net'])]==dom[net]else .625
    if distance<required+.02:check({'kind':'true_current_and_peer_Cu','UUID':item['uuid'],'other_UUID':q['uuid'],'layer':ly,'gap_mm':distance,'required_mm':required},distance>=required)
  for v in base['vias']:
   if v['uuid']==item['uuid']or'd'not in item and K.L.norm(v['net'])==net:continue
   distance=ax.distance(Point(v['x'],v['y']))-v['drill']/2-(item['drill']/2 if'd'in item else radius)
   if distance<.30:check({'kind':'physical_hole','UUID':item['uuid'],'other_UUID':v['uuid'],'gap_mm':distance,'required_mm':.275},distance>=.275)
  for p in base['pads']:
   for s in K.L.poly(p.get('hole')or[]):
    if not p.get('npth')and'd'not in item and K.L.norm(p['net'])==net:continue
    distance=ax.distance(s)-(item['drill']/2 if'd'in item else radius)
    if distance<.30:check({'kind':'physical_pad_hole','UUID':item['uuid'],'other_UUID':p['uuid'],'gap_mm':distance,'required_mm':.275},distance>=.275)
   if'd'in item and p['smd']:
    for ly,rs in p['layers'].items():
     if ly not in('F.Cu','B.Cu'):continue
     for s in K.L.poly(rs):
      if item['uuid']==IV and p['uuid']==pad['uuid']:
       hole=K.Z.bounded_disk(item,item['drill']/2);check({'kind':'ONLY_new_exact_C1028_1_process_gated_own_land_drill_containment','UUID':IV,'pad_UUID':pad['uuid'],'process_qualification':'OPEN not an ordinary-hole waiver'},padshape.buffer(-.005).covers(hole));continue
      if p['uuid']in circle:z=circle[p['uuid']];distance=ax.distance(Point(z['at']))-z['radius']-item['drill']/2
      else:distance=ax.distance(s)-item['drill']/2-.005
      if distance<.30:check({'kind':'all_other_SMD_holes','UUID':item['uuid'],'other_UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'gap_mm':distance,'required_mm':.275},distance>=.275)
  if'd'in item:
   nearest=min((v for v in base['vias']if v['uuid']!=item['uuid']),key=lambda v:ax.distance(Point(v['x'],v['y'])));pitch=ax.distance(Point(nearest['x'],nearest['y']));check({'kind':'generic_via_pitch_also_screened_even_inside_courtyard','UUID':item['uuid'],'other_UUID':nearest['uuid'],'pitch_mm':pitch,'generic_required_mm':.815},pitch>=.815)
 put('all-analytic-current-Cu-peer-drill-own-land-screen-checks.json',checks);put('raw-analytic-geometry-errors.json',errors)
 # Attribute the upstream gap against actual FULL before and exact current intent.
 center=Point(148.65,90.65);disk=K.Z.bounded_disk({'x':148.65,'y':90.65},.625);beforefills=[];intents=[]
 for z in full['zones']:
  for s in K.L.poly(z['fills'].get('In1.Cu',[])):
   overlap=s.intersection(disk)
   if not overlap.is_empty:beforefills.append({'UUID':z['uuid'],'raw_net':z['net'],'overlap':info(overlap),'covers_A_center':s.covers(center)})
 for z in wide['current_native_intents']:
  if'In1.Cu'not in z['layers']:continue
  for rs in z['outline_mm_exact_native_IU_div_1e6']:
   shape=Polygon(rs[0],rs[1:]);overlap=shape.intersection(disk)
   if not overlap.is_empty:intents.append({k:z.get(k)for k in('UUID','raw_net','raw_name','layers','priority','local_clearance_IU','rule_area')}|{'overlap':info(overlap),'covers_A_center':shape.covers(center)});break
 put('upstream-fixed-A-actual-full-In1-floor-and-current-intent-attribution.json',{'fixed_A':[148.65,90.65],'actual_before_fills':beforefills,'exact_R753_current_intents':intents,'Source_reference_gate':'RAW unmet; never waived or replaced with another net or a cap'})
 # Exact sparse replay is computed in memory only; no candidate board is saved.
 replace={u:exact[u]for u in WALL|{IV}};added={u:b for u,b in exact.items()if u not in replace};deletes={STUB:inventory[STUB]};staged=[]
 for chunk in chunks:
  uid=K.C.pcbtext.chunk_uuid(chunk)
  if uid in deletes:continue
  staged.append(replace.get(uid,chunk))
 staged.extend(added.values());candidate=head+b''.join(staged)+tail;after=K.C.inventory(candidate)[3];unlisted=set(inventory)-(set(replace)|set(deletes));assert all(after[u]==inventory[u]for u in unlisted);assert K.C.pcbtext.split(candidate)[0]==head and K.C.pcbtext.split(candidate)[2]==tail
 for uid,chunk in exact.items():
  parsed=K.A.G.parse(uid,chunk,{})
  target=next(t for t in tracks+vias if t['uuid']==uid);assert parsed['net']==K.L.norm(target['net'])
  if'd'in target:assert parsed['at']==[target['x'],target['y']]and parsed['d']==target['d']and parsed['drill']==target['drill']
  else:assert parsed['a']==target['a']and parsed['b']==target['b']and parsed['w']==target['w']
 fragments=[]
 for uid,chunk in exact.items():
  p=OUT/(uid+'.BLOCKED-native-fragment');p.write_bytes(chunk);fragments.append({'UUID':uid,'file':str(p.resolve()),'SHA256':sha(p),'operation':'replace'if uid in replace else'add'})
 for uid,chunk in deletes.items():
  p=OUT/(uid+'.exact-authorized-retired-native-fragment');p.write_bytes(chunk);fragments.append({'UUID':uid,'file':str(p.resolve()),'SHA256':sha(p),'operation':'delete'})
 length=best['CORE_length_mm'];delta=length-best['CORE_original_length_mm'];deltaR=1.724e-5*(1+.00393*105)*delta/(1.25*.025);registry=Path('Z:/pcb-runs/fab-check/assembly/vippo.csv');assert sha(registry)=='4f4bb263f813351b849f131f1f29f247cbab0a958a250cd874f90cc0eb7e07bd';rows=list(csv.DictReader(io.StringIO(registry.read_text(encoding='utf-8-sig'))));assert len(rows)==291 and not any(x['via_uuid']==IV for x in rows)
 packet=OUT/'SCREENED-BLOCKED-only-authorized-CORE-IO3-CDONE-sparse-packet.pkl';packet.write_bytes(pickle.dumps({'tracks':tracks,'vias':vias,'exact_new_or_replaced_chunks':exact,'exact_old_replaced_chunks':{u:inventory[u]for u in replace},'exact_deleted_original_chunks':deletes,'CORE_owner_paths':owners,'new_process_location':{'via_UUID':IV,'at':at,'pad':'C1028.1','type':'new TypeVII filled planarized capped process location, OPEN'},'screen_before':{'native_file':str(nativefile),'SHA256':sha(nativefile)},'all_gates_open':['REFERENCE_RAW','SOURCE_GRAPH','CURRENT_THERMAL_PDN_SI','PROCESS_292','NATIVE_AFTER_MASKS','COMPLETE_CDONE_B_CONNECTION'],'adopted':False},protocol=5))
 manifest={'verdict':'EXACT_COUPLED_CORE_LITERAL_CONTACT_GEOMETRY_SCREEN_FROZEN_REFERENCE_PROCESS_CURRENT_BLOCKED','packet_file':str(packet.resolve()),'packet_SHA256':sha(packet),'analytic_geometry_errors':len(errors),'CORE_controlled_original_owners':sorted(WALL),'CORE_route_points':path,'CORE_width_mm':1.25,'CORE_route_length_old_mm':best['CORE_original_length_mm'],'CORE_route_length_new_mm':length,'CORE_delta_length_mm':delta,'conditional_delta_R_25um_Cu_125C_ohm':deltaR,'current_rating_or_voltage_drop_qualification':'OPEN; conditional dR multiplied by actual validated branch current only','CORE_duplicate_overlap_current_credit':'none; physical union remains 1.25mm wide','all16_untouched_original_literal_contact_regions_retained':True,'seventeenth_controlled_peer_duplicate_contact':'coincident replacement owner paths','moved_original_IO3_via_at':at,'new_signal_via_at':sat,'new_exact_process_locations_if_qualified':1,'existing_registry_locations_unmodified':291,'proposed_registry_total_only_if_qualified':292,'replace_original_chunks':sorted(replace),'delete_original_chunks':sorted(deletes),'added_chunks':sorted(added),'all_unlisted_original_native_chunks_literal_count':len(unlisted),'unlisted_chunks_all_literal':True,'all_footprint_pad_zone_header_tail_native_bytes_literal':True,'candidate_board_saved':False,'native_jobs':0,'adopted':False,'REFERENCE_RAW_gap_mm2':best['source_gap']['area_mm2'],'REFERENCE_RAW_upstream_fixed_A_has_no_actual_LG_In1':True,'source_current_process_native_qualification':'BLOCKED; no native staging/adoption authorized by this packet','remaining_CDONE_scope':'only producer F escape/SG; complete SOURCE-supported B connection still pending','fragments':fragments,'input_SHA256':{str(p.resolve()):sha(p)for p in(rp,cp,nativefile,registry)},'elapsed_seconds':time.monotonic()-st};put('frozen-screened-BLOCKED-sparse-native-operation-manifest.json',manifest);print(json.dumps({k:manifest[k]for k in('verdict','packet_SHA256','analytic_geometry_errors','CORE_delta_length_mm','conditional_delta_R_25um_Cu_125C_ohm','all_unlisted_original_native_chunks_literal_count','REFERENCE_RAW_gap_mm2','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
