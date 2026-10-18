"""Select the next exact original lost relationship without a new board.

Current physical groups remain HOST evidence. Native R157 residual labels,
old chunks and observed masks are bound separately; no route acceptance.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;P=H.parent
for d in (P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.ops import unary_union,nearest_points
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'original-r07-residual-next-current-physical-port-census-r604'
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes())
 rp=pin(P/'original-r07-seventeen-lost-joins-actual-native-R157-residual-r287/actual-full-native-R157-unrestored-original-lost-relationships.json');res=json.loads(rp.read_bytes())
 np=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb','3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38');native=K.C.inventory(np.read_bytes())[3]
 fp=pin(P/'R155-known-reference-native-diagnostic-r157/measure/actual-full-refill-via-flashes.json','b64eb5a7ceab4c162699943ed5444554a93c7564cd391eb7dec4ce6e68512ce1');masks=json.loads(fp.read_bytes())['vias'];ctx=K.hole_context(c);rows=[];cache={}
 skip={'DI6_LOGIC','DI15_LOGIC','DOA_Q0_READY_N','DOA_SDO_FIELD'}
 for old in res:
  net=old['normalized_original_net']
  if net.rsplit('/',1)[-1]in skip:continue
  groups=K.physical(c,net,ctx)[1];cache[net]=groups;rr=[];metals=[]
  for i,group in enumerate(groups):
   pads=[r for r in group if r['kind']=='pad'];
   if not pads:continue
   padrows=[]
   for r in pads:
    p=next(x for x in h['pads']if x['uuid']==r['uuid']);z={'ref':p['ref'],'pin':str(p['num']),'UUID':p['uuid'],'at_mm':[p['x'],p['y']],'layers':list(p['layers'])}
    if z not in padrows:padrows.append(z)
   vv=[]
   for v in h['vias']:
    if K.L.norm(v['net'])!=net or not any(r['kind']=='via'and r['uuid']==v['uuid']for r in group):continue
    vv.append({'UUID':v['uuid'],'at_mm':[v['x'],v['y']],'diameter_mm':v['d'],'drill_mm':v['drill'],'actual_NATIVE_R157_masks':masks.get(v['uuid']),'original_NATIVE_R157_chunk_retained':v['uuid']in native})
   rr.append({'physical_group':i,'pads':padrows,'vias':vv,'Cu_key_count':len(K.keys(group))})
   metals.append((i,{ly:unary_union([r['shape']for r in group if r['layer']==ly])for ly in K.LAYERS}))
  options=[]
  for j,(ia,aa)in enumerate(metals):
   for ib,bb in metals[j+1:]:
    for ly in K.LAYERS:
     if aa[ly].is_empty or bb[ly].is_empty:continue
     x,y=nearest_points(aa[ly],bb[ly]);options.append({'groups':[ia,ib],'layer':ly,'nearest_actual_drilled_Cu_distance_mm':x.distance(y),'contact_points_mm':[list(x.coords)[0],list(y.coords)[0]]})
  row={'normalized_net':net,'original_native_R157_group_labels':old['actual_R157_current_groups'],'current_HOST_pad_group_count':len(rr),'current_groups':rr,'nearest_same_layer_options':sorted(options,key=lambda z:z['nearest_actual_drilled_Cu_distance_mm'])[:12]};rows.append(row);print('R604_NET',net,len(rr),[(x['layer'],round(x['nearest_actual_drilled_Cu_distance_mm'],3))for x in row['nearest_same_layer_options'][:3]],flush=True)
 f=OUT/'exact-current-other-residual-groups-NOMINATION_ONLY.pkl';f.write_bytes(pickle.dumps(cache,protocol=5));(OUT/'receipt.json').write_text(json.dumps({'verdict':'NEXT_ORIGINAL_R07_LOSSES_CURRENT_PORTS_FROZEN_NOMINATION_ONLY','input_SHA256':pins,'rows':rows,'cached_groups_file':str(f.resolve()),'cached_groups_SHA256':sha(f),'native_jobs':0,'board_written':False,'adopted':False,'full_current_after_drill_native_reference_current_SI':'OPEN','elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R604_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
