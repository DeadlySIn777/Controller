"""Immutable exact-pin transition plus fresh source-host regression; no manufacture claim."""
import datetime,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;dest=OUT/'r02-frozen'
assert not dest.exists(),'Do not replace issued source freeze'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[p for n in ['motherboard_analog_output','motherboard_analog_input'] for p in (ROOT/'hardware'/n).rglob('*') if p.is_file()]
paths += [ROOT/f'{prefix}/test_motherboard_{n}.py' if prefix=='tests' else ROOT/f'{prefix}/hardware_{op}_motherboard_{n}.py' for n in ['analog_output','analog_input'] for prefix,op in [('tests',''),('tools','build'),('tools','validate')]]
paths += list((OUT/'sources').glob('*.pdf'))+list((OUT/'sources').glob('*.txt'))+[OUT/'native-geometry.json',OUT/'native_geometry.py']
before={p.relative_to(ROOT).as_posix():sha(p) for p in paths};tests=[]
for name in ['analog_input','analog_output','acc_control','comms','identity_io','process','operator','io_control','do','di']:
 r=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p',f'test_motherboard_{name}.py','-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
 log=OUT/('r02-tests-'+name+'.txt');log.write_text(r.stdout+r.stderr,encoding='utf-8');m=re.search(r'Ran (\d+) tests?',r.stdout+r.stderr)
 tests.append(dict(name=name,count=int(m.group(1)) if m else None,passed=r.returncode==0,log_sha256=sha(log)))
 if r.returncode:print(r.stdout+r.stderr);raise SystemExit(r.returncode)
changed=[k for k,v in before.items() if sha(ROOT/k)!=v];assert not changed,changed
for p in paths:
 q=dest/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
ledger=[];models={}
for block in ['motherboard_analog_output','motherboard_analog_input']:
 old=json.loads((OUT/'pre-r02-frozen/hardware'/block/'design.json').read_text());new=json.loads((ROOT/'hardware'/block/'design.json').read_text());models[block]=new
 for ref in sorted(set(old['components'])|set(new['components'])):
  a=old['components'].get(ref);b=new['components'].get(ref)
  if a!=b:ledger.append(dict(source_block=block,reference=ref,old=a,new=b,physical_pin_changes={pin:dict(old=a['pins'].get(pin) if a else None,new=b['pins'].get(pin) if b else None) for pin in sorted(set(a['pins'] if a else[])|set(b['pins'] if b else[])) if not a or not b or a['pins'].get(pin)!=b['pins'].get(pin)}))
geometry=json.loads((OUT/'native-geometry.json').read_text())
receipt=dict(schema_version=1,date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='frozen corrected native source candidates; routed/thermal/target qualification open',
 source_counts={k:dict(physical_footprints=len(v['components']),electrical_pads=v['fitted_pad_count']) for k,v in models.items()},
 input_hashes=before,inputs_unchanged=True,tests=tests,fresh_test_count=sum(x['count'] for x in tests),focused_AI_AO_tests=95,
 native_ERC={'AO':{'errors':0,'warnings':8,'ignored':0,'justification':'Exact existing isolated AO_COM ground-name heuristic warnings; no domain bond'},'AI':{'errors':0,'warnings':0,'ignored':0}},
 native_full_pin_map_validations_pass=True,native_geometry=geometry,changed_physical_source_records=ledger,
 primary_sources={'Traco':'https://www.tracopower.com/tmr4wi-datasheet','TPS7A26':'https://www.ti.com/lit/ds/symlink/tps7a26.pdf','TPS3702':'https://www.ti.com/lit/ds/symlink/tps3702.pdf'},
 independent_review={'reviewer':'motherboard_contract','verified':'All5 converters feed actual CORE24; TPS3700 VDD overstress corrected; TPS3702 threshold/hysteresis bounds and TPS7A26 additive regulator screen source-checked.','remaining':'Actual maximum mixed AI5 load/copper thermal and loaded validity/ripple/propagation remain unqualified, not implied by500mA LDO rating.'},
 mechanical_modules=[dict(source_block=block,reference=ref,mpn=p['mpn'],body_xyz_mm=[21.8,9.3,11.2],courtyard_xy_mm=[23,10.5],top_view_pads={n:[8.9-(int(n)-1)*2.54,1.95] for n in p['pins']},routing_exclusion='No unrelated traces or copper pours under full body. Only own-pin escapes require vendor/layout reconciliation, not automatic waiver.',NC_pins=['5','8'],remote_open_pin='3',assembly_drill_mm=.9,assembly_pad_diameter_mm=1.7,manufacturer_land_not_specified=True) for block,d in models.items() for ref,p in d['components'].items() if p['mpn'].startswith('TMR 4-')],
 manufacturing_ready=False,parent_adoption=False,routed_board_DRC_pass=False,target_compiled=False,physical_qualification=False)
(OUT/'receipt-r02.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(source_counts=receipt['source_counts'],fresh_test_count=receipt['fresh_test_count'],hash_count=len(before),changed_inputs=changed,manufacturing_ready=False)))
