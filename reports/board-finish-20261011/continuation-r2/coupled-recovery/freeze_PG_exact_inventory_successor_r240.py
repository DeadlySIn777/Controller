"""Preserve R238 index failure; fix copper-inventory tuple position only."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
s=H/'nominate_U21003_exact_PG_return_detour_r238.py'
d=H/'nominate_U21003_exact_PG_return_detour_r240.py'
o=H/'U21003-exact-PG-single-track-return-nomination-r238'
assert not d.exists() and o.is_dir() and not (o/'failure.json').exists()
(o/'failure.json').write_text(json.dumps({'verdict':'EXACT_NATIVE_INVENTORY_INDEX_ASSERTION_FAILED_BEFORE_GEOMETRY','error':'C.inventory index2 is tail bytes; copper dictionary is index4','script_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'exit_code':1,'no_geometry_acceptance_no_board_native_or_source_change':True,'failed_script_and_launch_preserved':True},indent=1)+'\n')
t=s.read_text().replace('inventory[2]','inventory[4]').replace('nomination-r238','nomination-r240').replace('PG-return-r238:','PG-return-r240:').replace('PG-r238:','PG-r240:')
assert 'inventory[2]'not in t
d.write_text(t);compile(t,str(d),'exec')
print(hashlib.sha256(d.read_bytes()).hexdigest())
