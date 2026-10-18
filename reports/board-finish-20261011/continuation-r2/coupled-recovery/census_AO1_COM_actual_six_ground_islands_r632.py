"""Freeze actual COM ground islands for explicit finite source bridges."""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import R157_native_selected_actual_conversion_r673 as N
from shapely.ops import unary_union,nearest_points
OUT=H/'AO1-COM-six-actual-native-ground-islands-source-bridge-census-r632';COM='/motherboard_analog_output/AO1_COM'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inf(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 op=pin(Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md'),'392e2155400e156d180ac5a786b2d7e4a41c2dcc945bfc7a8de9b9e21b02dde5');bp=pin(P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl','ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4');_,nh,_,_,nc=pickle.loads(bp.read_bytes());N.assert_R157_actual_before();gf=pin(N.R157/'actual-full-refill-geometry.json','421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b');mf=pin(N.R157/'actual-full-refill-via-flashes.json','b64eb5a7ceab4c162699943ed5444554a93c7564cd391eb7dec4ce6e68512ce1');np=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb','3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38');ng=json.loads(gf.read_bytes());masks=json.loads(mf.read_bytes())['vias'];actual,ctx,padproof=N.convert_selected_actual(nh,nc,ng,masks,{COM},np);groups=K.physical(actual,COM,ctx)[1];source=K.root(groups,'U14619','7');sourceid=groups.index(source);smet={ly:unary_union([r['shape']for r in source if r['layer']==ly])for ly in K.LAYERS};rows=[];cache={}
 for i,group in enumerate(groups):
  pads=[]
  for r in group:
   if r['kind']!='pad':continue
   p=next(p for p in nh['pads']if p['uuid']==r['uuid']);row={'ref':p['ref'],'pin':str(p['num']),'UUID':p['uuid'],'at_mm':[p['x'],p['y']],'layers':list(p['layers'])}
   if row not in pads:pads.append(row)
  if not pads:continue
  metals={ly:unary_union([r['shape']for r in group if r['layer']==ly])for ly in K.LAYERS};options=[]
  if i!=sourceid:
   for ly in K.LAYERS:
    if metals[ly].is_empty or smet[ly].is_empty:continue
    a,z=nearest_points(metals[ly],smet[ly]);options.append({'layer':ly,'actual_drilled_metal_gap_mm':a.distance(z),'target_point_mm':list(a.coords)[0],'source_point_mm':list(z.coords)[0]})
  cache[i]={'group':group,'metals':metals,'pads':pads};rows.append({'group':i,'SOURCE_U14619_7':i==sourceid,'pads':pads,'nonfill_keys':len(K.keys(group)),'source_isolation_relevant_U14623_ground':any(p['ref']=='U14623'for p in pads),'layer_metal':{ly:inf(s)for ly,s in metals.items()},'nearest_actual_direct_source_metals':sorted(options,key=lambda r:r['actual_drilled_metal_gap_mm'])});print('R632_GROUP',i,'source',i==sourceid,'pads',[(p['ref'],p['pin'])for p in pads],'gaps',[(r['layer'],round(r['actual_drilled_metal_gap_mm'],3))for r in sorted(options,key=lambda r:r['actual_drilled_metal_gap_mm'])[:3]],flush=True)
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');_,h,_,_,c=pickle.loads(mp.read_bytes());current=K.physical(c,COM,K.hole_context(c))[1];cl=[]
 for i,data in cache.items():
  keys=K.keys(data['group']);ids=[j for j,g in enumerate(current)if keys<=K.keys(g)];cl.append({'actual_native_group':i,'all_old_nonfill_keys_retained_in_one_current_group':len(ids)==1,'current_groups':ids})
 f=OUT/'actual-six-COM-islands-and-SOURCE-metals-NOMINATION_ONLY.pkl';f.write_bytes(pickle.dumps({'islands':cache,'source_group':sourceid,'source_metals':smet,'actual_ground_candidate':actual,'actual_native_via_masks':masks,'current_contact_bindings':cl},protocol=5));(OUT/'receipt.json').write_text(json.dumps({'verdict':'ACTUAL_NATIVE_COM_GROUND_ISLANDS_FROZEN_FOR_SAME_NET_FINITE_SOURCE_BRIDGE','input_SHA256':pins,'actual_pad_island_count':len(rows),'source_group':sourceid,'island_rows':rows,'actual_nonfill_group_contacts_vs_current':cl,'island_cache_file':str(f.resolve()),'island_cache_SHA256':sha(f),'new_ground_conductors_reference_rule':'Direct real BEFORE COM SOURCE contact and DC loop; not a new SIGNAL-reference shadow screen','barrier_other_domain_and_peer_VREF_Cu_remain_HARD':True,'native_jobs':0,'adopted':False,'native_AFTER_current_final_source_loops':'OPEN','elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R632_COMPLETE',sha(OUT/'receipt.json'),len(rows),flush=True)
if __name__=='__main__':main()
