"""Locate actual remaining old logic-reference loss after the four-pad bridge."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import audit_aux_exact_raw as A
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def root(groups):return next(xs for xs in groups if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11001','2')for q in xs))
def main():
 out=H/'SAFE-remaining-logic-reference-diagnosis-r59';assert not out.exists();out.mkdir()
 mp=H/'SAFE-logic-four-return-restoration-r55/model.pkl';assert sha(mp)=='5499e67855ab47dcf207a3421c5bb630b56af52031e06c90e270312baf03232b'
 bg=H/'logic-two-independent-full-r43/groups.pkl';ng=H/'SAFE-logic-four-independent-full-r57/groups.pkl'
 audit=H/'SAFE-logic-four-independent-full-r57/receipt.json';assert sha(audit)=='203e598c36adb975374b393929fcb26e40a42315a3eb35eb80a46e967e5b6f52'
 old,h,b,z,current=pickle.loads(mp.read_bytes());before=pickle.loads(bg.read_bytes())['/LOGIC_GND'];after=pickle.loads(ng.read_bytes())['/LOGIC_GND'];br=root(before);nr=root(after)
 layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'}
 bf={l:unary_union([q['shape']for q in br if q['kind']=='fill'and q['layer']==inner])for l,inner in layers.items()}
 nf={l:unary_union([q['shape']for q in nr if q['kind']=='fill'and q['layer']==inner])for l,inner in layers.items()}
 allafter={l:unary_union([q['shape']for xs in after for q in xs if q['kind']=='fill'and q['layer']==inner])for l,inner in layers.items()}
 rr=json.loads((audit.parent/'reference-checkpoint.json').read_bytes());losses=next(q['retained_outer_reference_losses']for q in rr if q['net']=='/LOGIC_GND');tracks={t['uuid']:t for t in h['tracks']};rows=[]
 for row in sorted(losses,key=lambda q:q['prior_source_reference_lost_mm2'],reverse=True):
  t=tracks[row['uuid']];l=t['layer'];inner=layers[l];body=A.shape({'kind':'segment',**t});loss=body.intersection(bf[l]).difference(nf[l]);assert abs(loss.area-row['prior_source_reference_lost_mm2'])<1e-9
  filename=out/(row['uuid']+'.wkb');filename.write_bytes(loss.wkb)
  peers=[{'UUID':q['uuid'],'net':q['net'],'overlap_mm2':q['shape'].intersection(loss).area,'gap_mm':q['shape'].distance(loss)}for q in z if q['layer']==inner and C.norm(q['net'])!='/LOGIC_GND'and q['shape'].distance(loss)<.8]
  fragments=[]
  for index,xs in enumerate(after):
   if xs is nr:continue
   shapes=[q['shape']for q in xs if q['kind']=='fill'and q['layer']==inner]
   if not shapes:continue
   fs=unary_union(shapes);overlap=fs.intersection(loss).area
   if overlap>0:fragments.append({'group':index,'overlap_mm2':overlap,'pads':[{'UUID':q['uuid'],'ref':q['ref'],'pin':q['pin']}for q in xs if q['kind']=='pad'],'actual_vias':sorted({q['uuid']for q in xs if q['kind']=='via'})})
  rows.append({**row,'actual_retained_track':t,'bounds_mm':list(loss.bounds),'loss_WKB_sha256':sha(filename),'physically_remaining_but_not_source_rooted_mm2':loss.intersection(allafter[l]).area,'physically_removed_mm2':loss.difference(allafter[l]).area,'nearby_owned_power_planes':peers,'unrooted_actual_LG_fragments':fragments})
 put(out/'receipt.json',{'verdict':'REMAINING_REFERENCE_GEOMETRY_DIAGNOSIS_ONLY_NO_ACCEPTANCE','model_sha256':sha(mp),'audit_sha256':sha(audit),'old_groups_sha256':sha(bg),'new_groups_sha256':sha(ng),'rows':rows,'root_LG_named_pads':len({q['uuid']for q in nr if q['kind']=='pad'and q['pin']}),'native_jobs':0,'adopted':False})
 print('R59_DIAGNOSIS',len(rows),'top10',[(q['actual_retained_track']['net'],q['prior_source_reference_lost_mm2'],q['physically_remaining_but_not_source_rooted_mm2'],q['physically_removed_mm2'],len(q['unrooted_actual_LG_fragments']))for q in rows[:10]],flush=True)
if __name__=='__main__':main()
