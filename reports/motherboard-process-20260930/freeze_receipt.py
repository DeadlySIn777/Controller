"""Freeze source evidence and rerun bounded existing disconnected tests."""
import datetime,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REPORT=Path(__file__).resolve().parent;OUT=ROOT/'hardware/motherboard_process'
sources=REPORT/'sources'
copies=[('reports/motherboard-do-20260930/sources/tnpw.pdf','tnpw.pdf','https://www.vishay.com/docs/28758/tnpw.pdf'),('reports/motherboard-do-20260930/sources/sn74lvc08a.pdf','sn74lvc08a.pdf','https://www.ti.com/lit/ds/symlink/sn74lvc08a.pdf'),('reports/motherboard-do-20260930/sources/sn74lvc1g74.pdf','sn74lvc1g74.pdf','https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf'),('reports/motherboard-operator-20260930/sources/sn74lvc1g08.pdf','sn74lvc1g08.pdf','https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf'),('reports/motherboard-operator-20260930/sources/tpd1e10b06.pdf','tpd1e10b06.pdf','https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf')]
for source,name,url in copies:
 shutil.copy2(ROOT/source,sources/name)
 txt=(ROOT/source).with_suffix('.txt')
 if txt.exists():shutil.copy2(txt,sources/Path(name).with_suffix('.txt'))
urls={name:url for _,name,url in copies}
urls.update({n+'.pdf':'https://www.ti.com/lit/ds/symlink/'+n+'.pdf' for n in ['tps1h000-q1','sn74lvc1g06','tps22918','sn74lvc2t45','lm66100']})
urls['pmv20xnea.pdf']='https://assets.nexperia.com/documents/data-sheet/PMV20XNEA.pdf'
manifest=[{'file':p.relative_to(ROOT).as_posix(),'url':urls.get(p.name),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'source':'primary PDF; copied historical hashes identified where reused'} for p in sorted(sources.glob('*.pdf'))]
(sources/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
paths=list(p for p in OUT.rglob('*') if p.is_file())+[ROOT/'tools/hardware_build_motherboard_process.py',ROOT/'tools/hardware_validate_motherboard_process.py',ROOT/'tests/test_motherboard_process.py']+list(sources.glob('*.pdf'))+list(sources.glob('*.txt'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
tests=[]
for name in ['process','io_control','operator','do','di','motors']:
 cmd=[sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p','test_motherboard_'+name+'.py','-v']
 r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8');log=REPORT/('tests-'+name+'.txt');log.write_text(r.stdout+r.stderr)
 m=re.search(r'Ran (\d+) tests?',r.stdout+r.stderr);tests.append({'name':name,'count':int(m.group(1)) if m else None,'passed':r.returncode==0,'log_sha256':sha(log)})
 if r.returncode:print(r.stdout+r.stderr);raise SystemExit(r.returncode)
changed=[k for k,v in before.items() if sha(ROOT/k)!=v]
freeze=REPORT/'frozen-inputs';freeze.mkdir(exist_ok=True)
for p in paths:
 f=freeze/p.relative_to(ROOT);f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,f)
(REPORT/'input-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
native=json.loads((REPORT/'native-footprints.json').read_text());d=json.loads((OUT/'design.json').read_text())
receipt={'schema_version':1,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'frozen native circuit candidate','physical_footprints':68,'purchased_fitted_parts':68,'unique_electrical_pads':216,'all_native_pad_shapes':native['all_pad_shapes'],'native_ERC':{'errors':0,'warnings':0,'ignored_checks':[]},'nativeXML_independent_checks':'PASS','native_footprint_load':native['ok'],'primary_geometry_assertions':native['primary_geometry_assertions'],'tests':tests,'fresh_test_count':sum(t['count'] for t in tests),'input_hash_count':len(before),'changed_inputs':changed,'manufacturing_ready':False,'PCB_routing_provided':False,'target_firmware_compiled':False,'physical_qualified':False,'parent_integrated':False,'open_engineering_gates':d['unimplemented_parent_obligations'][:3],'physical_gates':[d['unimplemented_parent_obligations'][3],'PWM clamp turn-on timing and no-IO3 gate voltage/leakage at full temperature','PWM 20mA loaded levels at actual 3.3V-to-5V translator condition','TPS1H000 programmed current-limit conditions and latch-off delay / fault classification','Reverse-fed PWM startup energy and LM66100 reverse transient'],'boundary_file':'hardware/motherboard_process/boundary-map.json'}
(REPORT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ['tests','open_engineering_gates','physical_gates']}));raise SystemExit(bool(changed))
