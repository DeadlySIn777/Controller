from pathlib import Path
import sys,json,copy,importlib.util,hashlib
sys.path.insert(0,str(Path('tools').resolve()));from hardware_build_assembly import parse,dump,children,child,value
p=Path('reports/motherboard-critical-routing-20261001/verify_FLASH_MISO_F12_combined_r03.py');spec=importlib.util.spec_from_file_location('miso_compared',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=Path('reports/motherboard-critical-routing-20261001/actual-source26-root83-FPGA-flash-MISO-F-only-r03');diff=json.loads((r/'root84-lexical-differences.json').read_text());assert diff['old_diffs']==0and diff['diffs']==9
positive=[]
for row in diff['differences']:
 if not m.same_literal_new_segment(row['before'],row['after']):raise ValueError('Actual same-number native formatting rejected')
 positive.append(dict(uuid=row['uuid'],exact_decimal_geometry_equal=True,no_tolerance=True))
original=parse(diff['differences'][0]['before']);controls=[]
for label,mut in [('X shifted1nm',lambda t:child(t,'start').__setitem__(1,'94.000001')),('width shifted1nm',lambda t:child(t,'width').__setitem__(1,'0.200001')),('wrong domain',lambda t:child(t,'net').__setitem__(1,'"/FOREIGN_NET"')),('wrong side',lambda t:child(t,'layer').__setitem__(1,'"B.Cu"')),('wrong native UUID',lambda t:child(t,'uuid').__setitem__(1,'"00000000-0000-0000-0000-000000000000"')),('missing width',lambda t:t.remove(child(t,'width'))),('extra unreviewed field',lambda t:t.append(['locked','yes']))]:
 t=copy.deepcopy(original);mut(t)
 if m.same_literal_new_segment(dump(original),dump(t)):raise ValueError('Real scope mutation accepted '+label)
 controls.append(dict(label=label,rejected=True))
(r/'root84-numeric-notation-controls-r01.json').write_text(json.dumps(dict(passed=True,comparator_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actual_nine_native_serialization_positives=positive,all_retained_Cu_raw_unchanged=True,exact_decimal_no_tolerance=True,meaningful_negative_controls=controls),indent=2)+'\n');print('NOTATION_CONTROLS_PASS',len(positive),len(controls))
