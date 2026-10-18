"""Reuse exact R170 masks, expand local signal sites and actual retained returns.

No mask/grid weakening: nomination varies only unaccepted new DIC copper.
"""
import sys,json,pickle,time,math
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in (H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import guarded_power_projection_r44 as Z
import construct_di6_direct_source_escape_r5 as K
import construct_DIC_three_track_coupled_r164 as B
from shapely.geometry import Point
C=A.C;NET=B.NET;GND=B.GND

def main():
 started=time.monotonic();out=H/'DIC-expanded-real-return-site-nomination-r172.json';assert not out.exists();A.read(__file__);rp=H/'DIC-neighbour-safe-site-nomination-r170.json';r=json.loads(A.read(rp));raw=A.read(r['model_file']);assert C.sha(raw)==r['model_sha256'];saved=pickle.loads(raw);cur=saved['current'];h=saved['h_without_owned3_with_R164_CS_RSP'];root,refs,_=B.refs_for(cur['after']);insets={l:sh.buffer(-.075,quad_segs=128) for l,sh in refs.items()};rootlayers={(q['uuid'],q['layer']) for q in root if q['kind']=='via'};oldreturns=[]
 for v in h['vias']:
  if L.norm(v['net'])!=GND or not all((v['uuid'],l) in rootlayers for l in refs):continue
  p=Point(v['x'],v['y'])
  if p.distance(saved['regions'][NET])>1.1:continue
  assert all(l in v['flashed'] for l in refs);ann=p.buffer(v['d']/2,quad_segs=128).difference(p.buffer(v['drill']/2,quad_segs=128));contacts={l:ann.intersection(sh).area for l,sh in insets.items()}
  if all(a>.004 for a in contacts.values()):oldreturns.append({'return':[v['x'],v['y']],'return_new':False,'old_return_UUID':v['uuid'],'diameter_drill_mm':[v['d'],v['drill']],'actual_flash_layers':v['flashed'],'actual_source_interior_annulus_mm2':contacts})
 print('DIC_R172_FINITE_REAL_RETAINED_RETURNS',len(oldreturns),flush=True);rows=[]
 for kind,marker,radius in (('source',[127.057072,98.292323],3.0),('target',[130.775665,90.219031],1.5)):
  local=saved['regions'][NET].intersection(Point(marker).buffer(radius,quad_segs=128));opts=[]
  for s in K.sites(local,marker,96):
   at=[round(v,6) for v in s['at_mm']];pt=Point(at)
   if not local.covers(pt):continue
   pairs=[{**p,'distance_mm':math.dist(at,p['return'])} for p in oldreturns if .815<=math.dist(at,p['return'])<=.98]
   returns=saved['regions'][GND].intersection(pt.buffer(.98,quad_segs=128).difference(pt.buffer(.825,quad_segs=128)))
   for rs in K.sites(returns,marker,12):
    ret=[round(v,6) for v in rs['at_mm']];p=Point(ret)
    if not returns.covers(p):continue
    ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));contacts={l:ann.intersection(sh).area for l,sh in insets.items()}
    if all(a>.004 for a in contacts.values()):pairs.append({'return':ret,'return_new':True,'old_return_UUID':None,'diameter_drill_mm':[.5,.2],'distance_mm':math.dist(at,ret),'actual_source_interior_annulus_mm2':contacts})
   if pairs:opts.append({'signal':at,'distance_from_R164_mm':math.dist(at,marker),'pairs':pairs})
  rows.append({'kind':kind,'expanded_radius_mm_nomination_only':radius,'local_signal_region_mm2':local.area,'options':opts});print('DIC_R172_EXPANDED_OPTIONS',kind,len(opts),flush=True)
 result={'verdict':'DIC_EXACT_EXPANDED_SIGNAL_REAL_RETURN_NOMINATION_OPEN' if all(q['options'] for q in rows) else'DIC_EXACT_EXPANDED_SIGNAL_REAL_RETURN_NOMINATION_INCOMPLETE','R170_receipt_sha256':C.sha(A.read(rp)),'exact_old_reference_and_all6_regions_unchanged':True,'source_model_sha256':r['model_sha256'],'ordinary_SMD_every_hole_pitch_masks_unchanged':True,'finite_retained_GND_returns':oldreturns,'nominations':rows,'full_candidate_old_new_contact_reference_source_current_native_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':result['verdict'],'options':[len(q['options']) for q in rows]}),flush=True)
if __name__=='__main__':main()
