"""Exact independent mutual distances of R114 REG and ROOT R18 LG bodies."""
import pickle,json,math
from pathlib import Path
from shapely.geometry import Point,LineString
from inventory import sha
H=Path(__file__).resolve().parent;O=H/'regulated-root-logic-spine-mutual-r118';assert not O.exists();O.mkdir();root=H.parent/'logic-return-r18-snapshot-1';assert sha(root/'proposed-zones.pkl')=='943d222e160f478d8cc351f63489b5b07a4ef380a326e81b8e6f2a6d13a05a42';lg=pickle.loads((root/'proposed-zones.pkl').read_bytes());p=H/'regulated-quantized-inner-source-feeds-r114';r=json.loads((p/'receipt.json').read_text());assert sha(p/'proposed-zones.pkl')==r['proposed_zones_sha256'];regs=pickle.loads((p/'proposed-zones.pkl').read_bytes());d=pickle.loads((p/'proposed-discrete.pkl').read_bytes());fail=[];checks=[]
for q in regs:
 for x in lg:
  if q['layer']!=x['layer']:continue
  req=max(.6,float(q.get('clearance_mm',.15)),float(x.get('clearance_mm',.15)))+.025;gap=q['shape'].distance(x['shape']);row={'REG_uuid':q['uuid'],'ROOT_uuid':x['uuid'],'layer':q['layer'],'analytic_gap_mm':gap,'required_mm':req,'physical_overlap_mm2':q['shape'].intersection(x['shape']).area};checks.append(row)
  if gap<req:fail.append(row)
for kind,items in d.items():
 for q in items:
  for x in lg:
   if kind=='tracks' and q['layer']!=x['layer']:continue
   center=Point(q['x'],q['y']) if kind=='vias' else LineString([q['a'],q['b']]);radius=q['d']/2 if kind=='vias' else q['w']/2;req=max(.6,float(x.get('clearance_mm',.15)))+.025;gap=center.distance(x['shape'])-radius;row={'REG_uuid':q['uuid'],'REG_kind':kind,'ROOT_uuid':x['uuid'],'layer':x['layer'],'analytic_gap_mm':gap,'required_mm':req};checks.append(row)
   if gap<req:fail.append(row)
(O/'checks.json').write_text(json.dumps(checks,indent=1)+'\n',encoding='utf-8');(O/'errors.json').write_text(json.dumps(fail,indent=1)+'\n',encoding='utf-8');(O/'receipt.json').write_text(json.dumps({'verdict':'PASS_SCOPED_MUTUAL_BODY_DISTANCES' if not fail else 'OWNED_COUPLED_REPAIR_REQUIRED','R114_receipt_sha256':sha(p/'receipt.json'),'ROOT_R18_spines_sha256':sha(root/'proposed-zones.pkl'),'tested_analytic_pairs':len(checks),'errors':len(fail),'checks_sha256':sha(O/'checks.json'),'errors_sha256':sha(O/'errors.json'),'geometry_changed':False,'source_old_contact_current_native_gates':'OPEN','board_written':False,'native_jobs':0},indent=1)+'\n',encoding='utf-8');print('R118',len(checks),'checks',len(fail),'errors',sha(O/'receipt.json'))
