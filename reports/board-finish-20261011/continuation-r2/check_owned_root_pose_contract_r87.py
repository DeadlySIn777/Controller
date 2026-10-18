"""Guard critical native source/pad/mask/pose identity against undeclared or altered replacements."""
import copy,hashlib,json
from pathlib import Path
import native_owned_root_pose_contract_r3 as M
import native_pose_signal_contract as NC
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';inv=NC.C.inventory(parent.read_bytes());rows=M.frozen_rows();assert len(rows)==2;good=M.collect(rows,inv);assert len(good[0])==len(good[2])==len(good[3])==2
tests=[]
def rejected(label,change):
 bad=copy.deepcopy(rows);change(bad)
 try:M.collect(bad,inv)
 except(AssertionError,KeyError,ValueError):tests.append({'case':label,'rejected':True});return
 raise AssertionError('Unauthorized native replacement accepted: '+label)
rejected('undeclared component',lambda r:r[0].update(ref='U11025'))
rejected('changed raw pad net',lambda r:r[0]['native_pose_row']['pads'][0].update(raw_net='/LOGIC_GND'))
rejected('changed physical pad identity',lambda r:r[0]['native_pose_row']['pads'][0].update(pad_uuid=r[0]['native_pose_row']['pads'][1]['pad_uuid']))
rejected('mask drops fitted paste opening',lambda r:r[0]['native_mask_and_text_row']['pads'][0].update(native_declared_layers=['F.Cu','F.Mask']))
rejected('caller shifts pad within old 3um budget',lambda r:r[0]['native_pose_row']['pads'][0]['absolute_center_mm'].__setitem__(0,r[0]['native_pose_row']['pads'][0]['absolute_center_mm'][0]+.002))
rejected('caller changes alarm-preserving root pose',lambda r:r[1].update(replacement_root_pose_mm_deg=[221,42.901,90]))
rejected('changed field angle',lambda r:r[0]['native_mask_and_text_row']['texts'][0].update(native_angle_deg=123))
rejected('duplicate replacement',lambda r:r.append(copy.deepcopy(r[0])))
rejected('caller replaces authorizer',lambda r:r[0].update(authorizing_recipe_file=r[1]['authorizing_recipe_file']))
out=H/'two-rotated-FP-native-collector-contract-r87';assert not out.exists();out.mkdir();(out/'frozen-rotation-rows.json').write_text(json.dumps(rows,indent=1)+'\n');(out/'receipt.json').write_text(json.dumps({'verdict':'PASS_TWO_EXACT_NATIVE_ROOT_ROTATION_COLLECTOR_AND_NINE_NEGATIVE_GUARDS','collector_sha256':sha(M.__file__),'test_sha256':sha(__file__),'parent_native_sha256':sha(parent),'exact_two_FP_replacements':sorted(good[0]),'frozen_rotation_rows_sha256':sha(out/'frozen-rotation-rows.json'),'nine_negative_cases':tests,'original_R17031_translation_delegate_unchanged':True,'wholeboard_old_contact_source_fill_DRC_current_threshold_fault_gates':'OPEN','native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n');assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';print('R87_ROOT_FP_COLLECTOR_PASS',len(tests),sha(out/'receipt.json'))
