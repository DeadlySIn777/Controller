"""Distinguish actual native DRU prefix from explicit planning-reserve suffix."""
import json,hashlib
from pathlib import Path
from inventory import sha
H=Path(__file__).resolve().parent;R=H.parent.parent;O=H/'moved-supply-escape-rule-native-prefix-r126'
def digest(x):return hashlib.sha256(x).hexdigest()
def main():
 assert not O.exists();O.mkdir();native=H/'combined-power-source-r3-hierarchy/source/motherboard.kicad_dru';assert sha(native)=='159c4614968368a7d88946cc71cc341f886fd22b356ced1d0738252dbeb65fe4';old=R/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru';adapter=H/'moved-supply-escape-rule-adapter-r122';recipe=json.loads((adapter/'owned-rule-replacement-recipe.json').read_text());assert sha(old)==recipe['original_sha256'];proposal=Path(recipe['proposed_file']);assert sha(proposal)==recipe['proposed_sha256'];n=native.read_bytes();a=old.read_bytes();b=proposal.read_bytes();assert a.startswith(n) and b.startswith(n)
 suffix=a[len(n):];new=b[len(n):];assert suffix.count(b'(rule "RESERVE_KEEPOUT_')==217 and new.count(b'(rule "RESERVE_KEEPOUT_')==217
 for row in recipe['operations']:
  before=row['before_text'].encode();after=row['after_text'].encode();assert before not in n and after not in n and suffix.count(before)==1 and new.count(after)==1;new=new.replace(after,before)
 assert new==suffix
 (O/'planning-reservation-suffix-before.dru').write_bytes(suffix);(O/'source-synchronized-reservation-suffix-after.dru').write_bytes(b[len(n):])
 receipt={'verdict':'PASS_NATIVE_PREFIX_AND_DECLARED_SUFFIX_PROVENANCE_ONLY','actual_native_DRU_file':str(native.resolve()),'actual_native_DRU_sha256':sha(native),'planning_expanded_DRU_sha256':sha(old),'R122_adapter_recipe_sha256':sha(adapter/'owned-rule-replacement-recipe.json'),'R122_receipt_sha256':sha(adapter/'receipt.json'),'source_synchronized_expanded_DRU_sha256':sha(proposal),'actual_native_prefix_bytes_exact_unchanged':True,'existing_native_rules_replaced':0,'declared_appended_reservation_rules':217,'only_three_appended_reservation_rules_change':True,'all_other_suffix_bytes_exact_unchanged':True,'before_suffix_sha256':digest(suffix),'after_suffix_sha256':sha(O/'source-synchronized-reservation-suffix-after.dru'),'native_integration_requirement':'Bind native area-addition recipe plus explicit217-rule suffix and its three source-synchronized rules; R122 is not a replacement of three rules already present in native159c.','native_rule_area_parse_source_ALLseverity_reference_current_gates':'OPEN','board_written':False,'native_jobs':0};(O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print('R126',sha(O/'receipt.json'))
if __name__=='__main__':main()
