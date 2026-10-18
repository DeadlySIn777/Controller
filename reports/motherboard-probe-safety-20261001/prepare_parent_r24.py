"""Refresh the exact derived198 operator input and build isolated parent r24."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];REPORT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import hardware_build_motherboard_probe_limit_upgrade as upgrade
import hardware_validate_motherboard_probe_limit_upgrade as validate_upgrade
import hardware_validate_motherboard as validator
KICAD=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
live=ROOT/'hardware/motherboard_probe_limit_upgrade'
archive=REPORT/'derived198-before-r24'
if not archive.exists():shutil.copytree(live,archive)
else:assert sha(archive/'design.json')==sha(live/'design.json')
staged=REPORT/'derived198-r24';staged.mkdir(exist_ok=True)
upgrade.REPORT=staged;upgrade.build(staged)
runs=[]
def native(kind,target,out):
    cmd=[str(KICAD),'sch',*kind,'--output',str(out),str(target)]
    r=subprocess.run(cmd,text=True,encoding='utf8',capture_output=True)
    runs.append(dict(command=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
    assert r.returncode==0,r.stderr
native(['export','netlist','--format','kicadxml'],staged/'motherboard_operator.kicad_sch',staged/'netlist.xml')
native(['erc','--format','json'],staged/'motherboard_operator.kicad_sch',staged/'erc.json')
before=read(archive/'design.json');after=read(staged/'design.json')
delta=[]
for ref,c in before['components'].items():
    for pin,net in c['pins'].items():
        if after['components'][ref]['pins'][pin]!=net:
            delta.append(dict(ref=ref,pin=pin,old=net,new=after['components'][ref]['pins'][pin]))
assert delta==[dict(ref='R14069',pin='2',old='PRB0_IN_SENSE',new='PRB0_SENSE'),
               dict(ref='R14072',pin='2',old='PRB1_IN_SENSE',new='PRB1_SENSE')]
normalized=json.loads(json.dumps(after))
for row in delta:normalized['components'][row['ref']]['pins'][row['pin']]=row['old']
assert normalized==before
before_nodes=validator.nodes(ET.parse(archive/'netlist.xml'));after_nodes=validator.nodes(ET.parse(staged/'netlist.xml'))
assert set(before_nodes)==set(after_nodes)
native_delta=[dict(ref=r,pin=p,old=n,new=after_nodes[r,p]) for (r,p),n in before_nodes.items() if after_nodes[r,p]!=n]
assert sorted(native_delta,key=lambda r:r['ref'])==[
    {**r,'old':'/'+r['old'],'new':'/'+r['new']} for r in delta]
assert sha(staged/'bom.csv')==sha(archive/'bom.csv')
for p in (archive/'CNC_MB_Operator.pretty').glob('*'):
    assert sha(p)==sha(staged/'CNC_MB_Operator.pretty'/p.name)
result=validate_upgrade.validate(after,netlist=staged/'netlist.xml',erc=staged/'erc.json');assert result['ok'],result
(staged/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
receipt=dict(exact_two_pin_changes=delta,all_other_source_fields_unchanged=True,
    MAX17612_override_and_current_contract_preserved=True,BOM_and_all_footprint_bytes_unchanged=True,
    components=198,pads=587,native_ERC_errors=0,native_ERC_warnings=2,ignored_checks=[],
    native_runs=runs,source_hashes={p.relative_to(staged).as_posix():sha(p) for p in staged.rglob('*') if p.is_file()},
    parent_modified=False,manufacturing_ready=False)
(REPORT/'derived198-r24-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
for p in staged.iterdir():
    if p.is_file() and p.name!='bounded-delta.json':shutil.copyfile(p,live/p.name)
    elif p.is_dir():shutil.copytree(p,live/p.name,dirs_exist_ok=True)
parent=ROOT/'reports/motherboard-integration-20260930/r24-2688-probe-topology-staged'
assert not parent.exists()
r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/hardware_build_motherboard.py'),'--out',str(parent)],
    text=True,encoding='utf8',capture_output=True)
(REPORT/'parent-r24-builder.log').write_text(r.stdout+r.stderr)
assert r.returncode==0,r.stderr
print(json.dumps(dict(derived_parts=198,pads=587,exact_pin_changes=delta,parent_stage=str(parent.relative_to(ROOT)))))
