"""Rebind saved DI15 trails to actual R157 endpoints and native barrels.

Read-only constructive selectors. Existing current source groups/actual
native annuli qualify nominations only; no old Cu changes or native jobs.
"""
from pathlib import Path
import sys,json,pickle,hashlib,math,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import R157_native_selected_actual_conversion_r673 as N
from shapely.geometry import Point
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI15-actual-R157-current-native-port-return-census-r590';NET='/motherboard_di/DI15_LOGIC';LG='/LOGIC_GND'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return{'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes());src=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');orig=K.C.inventory(src.read_bytes())[3];np=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb');native=K.C.inventory(np.read_bytes())[3];N.assert_R157_actual_before();gf=pin(N.R157/'actual-full-refill-geometry.json','421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b');mf=pin(N.R157/'actual-full-refill-via-flashes.json','b64eb5a7ceab4c162699943ed5444554a93c7564cd391eb7dec4ce6e68512ce1');ng=json.loads(gf.read_bytes());masks=json.loads(mf.read_bytes())['vias'];nativevias={v['uuid']:v for v in ng['vias']};gb,missing=N.bound_R663_before_groups({LG});assert not missing;LGroot=K.root(gb[LG],'J11001','2');lgkeys=K.keys(LGroot);refs={ly:unary_union([r['shape']for r in LGroot if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')};ctx=K.hole_context(c);_,groups=K.physical(c,NET,ctx);selectors=[];original_ports=[]
 for ref,pin_,uid in[('U13001','25','f5027315-3d7a-42d1-b8e2-6e07075d2842'),('U17005','9','b9ed640f-51d8-4121-a94d-4a29c6058751')]:
  p=next(p for p in h['pads']if p['uuid']==uid);assert(p['ref'],str(p['num']),K.L.norm(p['net']))==(ref,pin_,NET);group=next(gr for gr in groups if any(r['kind']=='pad'and r['uuid']==uid for r in gr));pads=[(r['ref'],str(r['pin']))for r in group if r['kind']=='pad'];metals={ly:unary_union([r['shape']for r in group if r['layer']==ly])for ly in K.LAYERS};vps=[]
  for v in h['vias']:
   if K.L.norm(v['net'])!=NET or not any(r['kind']=='via'and r['uuid']==v['uuid']for r in group):continue
   assert v['uuid']in orig and orig[v['uuid']]==native[v['uuid']];n=nativevias[v['uuid']];assert(n['net'],n['at'],n['w'],n['drill'])==(v['net'],[v['x'],v['y']],v['d'],v['drill']);returns=[]
   for r in h['vias']:
    if K.L.norm(r['net'])!=LG or r['uuid']not in orig or r['uuid']not in nativevias:continue
    d=math.dist([v['x'],v['y']],[r['x'],r['y']])
    if not .9<=d<=1:continue
    rn=nativevias[r['uuid']]
    if(rn['net'],rn['at'],rn['w'],rn['drill'])!=(r['net'],[r['x'],r['y']],r['d'],r['drill']):continue
    ann=K.Z.bounded_disk(r,r['d']/2).difference(K.Z.bounded_disk(r,r['drill']/2));contacts={ly:ann.buffer(-.025,quad_segs=128).intersection(refs[ly])for ly in refs};returns.append({'UUID':r['uuid'],'at_mm':[r['x'],r['y']],'distance_mm':d,'actual_NATIVE_R157_flash_layers':masks[r['uuid']],'finite_NATIVE_J1_reference_annuli':{ly:info(sh)for ly,sh in contacts.items()},'actual_used_In1_J1_return':('via',r['uuid'],'In1.Cu')in lgkeys and'In1.Cu'in masks[r['uuid']]and not contacts['In1.Cu'].is_empty and contacts['In1.Cu'].area>.005,'actual_both_In1_In4_J1_return':all(('via',r['uuid'],ly)in lgkeys and ly in masks[r['uuid']]and not contacts[ly].is_empty and contacts[ly].area>.005 for ly in refs)})
   row={'role':ref+'.'+pin_,'original_native_signal_UUID':v['uuid'],'at_mm':[v['x'],v['y']],'diameter_mm':v['d'],'drill_mm':v['drill'],'actual_NATIVE_R157_flash_layers':masks[v['uuid']],'exact_unchanged_chunk_SHA256':K.C.sha(native[v['uuid']]),'existing_saved_policy_compliant_native_returns':returns};vps.append(row);original_ports.append(row)
  selectors.append({'actual_required_pad':{'ref':ref,'pin':pin_,'UUID':uid,'at_mm':[p['x'],p['y']],'raw_net':p['net']},'current_named_pad_group':pads,'current_native_copper_layer_keys':[list(x)for x in sorted(K.keys(group))],'original_native_signal_ports':vps,'current_full_component_metal_per_layer':{ly:info(sh)for ly,sh in metals.items()}})
 rg=pin(P/'original-r07-seventeen-lost-joins-actual-native-R157-residual-r287/actual-full-native-R157-unrestored-original-lost-relationships.json');rr=json.loads(rg.read_bytes());old=next(z for z in rr if z['normalized_original_net']==NET);assert old['actual_R157_current_groups']==[['U13001.25#0'],['U17005.9#0']]
 cache=OUT/'exact-current-DI15-physical-groups-and-actual_NATIVE-J1-reference-primitives-NOMINATION_ONLY.pkl';cache.write_bytes(pickle.dumps({'groups':groups,'nativeLGroot':LGroot,'native_refs':refs,'selectors':selectors,'ports':original_ports},protocol=5));put(OUT/'original-native-DI15-ports-and-all-.90-to-1.0-return-census.json',original_ports);result={'verdict':'ACTUAL_R157_ORIGINAL_DI15_PAD_SPLIT_AND_CURRENT_NATIVE_PORT_RETURN_SELECTORS_FROZEN','native_R287_exact_lost_relation':old,'exact_current_model_SHA256':sha(mp),'actual_native_R157_board_SHA256':sha(np),'actual_native_fullgeometry_SHA256':sha(gf),'selectors':selectors,'cached_component_file':str(cache.resolve()),'cached_component_SHA256':sha(cache),'existing_source_native_port_count':len(original_ports),'original_native_unchanged_or_proposed_peer_Cu_source_masks_not_waived':True,'ordinary_pairs_window_mm':[.9,1.0],'saved_max_layer_legs':3,'full_current_all_drills_source_body_oldloss_SI_and_combined_allnet_NATIVE_AFTER':'OPEN','input_SHA256':pins,'native_jobs':0,'adopted':False,'board_written':False,'elapsed_seconds':time.monotonic()-st};put(OUT/'receipt.json',result);print('R590_COMPLETE',sha(OUT/'receipt.json'),'ports',len(original_ports),flush=True)
if __name__=='__main__':main()
