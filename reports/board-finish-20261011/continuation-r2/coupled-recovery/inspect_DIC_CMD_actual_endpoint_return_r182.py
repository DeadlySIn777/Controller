"""Bind actual retained CMD transition and real source-rooted used-layer return.

No generic own-aperture credit, signal-layer addition or board/native writes.
"""
import sys,json,pickle,time,math
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import construct_di6_direct_source_escape_r5 as K
from shapely.geometry import Point
from shapely.ops import unary_union
C=A.C;GND='/LOGIC_GND';CMD='/motherboard_io_control/DIC_IOL1_CMD_BUFFER'
def main():
 started=time.monotonic();out=H/'DIC-CMD-actual-endpoint-return-r182.json';assert not out.exists();A.read(__file__);rp=H/'DIC-neighbour-safe-site-nomination-r170.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='94bd456d0c2849dfd3a7bf0df56f9949826c1a8b651da1d3095cc6a51301d769';raw=A.read(r['model_file']);assert C.sha(raw)==r['model_sha256'];d=pickle.loads(raw);cur=d['current'];h=cur['h'];source=A.read(cur['binding']['exact_native_discrete_board_file']);assert C.sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';inv=C.inventory(source);signal=next(v for v in h['vias'] if v['uuid']=='1f815e33-e973-46e2-833e-96fee8d37fcf');assert L.norm(signal['net'])==CMD and(signal['x'],signal['y'],signal['d'],signal['drill'])==(128.549999,100.55,.6,.3);point=Point(signal['x'],signal['y']);refs={l:unary_union([q['shape'] for q in cur['root'] if q['kind']=='fill' and q['layer']==l]) for l in('In1.Cu','In4.Cu')};insets={l:sh.buffer(-.075,quad_segs=128) for l,sh in refs.items()};rootrows={}
 for q in cur['root']:
  if q['kind'] in('pad','via'):rootrows.setdefault((q['kind'],q['uuid']),[]).append(q)
 existing=[]
 for (kind,uid),rows in rootrows.items():
  if not all(any(q['layer']==l for q in rows) for l in refs):continue
  if kind=='via':
   v=next(v for v in h['vias'] if v['uuid']==uid);at=[v['x'],v['y']];assert L.norm(v['net'])==GND;ann=Point(at).buffer(v['d']/2,quad_segs=128).difference(Point(at).buffer(v['drill']/2,quad_segs=128));meta={'at_mm':at,'diameter_drill_mm':[v['d'],v['drill']],'actual_flash_layers':v['flashed']}
  else:
   p=next(p for p in h['pads'] if p['uuid']==uid)
   if p['smd'] or not p.get('hole'):continue
   # The exact plated pad bodies are already drill-subtracted graph rows.
   sh=unary_union([q['shape'] for q in rows if q['layer']=='In1.Cu']);at=[p['x'],p['y']];ann=sh;meta={'at_mm':at,'ref':p['ref'],'pin':p['num'],'exact_native_plated_pad':True}
  distance=point.distance(Point(at))
  if distance>1:continue
  contacts={l:ann.intersection(sh).area for l,sh in insets.items()};existing.append({'kind':kind,'UUID':uid,**meta,'signal_distance_mm':distance,'actual_J1_rooted_used_layer_finite_interior_mm2':contacts,'qualifies_finite_source_return':all(a>.004 for a in contacts.values())})
 rr=d['regions'][GND].intersection(point.buffer(.98,quad_segs=128).difference(point.buffer(.820,quad_segs=128)));nominees=[]
 for s in K.sites(rr,[signal['x'],signal['y']],32):
  at=[round(x,6) for x in s['at_mm']];p=Point(at)
  if not rr.covers(p):continue
  ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));contacts={l:ann.intersection(sh).area for l,sh in insets.items()}
  if all(a>.004 for a in contacts.values()):nominees.append({'return_at_mm':at,'distance_mm':point.distance(p),'actual_J1_rooted_interior_mm2':contacts,'ordinary_new_diameter_drill_mm':[.5,.2],'mask_reuse':'R170_GND_ALL6_REFERENCE_SAFE_CONSERVATIVE_CMD_STILL_HARD'})
 result={'verdict':'DIC_CMD_ACTUAL_RETAINED_TRANSITION_REAL_RETURN_FOUND_OPEN' if any(q['qualifies_finite_source_return'] for q in existing) else('DIC_CMD_ACTUAL_TRANSITION_NEW_ORDINARY_RETURN_NOMINATED_OPEN' if nominees else'DIC_CMD_ACTUAL_TRANSITION_RETURN_INCOMPLETE'),'source_parent_sha256':C.sha(source),'R170_receipt_sha256':C.sha(A.read(rp)),'actual_signal_via':signal,'actual_native_signal_chunk':inv[3][signal['uuid']].decode(),'actual_native_signal_chunk_sha256':C.sha(inv[3][signal['uuid']]),'used_signal_layers':['F.Cu','B.Cu'],'actual_required_reference_layers':['In1.Cu','In4.Cu'],'unchanged_exact_own_radius_mm':.575,'own_radius_expansion_mm':0,'existing_source_rooted_return_rows':existing,'new_return_region_mm2':rr.area,'new_ordinary_return_nominees':nominees,'full_after_all_new_holes_source_contact_reference_native_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':result['verdict'],'existing':existing,'new_return_options':len(nominees)}),flush=True)
if __name__=='__main__':main()
