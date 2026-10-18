"""Prepare an additive version; the failed r04 evidence remains unchanged."""
from pathlib import Path
old=Path('reports/motherboard-return-zoning-20261001/build-motor-bank-A-logic-reference-collars-r04.py')
new=old.with_name(old.name.replace('r04.py','r05.py'))
if new.exists():raise ValueError('Immutable report tool already exists')
s=old.read_text()
s=s.replace('import sys,json,shutil,subprocess','import sys,json,shutil,subprocess,argparse')
start=s.index("base=Path('reports/motherboard-power-entry")
stop=s.index("source=Path('hardware/motherboard')",start)
s=s[:start]+'''parser=argparse.ArgumentParser()
parser.add_argument('--base',type=Path,required=True)
parser.add_argument('--manifest',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args();base=args.base;manifest=args.manifest;out=args.out
power=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-eight-LED-power-classification-r02/classification.json')
original_roles=Path('reports/motherboard-power-entry-20261001/motor-bank-A-reference-ready-r121/actual-control-segment-manifest.json')
'''+s[stop:]
s=s.replace("manifest,power,source/'design.json'","manifest,power,original_roles,source/'design.json'")
old_check="if len(rows)!=82 or len(data['logical_original_control_roles'])!=18 or not data['all_five_source_ground_stitches_native_connected']:raise ValueError('Exact82 segments/18 roles/5 actual Ground witnesses required')"
new_check="""expected={(r['role'],r['net'])for r in json.loads(original_roles.read_text())['logical_original_control_roles']}
actual_roles={(r['role'],r['net'])for r in data['logical_original_control_roles']}
if actual_roles!=expected or len(actual_roles)!=18 or len(data['logical_original_control_roles'])!=18 or not data['all_five_source_ground_stitches_native_connected']:raise ValueError('Exact18 original control roles and5 actual Ground witnesses required')
if len(rows)<18 or len({r['actual_copper_UUIDs'][0]for r in rows})!=len(rows):raise ValueError('Exact unique native physical control segments required')
if {r['net']for r in rows}!={net for role,net in expected}:raise ValueError('A required logical control net was dropped or an unrelated net was added')"""
if old_check not in s:raise ValueError('Frozen r04 bounded role check drift')
s=s.replace(old_check,new_check)
s=s.replace('exact82_actual_control_segments=rows','exact_actual_control_segments=rows')
s=s.replace('actual82-control-segment-reference-reviews.json','actual-control-segment-reference-reviews.json')
s=s.replace('Exact82 actual control-segment/18-role','Exact manifest actual control-segment/18-role')
s=s.replace("print('Exact82 segments reviewed; strict failures'","print('Exact manifest segments reviewed',len(rows),'strict failures'")
new.write_text(s)
print(new)
