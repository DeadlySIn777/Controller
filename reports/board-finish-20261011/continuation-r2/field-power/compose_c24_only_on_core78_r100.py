"""Exact C24-only operations; no U19008 or regulated proposal is included.

Default CORE78 may be replaced only by explicit --core-r91, a separately
frozen removal-only successor. Optional --include-root4 adds its pinned four
hard return proposals without promoting their independent qualification.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy,argparse
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
import fast_contacts as F
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def load_C():
 cp=ROOT/'coupled-recovery/c10036-r25-reference-bridge-recipe-r24.json';assert sha(cp)=='016762020a735b19c932b4f0dc7a1d36b07854844c207f65aba6965caf438f6e';cr=json.loads(cp.read_text());d={'vias':[],'tracks':[]}
 for x in cr['new_items']:
  if x['kind']=='via':d['vias'].append({'uuid':x['uuid'],'net':x['raw_net'],'x':x['at_mm'][0],'y':x['at_mm'][1],'d':x['diameter_mm'],'drill':x['drill_mm'],'flashed':LAYERS,'prospective_not_native':True})
  else:d['tracks'].append({'uuid':x['uuid'],'net':x['raw_net'],'layer':x['layer'],'a':x['a'],'b':x['b'],'w':x['width_mm'],'prospective_not_native':True})
 zp=Path(cr['new_zone_manifest']['prospective_zone_pickle']);assert sha(zp)=='31efc84c7050c348390b36fce6c3c8cfeb683aa6a9a6cd19272ac1eff2bd7496';q=pickle.loads(zp.read_bytes());q=q[0] if isinstance(q,list) else q;q=copy.deepcopy(q);q['clearance_mm']=.25;q['C_exact_frozen_native_recipe_owner']='recover14';return cr,d,q,cp,zp
def main():
 pa=argparse.ArgumentParser();pa.add_argument('--include-root4',action='store_true');pa.add_argument('--core-r91',action='store_true');pa.add_argument('--output',default='c24-only-core78-source-context-r100');args=pa.parse_args();out=(HERE/args.output).resolve();assert out.is_relative_to(ROOT.resolve()) and not out.exists();out.mkdir()
 mp=ROOT/'sbc-power/r17031-translated-source-composition-r78/model.pkl';mh='128a21a83ccc8e1029f4b97e27930f82de743e00ef45fb1fc2041f0967b8a821'
 if args.core_r91:mp=ROOT/'sbc-power/unused-new-core-fragment-removal-r91/model.pkl';mh='1bb0d52095c4f2ad003d0c5934d8e7fca7174c8936af19ae0bbed66021003e09'
 assert sha(mp)==mh;g,h,b,z,_=pickle.loads(mp.read_bytes());z=copy.deepcopy(z);cr,d,cq,cp,zp=load_C();old={t['uuid']:t for t in h['tracks']};remove=set(cr['removed_source_UUIDs']);assert len(remove)==6 and remove<=set(old)
 led=json.loads((ROOT/'coupled-recovery/c10036-native-owned-ledger-r32/receipt.json').read_text());assert sha(ROOT/'coupled-recovery/c10036-native-owned-ledger-r32/receipt.json')=='017fb0ae11976a79059349bcc0364b8ce6cb0547b01ba542fb6a2a681bd76efb'
 for k in ('tracks','vias'):
  assert not({q['uuid'] for q in d[k]} & {q['uuid'] for q in h[k]})
 h={**h,'tracks':[t for t in h['tracks'] if t['uuid'] not in remove]+d['tracks'],'vias':h['vias']+d['vias']};rootspine_hash=None
 if args.include_root4:
  pp=ROOT/'protected-field-return-r4-snapshot-4/proposed-zones.pkl';assert sha(pp)=='213182e7ec8439cccb0087bf99b362e6e149a3f21843d103b7b50ddceb428239';rootspine_hash=sha(pp);sp=pickle.loads(pp.read_bytes());assert not ({q['uuid'] for q in sp}&{q['uuid'] for q in z});z+=sp
 # Replay exact new C copper cutters on actual current peer proposals. Their
 # immutable original recipes remain untouched; every derived cut is recorded.
 clips=[];updated=[]
 for q in z:
  before=q['shape'];outline=q.get('zone_outline_shape',before);cuts=[]
  for t in d['tracks']:
   if t['layer']!=q['layer'] or t['net']==q['net']:continue
   gap=max(.15 if h['domains_normalized'].get(C.norm(t['net']))==h['domains_normalized'].get(C.norm(q['net'])) else .6,float(q.get('clearance_mm',.15)))+.025;cut=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap)
   if cut.intersects(outline):cuts.append(cut)
  if cuts:
   cutter=unary_union(cuts);shape=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);newout=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6);q={**q,'shape':shape,'zone_outline_shape':newout};clips.append({'uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'physical_old_sha256':P.digest(before),'physical_new_sha256':P.digest(shape),'intended_old_sha256':P.digest(outline),'intended_new_sha256':P.digest(newout),'removed_mm2':before.difference(shape).area,'added_quantization_mm2':shape.difference(before).area,'cutter_sha256':P.digest(cutter)})
  updated.append(q)
 z,via_led=P.normalize_owned_via_guards(h,updated);native=cq.get('zone_outline_shape',cq['shape']);holes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64) for v in h['vias'] if v['net']==cq['net'] and Point(v['x'],v['y']).distance(native)<v['drill']/2];cq['zone_outline_shape']=native;cq['shape']=set_precision(native.difference(unary_union(holes)),1e-6);z.append(cq)
 print('R100 project exact C24 only',len(z),'new-zone records',flush=True);after,oldfill=P.projected(g,h,z);groups=F.graph(after,'/motherboard_do/FIELD_B_0V');ri=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));rootids={q['uuid'] for q in groups[ri]};census=[{'group':i,'source_rooted':i==ri,'physical_contacts':len([q for q in xs if q['kind']!='fill']),'named_pad_UUIDs':sorted({q['uuid'] for q in xs if q['kind']=='pad' and q['pin']}),'named_pad_refs':sorted({q['ref']+'.'+q['pin'] for q in xs if q['kind']=='pad' and q['pin']})} for i,xs in enumerate(groups) if any(q['kind']=='pad' and q['pin'] for q in xs)]
 b=copy.deepcopy(b);b['exact_C24_only_owned_delta']={'recipe_sha256':sha(cp),'native_owned_ledger_sha256':'017fb0ae11976a79059349bcc0364b8ce6cb0547b01ba542fb6a2a681bd76efb','native_deletions':sorted(remove),'fixed_C_zone_uuid':cq['uuid'],'native_C_priority_124_evidence_preserved':True,'U19008_or_REG_delta_included':False}
 (out/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(out/'FBG-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));write(out/'owned-C-native-old-deletes.json',[old[u] for u in sorted(remove)]);write(out/'C-track-peer-cut-ledger.json',clips);write(out/'foreign-via-guard-ledger.json',via_led);write(out/'oldfill-retreat-ledger.json',oldfill);write(out/'FBG-source-census.json',census)
 r={'verdict':'C24_ONLY_EXACT_CURRENT_CONTEXT_HOST_SOURCE_GRAPH_NATIVE_CURRENT_AND_ALL_MUTUAL_GATES_OPEN','model_sha256':sha(out/'model.pkl'),'base_CORE_model_sha256':sha(mp),'CORE_r91_explicit_option':args.core_r91,'root_four_spines_sha256':rootspine_hash,'exact_C_recipe_sha256':sha(cp),'exact_C_native_owned_ledger_sha256':'017fb0ae11976a79059349bcc0364b8ce6cb0547b01ba542fb6a2a681bd76efb','exact_C_zone_pickle_sha256':sha(zp),'actual_root':'J11005.2','C10036_pad_source_rooted':next(pad['uuid'] for pad in h['pads'] if pad['ref']=='C10036' and pad['num']=='2') in rootids,'both_new_C_return_vias_source_rooted':all(v['uuid'] in rootids for v in d['vias']),'FBG_unrooted_named_groups':len([q for q in census if not q['source_rooted']]),'FBG_source_named_pad_count':len({q['uuid'] for q in groups[ri] if q['kind']=='pad' and q['pin']}),'FBG_census_sha256':sha(out/'FBG-source-census.json'),'owned_native_deletes_sha256':sha(out/'owned-C-native-old-deletes.json'),'track_peer_cut_sha256':sha(out/'C-track-peer-cut-ledger.json'),'via_guard_sha256':sha(out/'foreign-via-guard-ledger.json'),'oldfill_retreat_sha256':sha(out/'oldfill-retreat-ledger.json'),'U19008_delta_included':False,'REG_delta_included':False,'board_written':False,'native_jobs':0};write(out/'receipt.json',r);print(json.dumps(r,indent=1),sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
