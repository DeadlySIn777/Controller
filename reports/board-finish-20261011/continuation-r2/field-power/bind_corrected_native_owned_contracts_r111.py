"""Add exact canonical ownership adapters without changing electrical geometry."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from inventory import sha
H=Path(__file__).resolve().parent;S=H.parent/'sbc-power';sys.path.insert(0,str(S))
import owned_native_delta_r49 as OWNED
import owned_native_cu_replacements_r100 as CR
import owned_native_footprint_delta_r86 as FP
O=H/'corrected-regulated-native-bound-search-base-r111'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();bp=H/'corrected-regulated-fbg-r10-search-base-r108';assert sha(bp/'model.pkl')=='6ae0fcf2fb8fd9d2551934512108e8394b0758994dcfef9c7b22dfa2134046ef';g,h,b,z,after=pickle.loads((bp/'model.pkl').read_bytes());b=copy.deepcopy(b)
 paths=[(S/'recovery-owned-deletion-adapters-r61/C10036-remove-only-recipe.json','2163b521986042e20bd2d18c6b271d033d8bc17f0a13643eb483837e6dfc50ee'),(S/'u19008-existing-native-copper-adapter-r99/remove-only-recipe.json','fdf39b64b1c7e1977674a1c1e768911eb0b287e2c0d5808712aa501084eeccd7')]
 specs=b.setdefault('existing_native_owned_Cu_removal_recipes',[])
 for p,digest in paths:
  assert sha(p)==digest
  if not any(x['file']==str(p.resolve()) for x in specs):specs.append({'file':str(p.resolve()),'sha256':digest})
 cb=json.loads((S/'cu-replacement-collector-contract-r103/binding-recipe.json').read_text());b['existing_native_owned_Cu_replacement_recipes']=cb['existing_native_owned_Cu_replacement_recipes'];fb=json.loads((S/'r17031-final-emitter-authorization-r88/binding-recipe.json').read_text());b['existing_native_owned_footprint_replacement_recipes']=[fb]
 base=pickle.loads((H/'native-bound-field-base-r5/model.pkl').read_bytes())['discrete'];removed,rs=OWNED.collect(b,base);repls,rmap,crs=CR.collect(b,base,h);fps,pads,frs=FP.collect(b,base,h)
 missing={}
 for kind in ('tracks','vias'):
  oldids={x['uuid'] for x in base[kind]};newids={x['uuid'] for x in h[kind]};lost=oldids-newids;allowed={u for u,r in removed.items() if r['kind']==('segment' if kind=='tracks' else 'via')};assert lost==allowed,('unowned_missing_or_not_applied',kind,lost-allowed,allowed-lost);missing[kind]=sorted(lost)
 assert not set(removed)&set(rmap)
 b['current_U19008_guarded_zone_recipe']={'file':str((H/'u19008-guarded-native-owned-recipe-r110/receipt.json').resolve()),'sha256':sha(H/'u19008-guarded-native-owned-recipe-r110/receipt.json')};b['current_corrected_U19008_scoped_analytic_reference_receipt']={'file':str((H/'u19008-corrected-independent-audit-r109/receipt.json').resolve()),'sha256':sha(H/'u19008-corrected-independent-audit-r109/receipt.json')}
 (O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));write(O/'binding.json',b);write(O/'owned-existing-contract.json',{'exact_missing':missing,'removed':list(removed.values()),'same_UUID_replacement_rows':repls,'existing_FP_rows':fps,'exact_changed_pad_UUIDs':sorted(pads),'canonical_removal_specs':rs,'canonical_Cu_replacement_specs':crs,'canonical_FP_replacement_specs':frs})
 for f in ('source-census.json','source-groups.pkl','owned-regulated-planes.pkl'):(O/f).write_bytes((bp/f).read_bytes())
 write(O/'receipt.json',{'verdict':'CANONICAL_OWNED_ADAPTERS_PASS_GEOMETRY_UNCHANGED_CURRENT_SEARCH_BASE_NOT_ADOPTED','model_sha256':sha(O/'model.pkl'),'previous_R108_model_sha256':sha(bp/'model.pkl'),'existing_contract_sha256':sha(O/'owned-existing-contract.json'),'binding_sha256':sha(O/'binding.json'),'missing_existing_segments':len(missing['tracks']),'missing_existing_vias':len(missing['vias']),'explicit_same_UUID_replacements':len(repls),'changed_FP':len(fps),'geometry_and_projected_fills_exactly_unchanged':True,'source_census_sha256':sha(O/'source-census.json'),'source_groups_sha256':sha(O/'source-groups.pkl'),'owned_REG19_plane_sha256':sha(O/'owned-regulated-planes.pkl'),'all_full_old_source_contact_reference_current_native_gates':'OPEN','native_jobs':0,'board_written':False});print('R111 frozen',sha(O/'model.pkl'),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
