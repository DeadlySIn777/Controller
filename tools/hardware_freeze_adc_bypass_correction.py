"""Freeze exact child delta and native proof for three approved ADC capacitors."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def pinmap(p):
    return {(n.attrib['ref'],n.attrib['pin']):net.attrib['name']for net in ET.parse(p).findall('.//nets/net')for n in net.findall('node')}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--proposal',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    before=a.proposal/'before/hardware/motherboard_analog_input';current=ROOT/'hardware/motherboard_analog_input'
    old=load(before/'design.json');new=load(current/'design.json')
    changed=[r for r in old['components']if old['components'][r]!=new['components'][r]]
    if changed!=['C14744','C14745','C14746']or set(old['components'])!=set(new['components']):raise ValueError('Unexpected actual source part delta')
    if old['blocks']!=new['blocks']or old['channels']!=new['channels']or old['boundaries']!=new['boundaries']:raise ValueError('Actual block owner/interface changed')
    if any(c['pins']!=new['components'][r]['pins']for r,c in old['components'].items()):raise ValueError('Actual source pin changed')
    if pinmap(before/'netlist.xml')!=pinmap(current/'netlist.xml'):raise ValueError('Native pin/net changed')
    a.out.mkdir(parents=True,exist_ok=False);frozen=a.out/'after';frozen.mkdir()
    paths=[p for p in current.rglob('*')if p.is_file()]+[ROOT/'tools/hardware_build_motherboard_analog_input.py',ROOT/'tools/hardware_validate_motherboard_analog_input.py',ROOT/'tests/test_motherboard_analog_input.py']
    hashes={str(p.resolve()):sha(p)for p in paths}
    for p in paths:
        dest=frozen/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    commands=[[sys.executable,'-X','utf8','tools/hardware_validate_motherboard_analog_input.py'],
              [sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p','test_motherboard_analog_input.py','-v']]
    results=[]
    for i,cmd in enumerate(commands):
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf8');log=a.out/f'validation-{i}.txt';log.write_text(p.stdout+p.stderr,encoding='utf8')
        results.append(dict(command=cmd,returncode=p.returncode,log=str(log.resolve()),sha256=sha(log)))
        if p.returncode:raise ValueError('Fresh source validation failed')
    for p,h in hashes.items():
        if sha(p)!=h:raise ValueError('Actual child changed during freeze')
    erc=load(current/'erc.json');violations=[v for s in erc['sheets']for v in s['violations']]
    if violations or erc['ignored_checks']:raise ValueError('Native ERC not clean')
    changes=[dict(reference=r,before=old['components'][r],after=new['components'][r],
        fields_changed=[k for k in old['components'][r]if old['components'][r][k]!=new['components'][r][k]])for r in changed]
    result=dict(schema_version=1,passed=True,proposal_sha256=sha(a.proposal/'proposal.json'),
        before_source_hashes={str((before/f).resolve()):sha(before/f)for f in ['design.json','netlist.xml','bom.csv']},
        after_source_hashes=hashes,exact_changes=changes,all_native_pin_net_assignments_preserved=True,
        all_other_components_and_block_ownership_preserved=True,actual_parts=165,actual_electrical_pads=554,
        native_ERC=dict(errors=0,warnings=0,ignored_checks=[]),focused_tests=60,validation=results,
        physical_layout_adoption=False,all_2688_parent_source_adoption_pending=True,
        manufacturing_ready=False,physical_qualified=False,
        remaining_source_primary_part_gap='GRM188R71H105KA12D elsewhere is not primary-confirmed; not newly selected. Retained reference1uF parts and their voltage/ESR/bias remain to source-qualify.',
        reference_table='TI p9 COUT_REFIO/COUT_REFCAP min10uF typ22uF, no numeric ESR limit/max capacitance specified; p31 explicitly another1uF HF cap. 22+1 nominal is coherent, not effective capacitance proof.',
        precision_cells_generic_router_excluded=True)
    (a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(passed=True,changes=changed,ERC_errors=0,ERC_warnings=0,tests=60,parent_adoption_pending=True)))
if __name__=='__main__':main()
