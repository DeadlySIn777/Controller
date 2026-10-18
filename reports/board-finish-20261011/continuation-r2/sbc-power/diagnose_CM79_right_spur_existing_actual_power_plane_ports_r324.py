"""Read-only exact source Cu on all layers at the external right power port."""
import hashlib,json,pickle,sys,time
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
O=H/'sbc-power/CM79-right-external-port-all-layer-actual-existing-CORE5-source-Cu-r324'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());nom=H/'sbc-power/CM79-external-full1p25-F-spur-exact-old-Cu-novel-margin-nominations-r323';assert sha(nom/'receipt.json')=='aa45aba75979c06f4ef43932f0ba7fe171808e24443efd609aac7ae90e5e96f0';rows=json.loads((nom/'external-fullwidth-source-spur-search-progress.json').read_text())['accepted']['right'];topo=H/'sbc-power/CM79-original-CORE5-native-alternate-path-no-new-hole-topology-r319';assert sha(topo/'receipt.json')=='8bac0960b658176645c9a33842d26913c266d4fdd1cb9aa1a36ce8676457efc1';pg=pickle.loads((topo/'actual-CORE5-with-only-native-middle-removed-groups.pkl').read_bytes());root=K.root(pg,'R11022','2');cu={ly:[r for r in root if r['layer']==ly]for ly in K.LAYERS};ct={ly:STRtree([r['shape']for r in rs])for ly,rs in cu.items()};holes,ht=K.hole_context(c);answers=[]
 for row in rows:
  xy=row['new_ordinary_power_via_xy_mm'];pt=Point(xy);disk=pt.buffer(.25,quad_segs=128);ann=disk.difference(pt.buffer(.10000002,quad_segs=128));ann=ann.difference(unary_union([holes[int(i)]for i in ht.query(ann,predicate='intersects')]));layers=[]
  for ly,rs in cu.items():
   direct=[]
   for i in ct[ly].query(ann,predicate='intersects'):
    rr=rs[int(i)];touch=ann.intersection(rr['shape'])
    if not touch.is_empty and touch.area>0:direct.append({'actual_rooted_kind':rr['kind'],'actual_rooted_UUID':rr['uuid'],'actual_finite_annulus_contact_mm2':touch.area})
   ni=int(ct[ly].nearest(pt));near=rs[ni];a,bb=nearest_points(pt,near['shape']);layers.append({'layer':ly,'actual_R11022_rooted_power_finite_contacts':direct,'nearest_existing_actual_source_Cu_kind':near['kind'],'nearest_existing_actual_source_Cu_UUID':near['uuid'],'nearest_actual_source_Cu_distance_mm':pt.distance(near['shape']),'nearest_source_point_mm':list(bb.coords[0])})
  answers.append({'external_right_power_via_xy_mm':xy,'all_layer_actual_power_source_rows':layers,'source_connection_without_new_left_power_hole_candidate':any(r['actual_R11022_rooted_power_finite_contacts']for r in layers),'prospective_all6_new_barrel_native_and_current_and_full_body_reference':'OPEN'})
 put(O/'all-eight-right-port-existing-source-all-layer-finite-annuli.json',answers);put(O/'receipt.json',{'verdict':'RIGHT_EXTERNAL_CORE5_BARREL_CAN_DIRECTLY_CONTACT_EXISTING_SOURCE_Cu_DIAGNOSTIC'if any(r['source_connection_without_new_left_power_hole_candidate']for r in answers)else'NO_RIGHT_EXTERNAL_PORT_DIRECT_EXISTING_POWER_SOURCE_ANNULUS_IN_ALL_SIX_LAYERS','exact_failed_R289_model_sha256':sha(mp),'R323_spur_receipt_sha256':sha(nom/'receipt.json'),'R319_source_graph_receipt_sha256':sha(topo/'receipt.json'),'tested_external_right_port_count':len(rows),'direct_actual_source_port_candidates':sum(r['source_connection_without_new_left_power_hole_candidate']for r in answers),'native_mask_current_loadflow_plating_drop_fullnew_reference_allold_source_contacts':'OPEN','model_source_native_board_or_adoption_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R324_COMPLETE',sha(O/'receipt.json'),sum(r['source_connection_without_new_left_power_hole_candidate']for r in answers),flush=True)
if __name__=='__main__':main()
