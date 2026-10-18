"""Exercise exact frozen native replacement rows and reject coordinate drift."""
import copy,hashlib,json
from pathlib import Path
import native_pose_signal_contract as NC
import native_same_uuid_cu_contract_r1 as CR
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=H/'sbc-native-contract-r1/copy/board.kicad_pcb'
assert sha(p)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
rp=H/'sbc-power/u19008-existing-native-copper-adapter-r99/replacement-only-recipe.json'
assert sha(rp)=='4fbf5b6d239b6308a757bc5298485688cb1726b4ba43217d723a6552aa066d03'
rows=json.loads(rp.read_bytes())['replacement_rows'];inv=NC.C.inventory(p.read_bytes())
replacements,pins,flashes=CR.collect(rows,inv)
assert len(replacements)==2 and len(flashes)==1
tests=[]
for field in ('native_position_1nm_drift','undeclared_padstack_size','missing_second_owned_record'):
 rs=copy.deepcopy(rows)
 if field=='native_position_1nm_drift':rs[0]['expected_replacement_geometry']['x']+=.000001
 elif field=='undeclared_padstack_size':rs[0]['expected_replacement_geometry']['d']=.6
 else:rs=rs[:1]
 try:CR.collect(rs,inv)
 except AssertionError:tests.append({'negative':field,'rejected':True})
 else:raise ValueError('Negative contract accepted: '+field)
out=H/'native-same-UUID-Cu-contract-independent-r1.json';assert not out.exists()
r={'verdict':'PASS_EXACT_NATIVE_TWO_SAME_UUID_U19008_NEIGHBOUR_CHANGES_CONTRACT_ONLY','parent_native_sha256':sha(p),'replacement_adapter_sha256':sha(rp),'exact_two_replacement_UUIDs':sorted(replacements),'required_actual_fresh_fill_via_obligations':flashes,'positive_byte_AST_geometry_authorizer_inventory_contract':True,'negative_tests':tests,'input_pins':{str(p.resolve()):sha(p),str(rp.resolve()):sha(rp),str(Path(CR.__file__).resolve()):sha(CR.__file__),**pins},'native_API_refill_contact_current_DRC':'OPEN','native_jobs':0,'board_written':False,'adopted':False}
out.write_text(json.dumps(r,indent=1)+'\n');print(json.dumps({'verdict':r['verdict'],'receipt_sha256':sha(out)}))
