"""Read-only source-pad baseline check, reusing the completed actual graph."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import collections,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;sha=N.sha
P=H/'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
OUT=H/'R157-actual-full-nine-source-CPP-versus-drilled-baseline-r773';assert not OUT.exists();OUT.mkdir()
pr=json.loads((P/'prepare-receipt.json').read_bytes());assert sha(P/'prepare-receipt.json')=='23c1b5669b0453132fe6b88ec41dc00cfe6c9ac48613386cbeb29ad149355019'
mf=P/'actual-full-R157-before-model.pkl';gf=P/'actual-full-R157-before-all-net-groups.pkl'
assert sha(mf)==pr['actual_before_model_SHA256']and sha(gf)==pr['actual_before_groups_SHA256']
before=pickle.loads(mf.read_bytes());groups=pickle.loads(gf.read_bytes());pf=N.R157/'partitions.json';cpp=json.loads(pf.read_bytes())
assert cpp['sha256']=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'and cpp['refilled']
counter=collections.Counter();labels={}
for p in before['pads']:
 label=p['ref']+'.'+str(p['num']);i=counter[label];counter[label]+=1;labels[p['uuid']]=label+'#'+str(i)
rows=[]
for net,ref,pin in K.ROOTS:
 raws={p['net']for p in before['pads']if L.norm(p['net'])==net};assert len(raws)==1
 physical=K.root(groups[net],ref,pin);anchor={labels[r['uuid']]for r in physical if r['kind']=='pad'and(r['ref'],str(r['pin']))==(ref,pin)}
 native=[set(xs)for xs in cpp['nets'][next(iter(raws))]if set(xs)&anchor];assert len(native)==1
 wanted={labels[r['uuid']]for r in physical if r['kind']=='pad'};native=native[0]
 rows.append({'net':net,'source':ref+'.'+pin,'drilled_source_named_pad_count':len({r['uuid']for r in physical if r['kind']=='pad'and str(r['pin'])}),
  'drilled_source_layer_key_count':len(K.keys(physical)),'CPP_source_pad_count':len(native),'physical_source_pad_labels':len(wanted),
  'CPP_source_pads_absent_physical':[a for a in sorted(native-wanted)],'physical_source_pads_absent_CPP':[a for a in sorted(wanted-native)]})
fp=OUT/'receipt.json';fp.write_text(json.dumps({'status':'READ_ONLY_ACTUAL_FULL_BEFORE_NINE_SOURCE_CPP_COMPARISON',
 'source_rows':rows,'CPP_vs_drilled_source_disagreement_count':sum(bool(r['CPP_source_pads_absent_physical']or r['physical_source_pads_absent_CPP'])for r in rows),
 'input_SHA256':{str(p):sha(p)for p in (Path(__file__),P/'prepare-receipt.json',mf,gf,pf)},
 'no_graph_rebuild_or_current_or_geometry_or_native_job':True,'all_disagreements_raw_failures_preserved':True,'adopted':False},indent=1)+'\n',encoding='utf-8')
print(json.dumps({'receipt_SHA256':sha(fp),'rows':[{k:v for k,v in r.items()if k not in('CPP_source_pads_absent_physical','physical_source_pads_absent_CPP')}for r in rows],'disagreements':sum(bool(r['CPP_source_pads_absent_physical']or r['physical_source_pads_absent_CPP'])for r in rows)}),flush=True)
