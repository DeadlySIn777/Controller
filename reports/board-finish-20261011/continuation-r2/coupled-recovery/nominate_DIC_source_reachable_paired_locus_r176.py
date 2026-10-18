"""Exact source reachable F component intersected with real paired locus.

Reuses frozen ordinary and strict neighbour masks without grid/radius waiver.
"""
import sys,json,pickle,time,math
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import construct_di6_direct_source_escape_r5 as K
import construct_DIC_three_track_coupled_r164 as B
from shapely.geometry import Point,box
from shapely.ops import unary_union
C=A.C;NET=B.NET;GND=B.GND
def main():
 started=time.monotonic();out=H/'DIC-source-reachable-paired-locus-r176.json';assert not out.exists();A.read(__file__);rp=H/'DIC-neighbour-safe-site-nomination-r170.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='94bd456d0c2849dfd3a7bf0df56f9949826c1a8b651da1d3095cc6a51301d769';raw=A.read(r['model_file']);assert C.sha(raw)==r['model_sha256'];d=pickle.loads(raw);cur=d['current'];h=d['h_without_owned3_with_R164_CS_RSP'];r172p=H/'DIC-expanded-real-return-site-nomination-r172.json';r172=json.loads(A.read(r172p));assert C.sha(A.read(r172p))=='f0d7d51bce0d1ab06e99f84fc6c338222dfbee07db7994cfa058d7d5992c3b92';root,refs,_=B.refs_for(cur['after']);insets={l:sh.buffer(-.075,quad_segs=128) for l,sh in refs.items()};win=box(121,86,137,102);attach=[124.381300,96.730773];free=B.physical_centres(h,cur,NET,'F.Cu',win).intersection(refs['In1.Cu'].intersection(win.buffer(1)).buffer(-.105,quad_segs=128));sourceparts=[p for p in K.pieces(free) if p.covers(Point(attach))];assert len(sourceparts)==1;reachable=sourceparts[0];paired_locus=d['regions'][GND].buffer(.98,quad_segs=128).union(unary_union([Point(p['return']).buffer(.98,quad_segs=128) for p in r172['finite_retained_GND_returns']]));legal=d['regions'][NET].intersection(reachable).intersection(paired_locus);print('DIC_R176_SOURCE_REACHABLE_PAIRED_REGION',legal.area,flush=True);options=[]
 for s in K.sites(legal,[127.057072,98.292323],96):
  at=[round(x,6) for x in s['at_mm']];p=Point(at)
  if not legal.covers(p):continue
  pairs=[{**q,'distance_mm':math.dist(at,q['return'])} for q in r172['finite_retained_GND_returns'] if .815<=math.dist(at,q['return'])<=.98];rr=d['regions'][GND].intersection(p.buffer(.98,quad_segs=128).difference(p.buffer(.825,quad_segs=128)))
  for s in K.sites(rr,at,16):
   ret=[round(x,6) for x in s['at_mm']];pt=Point(ret)
   if not rr.covers(pt):continue
   ann=pt.buffer(.25,quad_segs=128).difference(pt.buffer(.1,quad_segs=128));contacts={l:ann.intersection(sh).area for l,sh in insets.items()}
   if all(a>.004 for a in contacts.values()):pairs.append({'return':ret,'return_new':True,'old_return_UUID':None,'diameter_drill_mm':[.5,.2],'distance_mm':math.dist(at,ret),'actual_source_interior_annulus_mm2':contacts})
  if pairs:options.append({'signal':at,'distance_from_R164_mm':math.dist(at,[127.057072,98.292323]),'pairs':pairs})
 mp=H/'DIC-source-reachable-paired-locus-r176-model.pkl';assert not mp.exists();mp.write_bytes(pickle.dumps({'current':cur,'source_reachable_F':reachable,'paired_locus':paired_locus,'source_legal_signal_region':legal,'source_attachment_mm':attach,'options':options},protocol=5));result={'verdict':'DIC_SOURCE_REACHABLE_ORDINARY_PAIRED_LOCUS_POSITIVE_ROUTE_OPEN' if options else'DIC_SOURCE_REACHABLE_ORDINARY_PAIRED_LOCUS_EMPTY_INCOMPLETE','R170_receipt_sha256':C.sha(A.read(rp)),'R172_receipt_sha256':C.sha(A.read(r172p)),'source_attachment_mm':attach,'strict_source_reachable_F_area_mm2':reachable.area,'all_window_reference_safe_source_signal_area_mm2':d['regions'][NET].intersection(reachable).area,'paired_locus_intersection_area_mm2':legal.area,'source_signal_radius_bound_mm':None,'old_reference_masks_and_all6_guards_unchanged':True,'nominations':[{'kind':'source','options':options},next(q for q in r172['nominations'] if q['kind']=='target')],'model_file':str(mp),'model_sha256':C.sha(mp.read_bytes()),'full_constructive_reference_contacts_native_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':result['verdict'],'options':len(options)}),flush=True)
if __name__=='__main__':main()
