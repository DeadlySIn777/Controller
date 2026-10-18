"""Actual old port Cu contacts and ordinary two-source-plane return census."""
import json,pickle,hashlib,sys,time
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
O=H/'sbc-power/CM79-R371-two-original-IO3-terminal-incoming-Cu-two-plane-return-attribution-r374'
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());groups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());lg=K.root(groups['/LOGIC_GND'],'J11001','2');io=K.root(groups['/IO_3V3'],'R18001','2');refs={ly:unary_union([r['shape']for r in lg if r['kind']=='fill'and r['layer']==ly])for ly in ('In1.Cu','In4.Cu')};nom=json.loads((H/'sbc-power/CM79-R353-IO3-existing-actual-annulus-no-hole-fixed-Cu-bypass-nomination-r366/receipt.json').read_text())['winner'];newids={t['uuid']for t in nom['only_new_tracks']};rows=[]
 for which in ('source_existing_annulus','detached_existing_annulus'):
  p=nom[which];vid=p['UUID'];incoming=[];ann={ly:unary_union([r['shape']for r in io if r['kind']=='via'and r['uuid']==vid and r['layer']==ly])for ly in K.LAYERS}
  for ly,ash in ann.items():
   if ash.is_empty:continue
   for rr in io:
    if rr['layer']!=ly or rr['kind']=='via'or rr['uuid']in newids:continue
    overlap=rr['shape'].intersection(ash)
    if not overlap.is_empty:incoming.append({'UUID':rr['uuid'],'kind':rr['kind'],'layer':ly,'actual_drilled_annulus_contact_mm2':overlap.area,'actual_contact_type':overlap.geom_type,'shape_WKB_sha256':hashlib.sha256(rr['shape'].wkb).hexdigest()})
  returns=[]
  for v in h['vias']:
   if L.norm(v['net'])!='/LOGIC_GND':continue
   dist=Point(v['x'],v['y']).distance(Point(p['x'],p['y']))
   if not .9<=dist<=1.:continue
   aa={ly:unary_union([rr['shape']for rr in lg if rr['kind']=='via'and rr['uuid']==v['uuid']and rr['layer']==ly])for ly in refs};areas={ly:aa[ly].intersection(refs[ly]).area for ly in refs}
   returns.append({'UUID':v['uuid'],'xy':[v['x'],v['y']],'ordinary_center_distance_mm':dist,'actual_both_source_plane_annulus_overlap_mm2':areas,'both_source_plane_positive':all(a>0 for a in areas.values()),'all_native_old_mask_and_flags_exact':True})
  rows.append({'terminal':which,'original_IO3_UUID':vid,'xy':[p['x'],p['y']],'actual_incoming_original_Cu_contacts':incoming,'ordinary_actual_LG_return_pair_candidates':returns,'source_planes_handoff_or_same_plane_finite_transfer':'OPEN','no_power_D4_or_larger_owncap_grant':True})
 put(O/'actual-old-incoming-contact-and-ordinary-return-source-attribution.json',rows);put(O/'receipt.json',{'verdict':'ORIGINAL_IO3_TERMINALS_ACTUAL_CU_AND_SOURCE_RETURN_ATTRIBUTION_ONLY','current_R371_model_sha256':sha(D/'model.pkl'),'source_R369_actual_group_cache_sha256':sha(R/'fresh-actual-drilled-changed-source-groups.pkl'),'two_terminal_rows':2,'both_source_plane_ordinary_return_pair_counts':[sum(v['both_source_plane_positive']for v in r['ordinary_actual_LG_return_pair_candidates'])for r in rows],'original_incoming_contact_layers':[sorted(set(v['layer']for v in r['actual_incoming_original_Cu_contacts']))for r in rows],'geometry_mask_source_native_profile_changes':0,'finite_transfer_signed_loop_native_current_thermal':'OPEN','elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R374',sha(O/'receipt.json'),json.dumps(rows),flush=True)
if __name__=='__main__':main()
