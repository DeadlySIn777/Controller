from pathlib import Path
import json,sys,copy,hashlib,csv,shutil,subprocess,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_apply_motherboard_health_source import apply_health_source,health_screen
from hardware_build_assembly import parse,dump,children,child,value,ref_property
OUT=Path('reports/motherboard-power-entry-20261001/health-source-correction-r01/candidate-r02');OUT.mkdir(parents=True,exist_ok=False);SOURCE=Path('hardware/motherboard');dest=OUT/'motherboard'
shutil.copytree(SOURCE,dest,ignore=shutil.ignore_patterns('*.kicad_pcb','*.kicad_prl','*.zip','*-backups','~*'))
model=json.loads((SOURCE/'design.json').read_text());trees={k:parse((SOURCE/(k+'.kicad_sch')).read_text())for k in ['mc_local_power','motherboard_power_entry']};orig=copy.deepcopy(model);trees,new,receipt=apply_health_source(trees,model)
for name,tree in trees.items():(dest/(name+'.kicad_sch')).write_text(dump(tree)+'\n')
(dest/'design.json').write_text(json.dumps(new,indent=2)+'\n')
with (dest/'bom.csv').open('w',newline='',encoding='utf8')as f:
 w=csv.writer(f);w.writerow(['Reference','Value','MPN','Footprint','Status','DNP','Scope'])
 for r,c in new['components'].items():w.writerow([r,c['value'],c.get('mpn',''),c.get('footprint',''),c.get('status','candidate_not_qualified'),str(bool(c.get('dnp',False))).lower(),'actual_on_motherboard_component_candidate'])
changed={r for r in orig['components']if orig['components'][r]!=new['components'][r]};assert changed=={'R2106','U11019','U11025'}
assert all(orig['components'][r]['pins']==c['pins']and orig['components'][r]['footprint']==c['footprint']for r,c in new['components'].items())
negatives=[]
for ref,key,bad in [('R2106','mpn','CRCW060310K0FKEA'),('R2106','pins',{'1':'CORE_5V','2':'LOGIC_GND'}),('U11019','footprint','Package_TO_SOT_SMD:SOT-23-6'),('U11025','pins',{'1':'MOTOR_FIELD_HEALTH_A_RAW','2':'LOGIC_GND','3':'MOTOR_FIELD_HEALTH_B_RAW','4':'FIELD_HEALTH_B_N','5':'FIELD_5V','6':'FIELD_HEALTH_A_N'})]:
 m=copy.deepcopy(model);m['components'][ref][key]=bad
 try:apply_health_source({k:parse((SOURCE/(k+'.kicad_sch')).read_text())for k in trees},m)
 except ValueError:negatives.append(dict(reference=ref,mutated_field=key,rejected=True))
 else:raise AssertionError(('Mutation accepted',ref,key))
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
for args in [['sch','export','netlist','--format','kicadxml','-o',str(dest/'netlist.xml'),str(dest/'motherboard.kicad_sch')],['sch','erc','--format','json','--severity-all','-o',str(OUT/'erc.json'),str(dest/'motherboard.kicad_sch')]]:
 run=subprocess.run([CLI]+args,capture_output=True,text=True);assert run.returncode==0,(args,run.stdout,run.stderr)
oldnet=ET.parse(SOURCE/'netlist.xml');newnet=ET.parse(dest/'netlist.xml')
def endpoints(t):return {n.get('name'):sorted((v.get('ref'),v.get('pin'))for v in n.findall('node'))for n in t.findall('.//nets/net')}
assert endpoints(oldnet)==endpoints(newnet)
erc=json.loads((OUT/'erc.json').read_text());errors=[v for s in erc.get('sheets',[])for v in s.get('violations',[])if v['severity']=='error'];assert not errors
s=health_screen();old=health_screen(47000);assert s['high_v']>3.8 and s['reset_total_sink_a']<.003 and old['high_v']<3.8 and s['absent_external_pullup_high_screen_v']<.8
receipt.update(exact_changed_model_refs=sorted(changed),all_native_net_endpoints_unchanged=True,native_erc_errors=errors,meaningful_negative_controls=negatives,core_healthy_dc_screen=s,old47k_loaded_screen=old,candidate_only=True,manufacturing_ready=False)
(Path('reports/motherboard-power-entry-20261001/health-source-correction-r01')/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('HEALTH_SOURCE_CANDIDATE',json.dumps(receipt),flush=True)
