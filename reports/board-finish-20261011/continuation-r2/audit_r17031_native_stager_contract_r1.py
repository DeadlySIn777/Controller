"""Validate frozen R17031 translation rows with the final native stager's exact checker."""
import hashlib,json
from pathlib import Path
import native_pose_signal_contract as NC
import native_translation_owned_contract_r2 as FP
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'sbc-power/r17031-native-translation-contract-r81/receipt.json';assert sha(p)=='56552466229acc8bd0dee88821ec82d8e0a79006f350ecaf47af9118e1d74495'
r=json.loads(p.read_bytes());parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
rows=r['native_existing_owned_footprint_replacement_rows'];replacement,pins,poses,masks=FP.collect(rows,NC.C.inventory(parent.read_bytes()));assert len(replacement)==len(poses)==len(masks)==1
out=H/'r17031-native-stager-contract-r1.json';assert not out.exists();pins.update({str(i.resolve()):sha(i)for i in(Path(__file__),p,parent,Path(FP.__file__))})
out.write_text(json.dumps({'verdict':'PASS_EXACT_R17031_NATIVE_STAGER_TRANSLATION_CONTRACT_API_PENDING','replacement_UUIDs':list(replacement),'pose_rows':len(poses),'exact_pad_and_text_rows':len(masks),'only_root_at_changed_source_local_pad_nets_UUID_geometry_text_courtyard_BOM_exact':True,'inputs':pins,'native_fullboard_API_refill_contact_reference_DRC_current':'OPEN','native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n');print(json.dumps({'verdict':'PASS_EXACT_STAGER_CONTRACT','receipt_sha256':sha(out)}))
