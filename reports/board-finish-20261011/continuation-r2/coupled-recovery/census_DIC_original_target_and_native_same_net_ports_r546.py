"""Exact original DIC barrel/component census before a wider NEW route.

Read-only host evidence. Withdraw only unaccepted new CS_BUFFER items for
component selection; original native chunks, physical contacts and raw nets
stay authoritative. No refill, native job, model adoption or disk credit.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,collections
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.geometry import Point
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def small(r):
 return {k:v for k,v in r.items() if k not in ('shape','layers','source','hole')}
def shapeinfo(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}

def main():
 st=time.monotonic();out=H/'DIC-original-target-and-native-same-net-ports-r546';assert not out.exists();out.mkdir()
 mp=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl';assert sha(mp)=='97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14'
 sp=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sp)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 source=sp.read_bytes();inv=K.C.inventory(source);identity=K.A.N.SourceNets(source)
 g,h,b,q,c=pickle.loads(mp.read_bytes());NET='/motherboard_io_control/DIC_IOL1_CS_BUFFER';raw=identity.raw(NET)
 items=[t for t in h['tracks']if K.L.norm(t['net'])==NET]+[v for v in h['vias']if K.L.norm(v['net'])==NET]
 new={x['uuid']for x in items if x['uuid']not in inv[3]};original=[x for x in items if x['uuid']in inv[3]]
 assert len([v for v in h['vias']if v['uuid']in new])==2
 isolated={**c,'tracks':[t for t in h['tracks']if t['uuid']not in new],'vias':[v for v in h['vias']if v['uuid']not in new]}
 ctx=K.hole_context(isolated);_,groups=K.physical(isolated,NET,ctx)
 endpoints={'source':'73d7d605-feb4-47ae-b36a-40896fba4ee9','target':'c9bab2fa-e6cb-45f7-b879-a934865b0e12'}
 result={};cache={'isolated':isolated,'groups':groups,'NET':NET,'raw_net':raw,'original_native_parent_sha256':sha(sp),'current_model_sha256':sha(mp)}
 for label,uid in endpoints.items():
  pad=next(p for p in h['pads']if p['uuid']==uid);group=next(xs for xs in groups if any(r['kind']=='pad'and r['uuid']==uid for r in xs));metal=unary_union([r['shape']for r in group if r['layer']=='F.Cu']);cache[label+'_F_component']=metal
  fp=next(fp for fp in h['footprints']if fp['ref']==pad['ref'])if 'footprints'in h else None
  result[label]={'pad':small(pad),'pad_layer_shape_info':{ly:shapeinfo(unary_union(K.L.poly(rs)))for ly,rs in pad['layers'].items()},'actual_group_keys':[list(k)for k in sorted(K.keys(group))],'actual_group_rows':[small(r)for r in group if r['kind']!='fill'],'F_metal':shapeinfo(metal),'footprint':None if fp is None else small(fp)}
  (out/(label+'-actual-original-F-component.wkb')).write_bytes(metal.wkb)
 native=[]
 for v in h['vias']:
  if K.L.norm(v['net'])!=NET or v['uuid']not in inv[3]:continue
  chunk=inv[3][v['uuid']];assert source.count(chunk)==1
  gi=next(i for i,xs in enumerate(groups)if any(r['kind']=='via'and r['uuid']==v['uuid']for r in xs))
  native.append({'via':v,'exact_original_native_chunk':chunk.decode(),'exact_original_native_chunk_SHA256':K.C.sha(chunk),'current_original_component_index':gi,'layer_keys':[list(k)for k in sorted(K.keys(groups[gi]))if k[1]==v['uuid']],'new_actual_mask_or_paired_return_credit':'NONE; native contract remains independently mandatory'})
 put(out/'exact-original-target-components-and-native-same-net-barrels.json',{'endpoints':result,'actual_native_same_net_barrels':native,'only_unaccepted_new_signal_UUIDs_withdrawn_for_component_census':sorted(new),'all_original_current_signal_items':original})
 cp=out/'census-components-only-NOT_ACCEPTED_MODEL.pkl';cp.write_bytes(pickle.dumps(cache,protocol=5))
 receipt={'verdict':'READ_ONLY_NATIVE_SAME_NET_PORT_AND_TARGET_COMPONENT_CENSUS','actual_exact_raw_NET':raw,'current_model_sha256':sha(mp),'original_native_parent_sha256':sha(sp),'native_same_net_barrel_count':len(native),'signal_original_component_count':len(groups),'source_target_same_original_component':any(set(endpoints.values())<={r['uuid']for r in xs if r['kind']=='pad'}for xs in groups),'only_unaccepted_new_signal_items_count':len(new),'component_cache_SHA256':sha(cp),'native_jobs':0,'source_board_project_model_written':False,'adopted':False,'original_source_current_contact_reference_NATIVE_SI_gates':'OPEN; census only','input_SHA256':{str(f.resolve()):sha(f)for f in(Path(__file__),mp,sp)},'output_SHA256':{str(f.resolve()):sha(f)for f in out.iterdir()if f.is_file()},'elapsed_seconds':time.monotonic()-st}
 put(out/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
