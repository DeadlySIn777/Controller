"""Allow finite actual annular landing beside surviving ordinary DI13 metal."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_DI13_mirrored_back_replacement_r146.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r146','r148').replace('R146','R148')
old="sourceattach=startmetal.buffer(-.04,quad_segs=128).intersection(ordinary).intersection(Point(start).buffer(15,quad_segs=128))"
new="sourceattach=startmetal.buffer(.240,quad_segs=128).intersection(ordinary).intersection(reference.buffer(-.726,quad_segs=128)).intersection(Point(start).buffer(15,quad_segs=128))"
assert old in s;s=s.replace(old,new)
s=s.replace("r124['best_nominations'][:12]","r124['best_nominations'][:1]")
s=s.replace("'DI13_new_signal_vias']=1","'DI13_new_signal_vias']=1;row['landing_predicate']='Exact .25/.1 annulus must meet surviving In3 metal by >.004mm2; centre need not lie inside the .2mm track. All6 ordinary Cu/SMD/hole/pitch unchanged. Entire existing source plane disk .726 required for nomination.'")
s=s.replace("'max_signal_layer_segments':3","'max_DI15_signal_layer_segments':3,'DI13_new_branch_layers':['In3.Cu','B.Cu'],'full_DI13_original_F_pad_to_F_pad_may_require_F_In3_B_F':'EXPLICIT_ALTERNATIVE_OPEN_PENDING_ACTUAL_RETAINED_GRAPH_AND_STRICT_LAYER_POLICY','strict_saved_router_limit_not_claimed_passed_by_counting_only_new_branch':True")
dst=H/'construct_DI15_DI13_finite_annular_landing_r148.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI13-finite-annular-attachment-r148.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Nominate finite actual annular contact off the current narrow track centre, then require >.004mm2 physical surviving contact and entire .726mm current source In4 disk. All physical/net/reference guards unchanged. Only exact best entry return evaluated; preserve full inherited layer-chain acceptance OPEN.'},indent=1)+'\n');print(sha(dst.read_bytes()))
