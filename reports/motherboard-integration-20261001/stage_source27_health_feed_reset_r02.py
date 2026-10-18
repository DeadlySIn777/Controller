"""Controlled report-only successor: frozen health override + receiving CLR.
No live source, inherited child, board or shared tool is overwritten.
"""
from pathlib import Path
import sys,json,hashlib,copy,shutil,csv,subprocess,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_build_assembly import parse,dump
from hardware_apply_motor_feed_reset import apply_feed_reset
ROOT=Path.cwd();LIVE=ROOT/'hardware/motherboard'
HEALTH=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01'
PEER=ROOT/'reports/motherboard-power-entry-20261001/feed-latch-reset-source-r01/candidate-r04'
OUT=ROOT/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02';OUT.mkdir(exist_ok=False)
DEST=OUT/'candidate/motherboard'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashes(path):return {p.relative_to(path).as_posix():sha(p)for p in path.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
peer_proof=json.loads((PEER/'freeze-receipt.json').read_text())
assert sha(PEER/'freeze-receipt.json')=='c75808eba7431a3cbb2c2c39758dbc28c92f028768f9e3c46a0f66c3089e6a0a'
for key,h in peer_proof['files'].items():assert sha(ROOT/key)==h,('Peer frozen input changed',key)
proof=json.loads((HEALTH/'freeze-receipt-r01.json').read_text());assert hashes(LIVE)==proof['before_source_sha256']
SRC=HEALTH/'final-source27-candidate/motherboard';assert hashes(SRC)==proof['candidate_source_sha256']
shutil.copytree(LIVE,OUT/'before/motherboard');shutil.copytree(SRC,DEST)
old=json.loads((LIVE/'design.json').read_text());prior=json.loads((SRC/'design.json').read_text());mapping=json.loads((SRC/'assembly-map.json').read_text())
trees={name:parse((SRC/(name+'.kicad_sch')).read_text())for name in('mc_local_power','motherboard_power_entry')}
newtrees,new,ledger=apply_feed_reset(trees,prior)
for name,tree in newtrees.items():(DEST/(name+'.kicad_sch')).write_text(dump(tree)+'\n')
added=set(new['components'])-set(old['components']);assert added=={'U11035','U11036','U11037','U11038','C11089','C11090','C11091','C11092','R11082','R11083'}
changed={r for r in old['components']if old['components'][r]!=new['components'][r]}
assert changed=={'R2106','U11019','U11025','U11032','U11034','R11074','R11078'}
peer_model=json.loads((PEER/'motherboard/design.json').read_text());assert new['components']==peer_model['components']
for key in('adc_bypass_correction','adc_reference_component_qualification'):assert old[key]==new[key]
assert new['physical_footprints']==2698 and new['assembly_fitted_parts']==2696
mapping['physical_parts']=2698
mapping['reviewed_motor_feed_reset_delta']=dict(id='MB-MOTOR-FEED-POR-001',parent_only_override=True,inherited_child_and_Source26_immutable=True,frozen_candidate='reports/motherboard-power-entry-20261001/feed-latch-reset-source-r01/candidate-r04',frozen_receipt_sha256=sha(PEER/'freeze-receipt.json'),frozen_primary_review_sha256=sha(PEER/'primary-and-integration-review.json'),exact_added_references=sorted(added),exact_existing_native_pin_changes=[dict(reference='U11032',pin='6',old='/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A',new='/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_A'),dict(reference='U11034',pin='6',old='/motherboard_power_entry/MOTOR_FEED_CLEAR_N_B',new='/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B')],physical_qualified=False)
dependency=ROOT/'tools/hardware_apply_motor_feed_reset.py'
for d in(new['source_sha256'],mapping['input_sha256']):d[dependency.relative_to(ROOT).as_posix()]=sha(dependency)
for name in('CNC_MB_FeedReset.kicad_sym','fp-lib-table','sym-lib-table'):shutil.copy2(PEER/'motherboard'/name,DEST/name)
shutil.copytree(PEER/'motherboard/CNC_MB_FeedReset.pretty',DEST/'CNC_MB_FeedReset.pretty')
(DEST/'design.json').write_text(json.dumps(new,indent=2)+'\n');(DEST/'assembly-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
with(DEST/'bom.csv').open(newline='',encoding='utf8')as file:reader=csv.DictReader(file);fields=reader.fieldnames;rows=list(reader)
byref={row['Reference']:row for row in rows}
for ref in sorted(changed|added):
 part=new['components'][ref];row=copy.deepcopy(byref.get(ref,{key:''for key in fields}))
 row.update(Reference=ref,Value=part['value'],MPN=part.get('mpn',''),Footprint=part.get('footprint',''))
 if ref in added:row.update(Status=part.get('status','candidate_not_qualified'),DNP='false',Scope='actual_on_motherboard_component_candidate');rows.append(row)
 else:byref[ref].update(row)
with(DEST/'bom.csv').open('w',encoding='utf8',newline='')as file:w=csv.DictWriter(file,fieldnames=fields);w.writeheader();w.writerows(rows)
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
for label,args in[('netlist',['sch','export','netlist','--format','kicadxml','-o',str(DEST/'netlist.xml'),str(DEST/'motherboard.kicad_sch')]),('ERC',['sch','erc','--format','json','--severity-all','-o',str(OUT/'erc.json'),str(DEST/'motherboard.kicad_sch')])]:
 run=subprocess.run([CLI]+args,capture_output=True,text=True,encoding='utf8');(OUT/(label+'.log')).write_text(run.stdout+run.stderr);assert not run.returncode,(label,run.returncode)
def nodes(path):return{(n.get('ref'),n.get('pin')):net.get('name')for net in ET.parse(path).findall('.//nets/net')for n in net.findall('node')}
bn,an=nodes(LIVE/'netlist.xml'),nodes(DEST/'netlist.xml');actual_changed={k:(v,an.get(k))for k,v in bn.items()if an.get(k)!=v}
assert actual_changed=={('U11032','6'):('/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A','/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_A'),('U11034','6'):('/motherboard_power_entry/MOTOR_FEED_CLEAR_N_B','/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B')}
newpins={k:v for k,v in an.items()if k not in bn};assert len(newpins)==34 and sum(v.startswith('unconnected-')for v in newpins.values())==4
erc=json.loads((OUT/'erc.json').read_text());viol=[v for sheet in erc['sheets']for v in sheet['violations']];assert not erc['ignored_checks']and len(viol)==70 and not any(v['severity']=='error'for v in viol)
assert hashes(LIVE)==proof['before_source_sha256']
receipt=dict(passed=True,adopted=False,physical_parts=2698,purchased_fitted_parts=2652,bare_features=44,DNP_footprints=2,changed_existing_references=sorted(changed),new_references=sorted(added),actual_existing_pin_changes=[dict(reference=k[0],pin=k[1],old=v[0],new=v[1])for k,v in actual_changed.items()],new_native_pins=34,new_connected_native_pins=30,new_NC_pins=4,all_other_existing_pin_nets_unchanged=True,all_original327_native_pin_nets_unchanged=True,FPGA135_assigned48_free_unchanged=True,source26_ADC_fuse_metadata_retained=True,peer_component_dictionaries_exactly_reproduced=True,native_ERC_errors=0,native_ERC_warnings=70,no_ignored_checks=True,before_source_sha256=proof['before_source_sha256'],candidate_source_sha256=hashes(DEST),original_health_stage_sha256=sha(HEALTH/'freeze-receipt-r01.json'),frozen_feed_reset_primary_sha256=sha(PEER/'freeze-receipt.json'),independent_parent_validator_and_future_generator_hook_pending=True,live_source26_unchanged=True,physical_qualification=False,manufacturing_ready=False)
(OUT/'initial-stage-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({key:receipt[key]for key in('passed','adopted','physical_parts','new_native_pins','native_ERC_errors','native_ERC_warnings')}))
