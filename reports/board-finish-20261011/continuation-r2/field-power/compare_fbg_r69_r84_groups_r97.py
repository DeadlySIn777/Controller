import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json
from pathlib import Path
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;O=H/'fbg-r69-to-r84-source-census-r97';N='/motherboard_do/FIELD_B_0V'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();ap=H.parent/'sbc-power/core-pocket-outward-round-guards-r69/model.pkl';bp=H/'c-u19008-actual-regulated-search-base-r84/model.pkl';ag,ah,ab,az,aa=pickle.loads(ap.read_bytes());bg,bh,bb,bz,ba=pickle.loads(bp.read_bytes());ga=F.graph(aa,N);print('R97 baseline groups',len(ga),flush=True);gb=F.graph(ba,N);print('R97 new groups',len(gb),flush=True)
 def key(q):return (q['kind'],q['uuid'],q['layer'])
 def root(gs):return next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs))
 ai=root(ga);bi=root(gb);newkeys={key(q):i for i,xs in enumerate(gb) for q in xs if q['kind']!='fill'};oldrows=[]
 for i,xs in enumerate(ga):
  pads=[q for q in xs if q['kind']=='pad' and q['pin']];physical=[q for q in xs if q['kind']!='fill'];dest={newkeys[key(q)] for q in physical if key(q) in newkeys};unmapped=[C.identity(q) for q in physical if key(q) not in newkeys];oldrows.append({'R69_group':i,'R69_source_group':i==ai,'named_pad_UUIDs':sorted({q['uuid'] for q in pads}),'named_pad_refs':sorted({q['ref']+'.'+q['pin'] for q in pads}),'physical_contact_records':len(physical),'R84_groups':sorted(dest),'all_retained_physical_contacts_in_J11005_source':dest=={bi} and not unmapped,'R84_unmapped_old_records':unmapped})
 census=[{'group':i,'source_rooted':i==bi,'physical_contact_records':len([q for q in xs if q['kind']!='fill']),'named_pad_UUIDs':sorted({q['uuid'] for q in xs if q['kind']=='pad' and q['pin']}),'named_pad_refs':sorted({q['ref']+'.'+q['pin'] for q in xs if q['kind']=='pad' and q['pin']})} for i,xs in enumerate(gb) if any(q['kind']=='pad' and q['pin'] for q in xs)]
 (O/'groups.pkl').write_bytes(pickle.dumps({'R69':ga,'R84':gb},protocol=5));write(O/'per-R69-group.json',oldrows);write(O/'R84-named-source-census.json',census);r={'verdict':'EXACT_HOST_FBG_GROUP_SOURCE_MAPPING_NOT_NATIVE_CURRENT_OR_ALL_NEW_REFERENCE_PROOF','R69_model_sha256':sha(ap),'R84_model_sha256':sha(bp),'R69_source_group':ai,'R84_source_group':bi,'R69_named_groups':len([r for r in oldrows if r['named_pad_UUIDs']]),'R84_named_groups':len(census),'R84_source_named_physical_pads':len(census[bi]['named_pad_UUIDs']) if bi<len(census) and census[bi]['group']==bi else len({q['uuid'] for q in gb[bi] if q['kind']=='pad' and q['pin']}),'R84_unrooted_named_groups':len([r for r in census if not r['source_rooted']]),'all_R69_unrooted_named_groups_now_rooted':all(r['all_retained_physical_contacts_in_J11005_source'] for r in oldrows if r['named_pad_UUIDs'] and not r['R69_source_group']),'per_R69_group_sha256':sha(O/'per-R69-group.json'),'R84_census_sha256':sha(O/'R84-named-source-census.json'),'full_guarded_joint_rebase_native_current_gates':'OPEN','board_written':False};write(O/'receipt.json',r);print(json.dumps(r,indent=1),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
