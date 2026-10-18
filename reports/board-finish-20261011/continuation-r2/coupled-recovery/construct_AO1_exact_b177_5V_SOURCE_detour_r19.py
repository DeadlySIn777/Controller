"""Repair only the real b17752d1 5V SOURCE-reference loss in saved R11.

One explicitly controlled original power segment joins MON3 ownership.
Same endpoints/raw net/width/lock; no power aperture or generic cap credit.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import tri_route as T
from verify_source import parse,children,child,atom
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
OUT=H/'AO1-MON3-VREF-and-only-b177-5V-native-width-endpoint-source-detour-r19'
POWER='/motherboard_analog_output/AO1_5V';COM='/motherboard_analog_output/AO1_COM';UID='b17752d1-3aeb-4b37-8ae4-7fbf8502584e'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def pieces(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for g in s.geoms for p in pieces(g)]if hasattr(s,'geoms')else[]
def info(s):return{'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,w=None):
  p=Path(p);v=sha(p);assert w is None or v==w;pins[str(p.resolve())]=v;return p
 rr=pin(H/'AO1-MON3-VREF-actual-full-native-baseline-independent-host-scope-r12/receipt.json');r=json.loads(rr.read_bytes());assert r['strict_literal_old_SOURCE_reference_losses']==1 and r['geometry_errors']==0 and r['new_full_body_reference_losses']==0;mp=pin(r['host_model_file'],r['host_model_SHA256']);after=pickle.loads(mp.read_bytes());gp=pin(rr.parent/'AO1-and-local-antipad-all-drilled-after-groups.pkl',r['groups_SHA256']);ng=pickle.loads(gp.read_bytes());root=K.root(ng[COM],'U14619','7');reference=unary_union([q['shape']for q in root if q['kind']=='fill'and q['layer']=='In1.Cu']);old=next(t for t in after['tracks']if t['uuid']==UID);assert K.L.norm(old['net'])==POWER and old['layer']=='F.Cu';source=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');raw=source.read_bytes();inv=K.C.inventory(raw)[3];ch=inv[UID];p=K.A.G.parse(UID,ch,{});assert(p['net'],p['layer'],p['a'],p['b'],p['w'])==(POWER,old['layer'],old['a'],old['b'],old['w']);locked=b'(locked yes)'in ch
 minx,miny,maxx,maxy=LineString([old['a'],old['b']]).bounds;win=box(minx-2,miny-2,maxx+2,maxy+2);local={**after,'tracks':[t for t in after['tracks']if t['uuid']!=UID and not K.L.body(t).envelope.disjoint(win.buffer(1))],'vias':[v for v in after['vias']if not Point(v['x'],v['y']).envelope.disjoint(win.buffer(1))],'pads':[p for p in after['pads']if not Point(p['x'],p['y']).envelope.disjoint(win.buffer(1))],'zones':[]};rec,trees=K.F.build(local);dom=after['domains_normalized'];req=lambda n:.15 if dom[K.L.norm(n)]==dom[POWER]else .6;obs=[]
 for q in rec['F.Cu']:
  if K.L.norm(q['net'])==POWER:continue
  obs.append(K.Z.bounded_buffer(q['shape'],req(q['net'])+.025+old['w']/2+.000005))
 for z in after['zones']:
  if K.L.norm(z['net'])==POWER or req(z['net'])==.15:continue
  for sh in K.L.poly(z['fills'].get('F.Cu',[])):
   if not sh.envelope.disjoint(win.buffer(1)):obs.append(K.Z.bounded_buffer(sh.intersection(win.buffer(1)),max(z['clearance_mm'],req(z['net']))+.025+old['w']/2+.000005))
 obs.extend(K.Z.bounded_disk(v,v['drill']/2+.275+old['w']/2+.000005)for v in local['vias']if K.L.norm(v['net'])!=POWER)
 obs.extend(K.Z.bounded_buffer(sh,.275+old['w']/2+.000005)for pad in local['pads']for sh in K.L.poly(pad.get('hole')or[])if K.L.norm(pad['net'])!=POWER or pad['npth'])
 reserve,exempt=K.A.reservations()
 for rule in after['rule_areas']:
  if 'F.Cu'in rule['layers']and rule.get('no_tracks'):obs.extend(K.Z.bounded_buffer(sh,old['w']/2+.025)for sh in K.L.poly(rule['outline'])if not sh.envelope.disjoint(win.buffer(1)))
 for rule in reserve['keepouts']:
  if 'F.Cu'in rule['layers']and POWER not in exempt.get(rule['name'],set()):obs.extend(K.Z.bounded_buffer(sh,old['w']/2+.025)for sh in K.L.poly(rule['outline'])if not sh.envelope.disjoint(win.buffer(1)))
 free=win.difference(unary_union(obs)).intersection(reference.buffer(-old['w']/2-.000005));components=[s for s in pieces(free)if s.covers(Point(old['a']))and s.covers(Point(old['b']))];paths=None
 if components:
  pts,search=T.route(components[0],old['a'],old['b']);pts=[[round(x,6),round(y,6)]for x,y in pts]
  if len(pts)>1 and components[0].covers(LineString(pts)):paths={'layer':'F.Cu','points_mm':pts,'width_mm':old['w'],'locked_yes':locked,'length_mm':LineString(pts).length,'search':search}
 nf=pin(ROOT/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net','070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2');netdoc=parse(nf.read_text());n=next(n for n in children(child(netdoc,'nets'),'net')if atom(n,'name').replace('{slash}','/')==POWER);nodes=[{q[0]:q[1]for q in node[1:]}for node in children(n,'node')];candidates=[q for q in nodes if q.get('pintype')=='power_out'];put('fresh-actual-5V-source-pin-contract.json',{'raw_net':atom(n,'name'),'all_source_nodes':nodes,'power_out_source_selector_candidates':candidates,'source_changed':False,'every_supply_load_retained':True,'full_load_mesh_IR_current_capacity_qualification':'OPEN'})
 beforegroupsfile=pin(ROOT/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-all-net-groups.pkl','d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a');bg=pickle.loads(beforegroupsfile.read_bytes());sourceproof=[]
 for selector in candidates:
  group=K.root(bg[POWER],selector['ref'],selector['pin']);contains=any(q['kind']=='track'and q['uuid']==UID for q in group);sourceproof.append({'actual_source_ref':selector['ref'],'pin':selector['pin'],'pinfunction':selector.get('pinfunction'),'source_group_contains_original_b177':contains,'source_group_old_physical_layer_keys':len(K.keys(group))})
 if not sourceproof:sourceproof=[{'no_power_out_PIN_selector':'OPEN; positive 5V supply is not invented'}]
 put('actual-full-native-before-5V-source-to-b177-provenance.json',sourceproof);ident=K.A.N.SourceNets(raw);nt=[];chunks={}
 if paths:
  for a,b in zip(paths['points_mm'],paths['points_mm'][1:]):
   uid,chnew=ident.serial_segment(POWER,'F.Cu',a,b,old['w'])
   if locked:chnew=chnew.replace(b'\t\t(layer ',b'\t\t(locked yes)\n\t\t(layer ')
   assert (b'(locked yes)'in chnew)==locked;chunks[uid]=chnew;nt.append({'uuid':uid,'net':ident.raw(POWER),'layer':'F.Cu','a':a,'b':b,'w':old['w'],'locked_yes':locked})
  ident.assert_chunks(chunks);assert set(chunks).isdisjoint(inv)
 oldlength=LineString([old['a'],old['b']]).length;delta=None if not paths else paths['length_mm']-oldlength;rho125=1.724e-8*(1+.00393*(125-20));coef=None if delta is None else rho125*(delta*1e-3)/(old['w']*1e-3*25e-6);powercost={'native_width_mm':old['w'],'original_length_mm':oldlength,'proposed_length_mm':paths['length_mm']if paths else None,'added_length_mm':delta,'CONDITIONAL_same_25um_Cu_125C_incremental_series_ohm':coef,'incremental_drop_volts_at_actual_load_I':'I * stated conditional incremental series ohm; actual all-load IR ledger remains open','thickness_material_temperature_are_ASSUMPTIONS_not_fabrication_or_measurement':True,'actual_rail_voltage_limit_or_rating_changed':False};put('same-native-width-conditional-added-series-resistance-per-amp.json',powercost)
 oldchunk=OUT/(UID+'.exact-native-before-controlled-5V-chunk');oldchunk.write_bytes(ch);put('only-one-controlled-5V-segment-exact-native-owner-ledger.json',{'UUID':UID,'raw_net':old['net'],'a':old['a'],'b':old['b'],'native_width_mm':old['w'],'native_locked_yes':locked,'native_before_chunk_file':str(oldchunk.resolve()),'native_before_chunk_SHA256':sha(oldchunk),'other_5V_old_bodies_softened':0,'original_SDICu_or_old_5V_caps_borrowed':0});(OUT/'new5V-whole-body-SOURCE-COM-free-centres.wkb').write_bytes(free.wkb)
 cr=pin(H/'AO1-joint-VREF-ports-and-MON3-locked-source-supported-detour-r11/receipt.json');cp=json.loads(cr.read_bytes());vp=pin(cp['packet_file'],cp['packet_SHA256']);base=pickle.loads(vp.read_bytes());packet=OUT/'MON3-VREF-plus-exact-b177-5V-controlled-detour-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':base['tracks']+nt if paths else [],'vias':base['vias']if paths else [],'exact_new_chunks':base['exact_new_chunks']|chunks if paths else {},'deleted_original_chunks':base['deleted_original_chunks']|{UID:ch}if paths else {},'selected':base['selected'],'controlled_power_path':paths,'conditional_added_resistance':powercost,'power_source_before_proof':sourceproof},protocol=5));result={'verdict':'CONSTRUCTIVE_ONLY_B177_5V_NATIVE_WIDTH_REAL_SOURCE_BODY_DETOUR_MON3_VREF_NOMINEE'if paths else'B177_SINGLE_SEGMENT_SOURCE_BODY_DETOUR_BOUNDED_INCOMPLETE','exact_original_controlled_power_segment':old,'controlled_power_path':paths,'power_source_before_proof':sourceproof,'all_other_old_5V_and_SDI_SOURCE_supported_bodies_fixed':True,'packet_file':str(packet.resolve()),'packet_SHA256':sha(packet),'new_power_tracks':len(nt),'native_jobs':0,'adopted':False,'all_root_contact_reference_current_native_analog_SI_gates':'OPEN','input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','exact_original_controlled_power_segment','controlled_power_path','power_source_before_proof','new_power_tracks','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
