"""Correct only the 18 owned R41 meshes on the frozen guarded R47 base.

No original zone definition is changed; no overlap is accepted as capacity.
The exact clipped meshes and subsequent true source census are preserved.
"""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,sys
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
import fast_contacts as F
from regulated_outer_joins_r51 import PORTS
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=HERE/'regulated-guarded-composition-r60'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir()
 bp=HERE.parent/'sbc-power/io3-u15-logic-guarded-model-r47';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'model.pkl')=='14b850b408e536d6fb19ee72efc87a1840f97aca7392f2497a17cc63355eea61';g,h,binding,zones,prior=pickle.loads((bp/'model.pkl').read_bytes())
 rp=HERE/'regulated-field-source-feeds-r41';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'proposed-discrete.pkl')==rr['proposed_discrete_sha256'];d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());assert sha(rp/'proposed-zones.pkl')==rr['proposed_zones_sha256'];owned=pickle.loads((rp/'proposed-zones.pkl').read_bytes());assert not {q['uuid'] for q in d['vias']} & {q['uuid'] for q in h['vias']};h={**h,'vias':h['vias']+d['vias'],'tracks':h['tracks']+d['tracks']};rec,trees=F.build({**h,'zones':[]});updated=[];ledger=[]
 for z in owned:
  cuts=[];cutrows=[];dom=h['domains_normalized'][C.norm(z['net'])];outline=z.get('zone_outline_shape',z['shape'])
  for i in trees[z['layer']].query(outline.buffer(.627),predicate='intersects'):
   q=rec[z['layer']][int(i)]
   if q['net']==z['net']:continue
   dist=(.15 if q['domain']==dom else .6)+.025;cut=P.bounded_buffer(q['shape'],dist);cuts.append(cut);cutrows.append({'kind':q['kind'],'uuid':q['uuid'],'raw_net':q['net'],'required_mm':dist,'cutter_sha256':P.digest(cut)})
  for q in zones+owned:
   if q['layer']!=z['layer'] or q['net']==z['net'] or q['shape'].distance(outline)>.627:continue
   dist=(.15 if h['domains_normalized'].get(C.norm(q['net']))==dom else .6)+.025;cut=P.bounded_buffer(q['shape'],dist);cuts.append(cut);cutrows.append({'kind':'proposal','uuid':q['uuid'],'raw_net':q['net'],'required_mm':dist,'cutter_sha256':P.digest(cut)})
  cutter=unary_union(cuts);body=set_precision(set_precision(z['shape'],1e-6).difference(cutter),1e-6);newoutline=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6);q={**z,'shape':body,'zone_outline_shape':newoutline,'R41_outward_and_later_CORE_corrected':True};updated.append(q)
  removed=z['shape'].difference(body);added=body.difference(z['shape']);rf=OUT/(z['uuid']+'.removed.wkb');af=OUT/(z['uuid']+'.quantization-added.wkb');rf.write_bytes(removed.wkb);af.write_bytes(added.wkb);ledger.append({'uuid':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'old_physical_sha256':P.digest(z['shape']),'new_physical_sha256':P.digest(body),'old_intended_sha256':P.digest(outline),'new_intended_sha256':P.digest(newoutline),'removed_area_mm2':removed.area,'positive_quantization_area_mm2':added.area,'removed_file_sha256':sha(rf),'added_file_sha256':sha(af),'cutters':cutrows})
 print('owned18 clipped, normalize all proposed via guards',flush=True)
 allzones,guards=P.normalize_owned_via_guards(h,zones+updated);print('guarded full oldfill projection',len(allzones),flush=True);after,retreats=P.projected(g,h,allzones);newids={q['uuid'] for q in updated};updated=[q for q in allzones if q['uuid'] in newids];census=[];groups={}
 for bank,net,ref,pin,policy in PORTS:
  gs=F.graph(after,net);groups[net]=gs;ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));row={'bank':bank,'net':net,'actual_source':ref+'.'+pin,'source_group':ri,'source_named_pad_count':len({q['uuid'] for q in gs[ri] if q['kind']=='pad' and q['pin']}),'remaining':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]};census.append(row);write(OUT/'source-census-checkpoint.json',census);print(bank,'remaining',len(row['remaining']),flush=True)
 (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(updated,protocol=5));(OUT/'all-zones.pkl').write_bytes(pickle.dumps(allzones,protocol=5));(OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,allzones,after),protocol=5));(OUT/'source-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));write(OUT/'owned18-shape-delta-ledger.json',ledger);write(OUT/'all-new-via-outward-guard-ledger.json',guards);write(OUT/'all-oldfill-outward-retreat-ledger.json',retreats)
 receipt={'verdict':'SCOPED_R41_OUTWARD_CORRECTION_COMPOSED_SOURCE_REPAIR_AND_FULL_CONTACT_REQUIRED','source_census':census,'new_vias':0,'new_tracks':0,'retained_R41_vias':20,'retained_R41_stubs':20,'owned_R41_meshes':18,'model_sha256':sha(OUT/'model.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'all_zones_sha256':sha(OUT/'all-zones.pkl'),'source_groups_sha256':sha(OUT/'source-groups.pkl'),'R47_receipt_sha256':sha(bp/'receipt.json'),'R47_model_sha256':sha(bp/'model.pkl'),'R41_receipt_sha256':sha(rp/'receipt.json'),'guarded_helper_sha256':sha(HERE.parent/'sbc-power/guarded_power_projection_r44.py'),'owned18_ledger_sha256':sha(OUT/'owned18-shape-delta-ledger.json'),'all_new_via_ledger_sha256':sha(OUT/'all-new-via-outward-guard-ledger.json'),'all_oldfill_retreat_ledger_sha256':sha(OUT/'all-oldfill-outward-retreat-ledger.json'),'original_native_definitions_untouched':True,'protected_R9_and_C10036_joint_reference_bridge_not_yet_composed':True,'full_current_control_rate_and_outputs_unchanged':True,'native_jobs':0,'board_written':False,'mutual_aperture_all_reference_old_relationships_ground_source_native_current_gates':'OPEN'};write(OUT/'receipt.json',receipt);print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
