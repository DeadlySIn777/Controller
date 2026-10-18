"""Fix only R126's new-only nominal/outward shape interface, preserve failure."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_DI13_coupled_reference_r126.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r126','r128').replace('R126','R128')
old="legal,maskledger=newzonelegal(hbase,cur,win,removed);assert legal.covers(island);_,oldgroups"
new="legal,maskledger=newzonelegal(hbase,cur,win,removed);original_new_island=island;island=island.intersection(legal);new_only_outward_trim={'original_R94_WKB_sha256':C.sha(original_new_island.wkb),'outward_trimmed_WKB_sha256':C.sha(island.wkb),'removed_new_only_mm2':original_new_island.difference(island).area,'original_native_or_power_Cu_trimmed':0};assert not island.is_empty and legal.covers(island);_,oldgroups"
assert old in s;s=s.replace(old,new).replace("'R94_exact_central_new_only_piece_sha256':C.sha(island.wkb)","'R94_exact_central_new_only_piece_sha256':C.sha(original_new_island.wkb),'new_only_outward_margin_correction':new_only_outward_trim")
dst=H/'construct_DI15_DI13_coupled_reference_r128.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI15-DI13-outward-r128.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Trim only new unaccepted R94 ground nominee to fresh conservative outward-mask legal region, exact area/hash ledger. No old/source/power trim; full body/reference/contact predicates remain strict. Preserve R126 early assertion failure and launcher.'},indent=1)+'\n');print(sha(dst.read_bytes()))
