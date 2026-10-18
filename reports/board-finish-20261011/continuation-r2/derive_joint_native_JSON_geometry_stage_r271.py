"""Select only native scalar Cu geometry; retain the R268 partial clone."""
from pathlib import Path
import hashlib,json,runpy
H=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();src=H/'stage_joint_native_sparse_R157_clone_r268.py';code=src.read_text()
needle="newcu.append({**pa,'uuid':uid,'raw_net':atom(parse(ch.decode()),'net'),'locked':row['locked_yes']})";assert code.count(needle)==1
replace="curow={k:pa[k]for k in (('kind','net','layer','w','a','b')if pa['kind']=='segment'else('kind','net','at','d','drill'))};newcu.append({**curow,'uuid':uid,'raw_net':atom(parse(ch.decode()),'net'),'locked':row['locked_yes']})"
code=code.replace(needle,replace).replace('clone-r268','clone-r271').replace('R268','R271');target=H/'stage_joint_native_sparse_scalar_clone_r271.py';assert not target.exists();compile(code,str(target),'exec');target.write_text(code)
receipt=H/'joint-native-scalar-input-derivation-r271.json';assert not receipt.exists();receipt.write_text(json.dumps({'source_SHA256':sha(src),'derived_SHA256':sha(target),'R268_partial_native_clone_and_R270_bad_intake_log_retained':True,'only_JSON_payload_geometry_selected_without_host_Polygon_objects':True,'native_or_board_geometry_changed_by_correction':False},indent=1)+'\n');runpy.run_path(str(target),run_name='__main__')
src2=H/'run_joint_native_API_main_slot_r270.py';c=src2.read_text().replace('clone-r268','clone-r271').replace('receipt-r270','receipt-r272').replace('R270','R272');needle="assert not log.exists()";assert c.count(needle)==1;c=c.replace(needle,needle+";assert spec.is_file()and board.is_file()")
target2=H/'run_joint_native_API_main_slot_r272.py';assert not target2.exists();compile(c,str(target2),'exec');target2.write_text(c)
