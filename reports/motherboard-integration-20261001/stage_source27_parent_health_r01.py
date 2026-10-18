from pathlib import Path
import sys,copy,json,csv,shutil,hashlib,subprocess,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_apply_motherboard_health_source import apply_health_source,health_screen
from hardware_build_assembly import parse,dump,children,child,value,ref_property
ROOT=Path.cwd();LIVE=ROOT/'hardware/motherboard';OUT=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01';OUT.mkdir(exist_ok=False,parents=True);DEST=OUT/'candidate/motherboard';SOURCE=ROOT/'reports/motherboard-power-entry-20261001/health-source-correction-r01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashes(folder):return {str(p.relative_to(folder)).replace('\\','/'):sha(p)for p in folder.rglob('*')if p.is_file()}
freeze=json.loads((SOURCE/'freeze-receipt.json').read_text())
for p,h in freeze['files_sha256'].items():
 if sha(ROOT/p)!=h:raise ValueError('Frozen health input changed '+p)
livehash=hashes(LIVE);shutil.copytree(LIVE,OUT/'before/motherboard');shutil.copytree(LIVE,DEST)
model=json.loads((LIVE/'design.json').read_text());mapping=json.loads((LIVE/'assembly-map.json').read_text());old=copy.deepcopy(model);originaltrees={n:parse((LIVE/(n+'.kicad_sch')).read_text())for n in ['mc_local_power','motherboard_power_entry']};trees,new,ledger=apply_health_source(originaltrees,model)
changed={r for r in old['components']if old['components'][r]!=new['components'][r]}
if changed!={'R2106','U11019','U11025'} or any(old['components'][r]['pins']!=new['components'][r]['pins']or old['components'][r]['footprint']!=new['components'][r]['footprint']for r in old['components']):raise ValueError('Unexpected parent delta')
for name,tree in trees.items():
 restored=copy.deepcopy(tree)
 for i,n in enumerate(restored):
  if isinstance(n,list)and n and n[0]=='symbol'and value(ref_property(n)[2])in changed:
   ref=value(ref_property(n)[2]);prior=next(s for s in children(originaltrees[name],'symbol')if value(ref_property(s)[2])==ref);restored[i]=copy.deepcopy(prior)
 if restored!=originaltrees[name]:raise ValueError('Native non-symbol-procurement object changed')
 (DEST/(name+'.kicad_sch')).write_text(dump(tree)+'\n')
meta=dict(id='MB-HEALTH-001',references=['R2106','U11019','U11025'],parent_only_override=True,immutable_child04_and_original_MC_baselines_retained=True,frozen_primary_receipt=str((SOURCE/'receipt.json').relative_to(ROOT)).replace('\\','/'),frozen_primary_receipt_sha256=sha(SOURCE/'receipt.json'),frozen_primary_review_sha256=sha(SOURCE/'sources/primary-review.json'),native_pin_nets_unchanged=True,manufacturer_lands_unchanged=True,part_count_unchanged=True,physical_qualified=False)
mapping['reviewed_health_source_delta']=meta
(DEST/'design.json').write_text(json.dumps(new,indent=2)+'\n');(DEST/'assembly-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
with (DEST/'bom.csv').open(newline='',encoding='utf8')as f:r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
before=copy.deepcopy(rows)
for row in rows:
 if row['Reference']in changed:
  c=new['components'][row['Reference']];row['MPN']=c['mpn'];row['Value']=c['value']
if {r['Reference']for r,o in zip(rows,before)if r!=o}!=changed:raise ValueError('Unreviewed BOM edits')
with (DEST/'bom.csv').open('w',newline='',encoding='utf8')as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe';commands=[]
for label,args in [('netlist',['sch','export','netlist','--format','kicadxml','-o',str(DEST/'netlist.xml'),str(DEST/'motherboard.kicad_sch')]),('ERC',['sch','erc','--format','json','--severity-all','-o',str(OUT/'erc.json'),str(DEST/'motherboard.kicad_sch')])]:
 p=subprocess.run([CLI]+args,capture_output=True,text=True,encoding='utf8');(OUT/(label+'.log')).write_text(p.stdout+p.stderr);commands.append(dict(label=label,returncode=p.returncode))
 if p.returncode:raise ValueError('Native command failed '+label)
def endpoints(path):return {n.get('name'):sorted((v.get('ref'),v.get('pin'))for v in n.findall('node'))for n in ET.parse(path).findall('.//nets/net')}
if endpoints(LIVE/'netlist.xml')!=endpoints(DEST/'netlist.xml'):raise ValueError('Native endpoint changed')
erc=json.loads((OUT/'erc.json').read_text());warn=[v for s in erc['sheets']for v in s['violations']]
if erc['ignored_checks']or any(v['severity']=='error'for v in warn)or len(warn)!=70:raise ValueError('Unreviewed native ERC change')
if livehash!=hashes(LIVE):raise ValueError('Live parent changed during stage')
result=dict(passed=True,adopted=False,scope='Exactly three parent-only health procurement/default corrections; inherited child/original327 immutable',source=str(DEST.relative_to(ROOT)).replace('\\','/'),before_source_sha256=livehash,candidate_source_sha256=hashes(DEST),frozen_health_source_receipt_sha256=sha(SOURCE/'freeze-receipt.json'),exact_changed_refs=sorted(changed),exact_three_part_ledger=ledger['exact_three_part_ledger'],source26_ADC_and_fuse_metadata_retained=(new['adc_bypass_correction']==old['adc_bypass_correction']and new['adc_reference_component_qualification']==old['adc_reference_component_qualification']),source26_and_ADC_mapping_retained=(mapping['reviewed_source26_qualification_delta']==json.loads((LIVE/'assembly-map.json').read_text())['reviewed_source26_qualification_delta']and mapping['reviewed_adc_bypass_delta']==json.loads((LIVE/'assembly-map.json').read_text())['reviewed_adc_bypass_delta']),all_native_pin_nets_preserved=True,all_manufacturer_lands_preserved=True,physical_parts=2688,retained327=327,FPGA_assigned=135,FPGA_free=48,native_ERC_errors=0,native_ERC_warnings=70,noignored=True,old_child04_baseline_untouched=True,independent_bounded_parent_validation_pending=True,reproducible_future_generator_hook_pending=True,live_parent_source26_unchanged=True,physical_qualification=False,manufacturing_ready=False)
(OUT/'initial-stage-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(stage_passed=True,adopted=False,source=str(DEST),ERC_errors=0,ERC_warnings=70)),flush=True)
