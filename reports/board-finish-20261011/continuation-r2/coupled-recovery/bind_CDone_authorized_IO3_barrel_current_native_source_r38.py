"""Bind only the authorized IO3 barrel and prepare wide exact-current ROI."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for p in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from verify_source import parse,children,child,atom
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union
OUT=H/'FPGA-CDONE-authorized-IO3-barrel-real-source-integer-pose-profile-and-wide-ROI-r38'
IO='/IO_3V3';LG='/LOGIC_GND';UID='0f88a8b6-67a2-4f38-b7cf-6b33a89cf99e'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();rp=H/'FPGA-CDONE-exact-IO3-barrel-controlled-move-ordinary-escape-screen-r37/receipt.json';r=json.loads(rp.read_bytes());cp=Path(r['cache_file']);assert sha(cp)==r['cache_SHA256'];prior=pickle.loads(cp.read_bytes());c=prior['context'];full=c['full_before'];sourcefile=Path(c['current_native_source']);assert sha(sourcefile)=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2';native=K.C.inventory(sourcefile.read_bytes())[3];chunk=native[UID];ast=parse(chunk.decode());io=prior['IO3'];old=[io['x'],io['y']];pose={'UUID':UID,'raw_net':atom(ast,'net'),'at_integer_IU':[round(float(x)*1e6)for x in child(ast,'at')[1:3]],'diameter_integer_IU':round(float(atom(ast,'size'))*1e6),'drill_integer_IU':round(float(atom(ast,'drill'))*1e6),'span':child(ast,'layers')[1:],'locked':child(ast,'locked'),'remove_unused_layers':child(ast,'remove_unused_layers'),'actual_FULL_BEFORE_flashes':io['flashed'],'native_chunk_SHA256':hashlib.sha256(chunk).hexdigest(),'controlled_definition_preserves_UUID_net_size_drill_span_lock':True};(OUT/'authorized-IO3-barrel-exact-before-native.chunk').write_bytes(chunk);put('authorized-native-barrel-definition-and-observed-before-masks.json',pose)
 gf=ROOT/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-all-net-groups.pkl';assert sha(gf)=='d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a';groups=pickle.loads(gf.read_bytes());source=K.root(groups[IO],'R18001','2');keys=K.keys(source);oldkeys=[['via',UID,ly]for ly in io['flashed']];assert all(tuple(k)in keys for k in oldkeys);ann=Point(old).buffer(io['d']/2,quad_segs=128).difference(Point(old).buffer(io['drill']/2,quad_segs=128));iofills={ly:unary_union([p['shape']for p in source if p['kind']=='fill'and p['layer']==ly])for ly in K.LAYERS};finite={ly:ann.intersection(iofills[ly]).area for ly in K.LAYERS};assert finite['In2.Cu']>0;incident=prior['incident'];assert len(incident)==1;originalcontacts=[]
 for g in groups[IO]:
  if not any(p['kind']=='via'and p['uuid']==UID for p in g):continue
  for p in g:
   if p['kind']in('pad','track','via')and p['shape'].intersects(ann):originalcontacts.append({k:p.get(k)for k in('kind','uuid','layer','ref','pin')})
 nf=ROOT/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(nf)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';nd=parse(nf.read_text());netnodes={K.L.norm(atom(n,'name')):[{p[0]:p[1]for p in q[1:]}for q in children(n,'node')]for n in children(child(nd,'nets'),'net')};ion=netnodes[IO];assert any(x['ref']=='R18001'and x['pin']=='2'for x in ion);comp=next(q for q in children(child(nd,'components'),'comp')if atom(q,'ref')=='R18001');otherpin=[{'net':n,'node':q}for n,ps in netnodes.items()for q in ps if q.get('ref')=='R18001'and q.get('pin')!='2'];sourcebinding={'root':'R18001.2','actual_all_net_ROOT_nonfill_keys':len(keys),'authorized_barrel_all_observed_before_layer_keys_SOURCE':True,'authorized_barrel_before_SOURCE_annular_contact_mm2':finite,'native_incident_tracks_retained':incident,'old_direct_Cu_contacts':originalcontacts,'fresh_source_R18001_component':{'ref':'R18001','value':atom(comp,'value'),'footprint':atom(comp,'footprint')},'fresh_source_R18001_upstream_pin_nets':otherpin,'fresh_IO3_node_count':len(ion),'fresh_IO3_local_FPGA_and_C1028_nodes':[q for q in ion if q.get('ref')in('U1001','C1028','R18001')],'supply_current_total_IR_rating_thermal_and_actual_native_AFTER':'OPEN'};put('real-source-before-and-fresh-IO3-supply-contact-contract.json',sourcebinding)
 ip=ROOT/'current-R753-all-native-zone-intents-read-only-r312/all-current-native-intended-zone-outlines-and-profiles.json';assert sha(ip)=='80452bcf08504313ac21195aba3d11ba11751bcd8943245c2404fb7c55e565c2';intents=json.loads(ip.read_bytes());around=[]
 for z in intents:
  shapes=[Polygon(rings[0],rings[1:])for rings in z['outline_mm_exact_native_IU_div_1e6']]
  if not any(s.intersects(Point(old).buffer(3))for s in shapes):continue
  own=K.L.norm(z.get('raw_net')or'')==IO;clear=(z.get('local_clearance_IU')or 150000)/1e6;row={k:z.get(k)for k in('UUID','raw_name','raw_net','layers','local_clearance_IU','priority','rule_area','no_tracks','no_vias')};row['authorized_IO3_own_plane_normal_copper_treatment']='own solid annulus with physical .150 drill radius only; no foreign antipad'if own else'foreign via native clearance antipad; own-SG reference cap grants no plane clip waiver';row['foreign_IO3_nominal_antipad_radius_mm']=None if own else io['d']/2+clear;row['normal_drill_radius_mm']=io['drill']/2;around.append(row)
 put('actual-current-native-connection-profiles-near-authorized-barrel.json',around)
 ep=ROOT/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json';assert sha(ep)=='13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3';expected=json.loads(ep.read_bytes())['copper'];win=box(old[0]-8,old[1]-8,old[0]+8,old[1]+8);oldv={v['uuid']:v for v in full['vias']};tracks=[];vias=[]
 for uid,e in expected.items():
  if e['kind']=='via':
   at=[x/1e6 for x in e['at_IU']]
   if not win.covers(Point(at)):continue
   diam=set(e['diameters_IU'].values());assert len(diam)==1;vias.append({'uuid':uid,'net':e['raw_net'],'x':at[0],'y':at[1],'d':next(iter(diam))/1e6,'drill':e['drill_IU']/1e6,'flashed':oldv[uid]['flashed']if uid in oldv else list(K.LAYERS)})
  else:
   a=[x/1e6 for x in e['start_IU']];b=[x/1e6 for x in e['end_IU']]
   if not LineString([a,b]).intersects(win):continue
   tracks.append({'uuid':uid,'net':e['raw_net'],'layer':e['layer'],'a':a,'b':b,'w':e['width_IU']/1e6})
 pp=ROOT/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json';poseall=json.loads(pp.read_bytes())['pads'];pads=[p for p in full['pads']if win.covers(Point(p['x'],p['y']))]
 for p in pads:
  actual=poseall[p['uuid']];assert str(actual[0])==str(p['num'])and actual[1]==p['net']and abs(actual[2]/1e6-p['x'])<.000001and abs(actual[3]/1e6-p['y'])<.000001
 wide={**full,'tracks':tracks,'vias':vias,'pads':pads,'zones':[]};cache=OUT/'exact-wide-current-Cu-and-real-IO3-SOURCE-screen-context.pkl';cache.write_bytes(pickle.dumps({'prior':prior,'wide_current':wide,'window':win,'IO3_source_group':source,'IO3_source_fills':iofills,'SOURCE_binding':sourcebinding,'current_native_intents':intents},protocol=5));receipt={'verdict':'EXACT_AUTHORIZED_IO3_BARREL_REAL_BEFORE_SOURCE_AND_WIDE_CURRENT_SCOPE_BOUND','native_pose':pose,'before_IO3_SOURCE_root_nonfill_keys':len(keys),'native_incident_tracks':len(incident),'before_In2_SOURCE_annular_area_mm2':finite['In2.Cu'],'wide_current_tracks':len(tracks),'wide_current_vias':len(vias),'wide_current_native_unchanged_pad_poses':len(pads),'current_native_profiles_bound':len(around),'ordinary_process_VIPPO_location_list':'unchanged; no new process location emitted','actual_after_source_current_IR_thermal_native_masks':'OPEN','native_jobs':0,'adopted':False,'cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'input_SHA256':{str(p.resolve()):sha(p)for p in(rp,cp,sourcefile,gf,nf,ip,ep,pp)},'elapsed_seconds':time.monotonic()-st};put('receipt.json',receipt);print(json.dumps({k:receipt[k]for k in('verdict','before_IO3_SOURCE_root_nonfill_keys','native_incident_tracks','before_In2_SOURCE_annular_area_mm2','wide_current_tracks','wide_current_vias','wide_current_native_unchanged_pad_poses','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
