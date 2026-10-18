"""Apply exactly three frozen ADC capacitor changes to the retained parent.

This edits only the native symbol properties and corresponding parts/BOM. It
never regenerates the hierarchy, FPGA allocation, retained MC or other regions.
"""
from __future__ import annotations
import argparse, copy, csv, datetime, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
from hardware_build_assembly import parse,dump,children,child,value,q,ref_property
from hardware_validate_motherboard import validate,nodes

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
REFS=('C14744','C14745','C14746')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,o):Path(p).write_text(json.dumps(o,indent=2)+'\n',encoding='utf8')
def file_hashes(folder):return {str(p.relative_to(folder)).replace('\\','/'):sha(p) for p in folder.rglob('*')if p.is_file()}

def apply(stage,child_receipt):
    old=load(stage/'design.json');model=copy.deepcopy(old);mapping=load(stage/'assembly-map.json')
    receipt=load(child_receipt);source=ROOT/'hardware/motherboard_analog_input';new=load(source/'design.json')
    if not receipt['passed']or[ r['reference']for r in receipt['exact_changes']]!=list(REFS):raise ValueError('Exact frozen three-cap receipt required')
    for p,h in receipt['after_source_hashes'].items():
        if sha(p)!=h:raise ValueError('Frozen child input changed: '+p)
    before_tree=parse((stage/'motherboard_analog_input.kicad_sch').read_text(encoding='utf8'));tree=copy.deepcopy(before_tree)
    symbols={value(ref_property(s)[2]):s for s in children(tree,'symbol')}
    changes=[]
    for ref in REFS:
        wanted=new['components'][ref];existing=model['components'][ref]
        frozen=next(r for r in receipt['exact_changes']if r['reference']==ref)
        if {k:v for k,v in existing.items()if k not in ('source_block','source_reference')}!=frozen['before']:raise ValueError('Actual parent differs from frozen prior part '+ref)
        model['components'][ref]={**wanted,'source_block':'motherboard_analog_input','source_reference':ref}
        for prop in children(symbols[ref],'property'):
            key=value(prop[1]);field={'Value':'value','MPN':'mpn','Footprint':'footprint'}.get(key)
            if field:prop[2]=q(wanted[field])
        changes.append(dict(reference=ref,before=existing,after=model['components'][ref]))
    allowed_symbols={value(ref_property(s)[2])for s in children(tree,'symbol')if s in [symbols[r]for r in REFS]}
    if allowed_symbols!=set(REFS):raise ValueError('Exactly three symbol property edits required')
    restored=copy.deepcopy(tree)
    originals={value(ref_property(s)[2]):s for s in children(before_tree,'symbol')}
    for i,n in enumerate(restored):
        if isinstance(n,list)and n and n[0]=='symbol'and value(ref_property(n)[2])in REFS:restored[i]=originals[value(ref_property(n)[2])]
    if restored!=before_tree:raise ValueError('Other integrated schematic objects changed')
    (stage/'motherboard_analog_input.kicad_sch').write_text(dump(tree)+'\n',encoding='utf8')
    model['adc_bypass_correction']=copy.deepcopy(new['adc_bypass_correction'])
    mapping['reviewed_adc_bypass_delta']=dict(id='MB-AI-ADC-001',references=list(REFS),
        child_receipt=str(child_receipt.relative_to(ROOT)).replace('\\','/'),child_receipt_sha256=sha(child_receipt),
        unchanged_native_pin_nets=True,unchanged_part_count=True,physical_layout_qualified=False)
    for container in [model['source_sha256'],mapping['input_sha256']]:
        for p in list(container):
            if p.startswith('hardware/motherboard_analog_input/'):
                container[p]=sha(ROOT/p)
    write(stage/'design.json',model);write(stage/'assembly-map.json',mapping)
    with (stage/'bom.csv').open(newline='',encoding='utf8')as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    old_rows=copy.deepcopy(rows)
    for row in rows:
        if row['Reference']in REFS:
            c=model['components'][row['Reference']]
            for label,k in [('Value','value'),('MPN','mpn'),('Footprint','footprint')]:row[label]=c[k]
    if [r['Reference']for r,o in zip(rows,old_rows)if r!=o]!=list(REFS):raise ValueError('BOM changed beyond approved three parts')
    with (stage/'bom.csv').open('w',newline='',encoding='utf8')as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    return changes

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--child-receipt',type=Path,required=True)
    ap.add_argument('--previous-adoption',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--adopt',action='store_true');a=ap.parse_args()
    a.out=a.out.resolve();a.child_receipt=a.child_receipt.resolve();live=ROOT/'hardware/motherboard';prior=load(a.previous_adoption)
    for relative,h in prior['source_hashes'].items():
        if sha(live/relative)!=h:raise ValueError('Actual prior adopted parent changed: '+relative)
    if a.out.exists():raise ValueError('Fresh immutable report required')
    a.out.mkdir(parents=True);before=a.out/'before';stage=a.out/'source-r25';shutil.copytree(live,before);shutil.copytree(live,stage)
    old_hashes=file_hashes(before);old_model=load(before/'design.json');old_nodes=nodes(ET.parse(before/'netlist.xml'))
    changes=apply(stage,a.child_receipt)
    run=[]
    for i,cmd in enumerate([[str(CLI),'sch','export','netlist','--format','kicadxml','--output',str(stage/'netlist.xml'),str(stage/'motherboard.kicad_sch')],
                           [str(CLI),'sch','erc','--format','json','--output',str(a.out/'erc.json'),str(stage/'motherboard.kicad_sch')]]):
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8');(a.out/f'native-{i}.txt').write_text(p.stdout+p.stderr,encoding='utf8');run.append(dict(command=cmd,returncode=p.returncode))
        if p.returncode:raise ValueError('Native export/ERC command failed')
    model=load(stage/'design.json');mapping=load(stage/'assembly-map.json');native=ET.parse(stage/'netlist.xml')
    if nodes(native)!=old_nodes:raise ValueError('Any actual native pin/net changed')
    if set(model['components'])!=set(old_model['components'])or len(model['components'])!=2688:raise ValueError('Full physical source count changed')
    if [r for r in model['components']if model['components'][r]!=old_model['components'][r]]!=list(REFS):raise ValueError('Other actual parent component changed')
    errors=validate(native,model,mapping)
    if errors:write(a.out/'validation-failed.json',errors);raise ValueError('Fresh independent source validation failed')
    erc=load(a.out/'erc.json');violations=[v for s in erc['sheets']for v in s['violations']]
    if any(v['severity']=='error'for v in violations)or erc['ignored_checks']:raise ValueError('Native ERC error/ignored check')
    env={**os.environ,'CONTROLLER_MOTHERBOARD_TEST_SOURCE':str(stage.resolve())};tests=[]
    for name in ['test_motherboard_integration.py','test_motherboard_adc_source_adoption.py','test_motherboard_analog_input.py','test_motherboard_fpga_current_annotations.py','test_motherboard_fpga_allocation.py']:
        cmd=[sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p',name,'-v'];p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8');log=a.out/(name+'.log');log.write_text(p.stdout+p.stderr,encoding='utf8');tests.append(dict(name=name,returncode=p.returncode,log=str(log.relative_to(ROOT))))
        if p.returncode:raise ValueError('Fresh focused regression failed '+name)
    after_hashes=file_hashes(stage);changed_files=[p for p in old_hashes if after_hashes.get(p)!=old_hashes[p]]
    expected={'motherboard_analog_input.kicad_sch','design.json','assembly-map.json','bom.csv','netlist.xml'}
    if set(changed_files)!=expected:raise ValueError('Actual parent file delta outside exact bounds: '+repr(changed_files))
    if file_hashes(live)!=old_hashes:raise ValueError('Actual prior parent changed while staging')
    if a.adopt:
        for name in changed_files:shutil.copyfile(stage/name,live/name)
    result=dict(schema_version=1,passed=True,adopted=a.adopt,date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        previous_adoption_sha256=sha(a.previous_adoption),child_receipt_sha256=sha(a.child_receipt),
        exact_component_changes=changes,exact_changed_parent_files=changed_files,
        all_native_pin_nets_preserved=True,retained_mc_parts=327,retained_mc_native_pin_nets=1229,
        FPGA_electrical_and_metadata_files_byte_unchanged=True,FPGA_assigned=135,FPGA_free=48,
        physical_parts=2688,purchased_fitted_parts=2642,bare_geometry=44,DNP=2,
        native_ERC_errors=0,native_ERC_warnings=len(violations),ignored_checks=[],
        independent_validation_pass=True,tests=tests,native_commands=run,source=str(stage.relative_to(ROOT)),
        archive=str(before.relative_to(ROOT)),source_hashes=after_hashes,
        physical_layout_adopted=False,manufacturing_ready=False,physical_qualified=False,
        new_AI5_transient_qualification_pending=True,reference_effective_capacitance_qualification_pending=True,
        tool_sha256=sha(__file__))
    write(a.out/'adoption.json',result)
    print(json.dumps(dict(passed=True,adopted=a.adopt,parts=2688,ERC_errors=0,ERC_warnings=len(violations),changed_components=list(REFS),receipt=str(a.out/'adoption.json'))))
if __name__=='__main__':main()
