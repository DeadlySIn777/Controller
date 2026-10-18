"""Source-only, integrated ROOT106 correction. No native jobs or live edits."""
import json,copy,hashlib,re,uuid
from pathlib import Path
import inspect_integrated_source as I
import source_correction_r1 as S
HERE=Path(__file__).resolve().parent
ROOT=Path.cwd()
SRC=ROOT/'reports/board-finish-20261011/parity-repair/root106/source/motherboard_power_entry.kicad_sch'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    comps,pins=I.load();ref='C11094';reserved={'U11038','C11092','C11093','R11088'}
    assert ref not in comps and ref not in reserved
    assert comps['L11001']['value']=='4.7uH 20%' and comps['L11001']['fields']['MPN']=='XAL1010-472MED'
    assert pins['C11088']=={'1':'/mc_local_power{slash}CORE_5V','2':'/LOGIC_GND'}
    assert pins['C11089']=={'1':'/motherboard_power_entry/C_SHDN','2':'/LOGIC_GND'}
    before={str(p.resolve()):sha(p) for p in (SRC,I.NET,I.PARSER,HERE/'source-correction-r1.json',HERE/'source-proposal/design.json')}
    text=SRC.read_text(encoding='utf-8');lines=text.splitlines(keepends=True)
    li=next(i for i,l in enumerate(lines) if '(property "Reference" "L11001"' in l)
    ci=next(i for i,l in enumerate(lines) if '(property "Reference" "C11088"' in l)
    old_l=lines[li];new_l=old_l.replace('"4.7uH 20%"','"6.8uH 20%"').replace('"XAL1010-472MED"','"XAL1010-682MED"')
    assert new_l!=old_l;lines[li]=new_l
    # Place a distinct same-symbol capacitor in unused schematic bottom space.
    # All source labels remain literal CORE_5V and LOGIC_GND; hierarchy does the binding.
    block=''.join(lines[ci:ci+5]).replace('C11088',ref)
    translate=(0.,480.)
    def pos(m):return '('+m[1]+' '+format(float(m[2])+translate[0],'.10g')+' '+format(float(m[3])+translate[1],'.10g')
    block=re.sub(r'\((at|xy) (-?[0-9.]+) (-?[0-9.]+)',pos,block)
    old_uuids=re.findall(r'\(uuid "([^"]+)"\)',block)
    uuid_ledger={old:str(uuid.uuid5(uuid.NAMESPACE_URL,'controller:CORE-full-source-r2:'+ref+':'+old)) for old in old_uuids}
    for old,new in uuid_ledger.items():block=block.replace('(uuid "'+old+'")','(uuid "'+new+'")')
    # The complete source remains byte-for-byte outside the one inductor line plus added block.
    patched=''.join(lines);end=patched.rfind(')');patched=patched[:end]+block+patched[end:]
    dest=HERE/'source-proposal-r2';dest.mkdir(exist_ok=True)
    sch=dest/'motherboard_power_entry.kicad_sch'
    if sch.exists():raise ValueError('Immutable proposal exists')
    sch.write_text(patched,encoding='utf-8',newline='')
    integrated={r:{**copy.deepcopy(c),'pins':copy.deepcopy(pins.get(r,{}))} for r,c in comps.items() if c['sheet']=='/motherboard_power_entry/'}
    integrated['L11001']['value']='6.8uH 20%';integrated['L11001']['fields']['MPN']='XAL1010-682MED'
    integrated[ref]=copy.deepcopy(integrated['C11088'])
    manifest=dest/'integrated-power-source.json';manifest.write_text(json.dumps({'schema':'integrated-ROOT106-CORE-source-correction-r2','component_count_root_before':len(comps),'component_count_root_proposed':len(comps)+1,'power_entry_components':integrated,'all_existing_component_refs':sorted(comps),'new_reference':ref,'native_export_performed':False},indent=2)+'\n',encoding='utf-8')
    prior=json.loads((HERE/'source-correction-r1.json').read_text());tests=prior['bounded_screens']
    receipt={**prior,'schema':'integrated-ROOT106-CORE-source-correction-r2','proposal_sha256':sha(sch),'source_original_sha256':sha(SRC),'native_schematic_candidate':str(sch.resolve()),'integrated_manifest':str(manifest.resolve()),'integrated_manifest_sha256':sha(manifest),
      'supersedes_invalid_reference_proposal':{'receipt':str((HERE/'source-correction-r1.json').resolve()),'valid_for_integration':False,'reason':'C11089 already exists in integrated ROOT106 as 10nF CORE shutdown filter. Standalone 221-part dictionary omitted integrated shutdown additions.'},
      'source_pin_ledger':{'L11001':{'old':comps['L11001'],'pins':pins['L11001'],'new_value':'6.8uH 20%','new_MPN':'XAL1010-682MED','footprint_unchanged':True},ref:{'old':None,'new':integrated[ref],'symbol_uuid':uuid_ledger[old_uuids[0]],'source_position_mm':[762.,3329.88]},'C11089':{'preserved':comps['C11089'],'pins':pins['C11089']},'C11090':{'preserved':comps['C11090'],'pins':pins['C11090']},'C11091':{'preserved':comps['C11091'],'pins':pins['C11091']}},
      'electrical_delta':{'L11001':{'old_MPN':'XAL1010-472MED','new_MPN':'XAL1010-682MED','old_uH':4.7,'new_uH':6.8,'same_footprint':comps['L11001']['footprint']},ref:integrated[ref]},
      'reference_inventory':{'complete_existing_component_count':len(comps),'new_ref_absent_in_complete_ROOT106':True,'field_agent_reserved_refs':sorted(reserved)},
      'change_ledger':{'modified_original_lines':[{'reference':'L11001','old_sha256':hashlib.sha256(old_l.encode()).hexdigest(),'new_sha256':hashlib.sha256(new_l.encode()).hexdigest()}],'added_source_block_sha256':hashlib.sha256(block.encode()).hexdigest(),'added_uuid_ledger':uuid_ledger,'all_other_original_lines_byte_preserved':True},
      'mandatory_obligations':[x.replace('C11089physicalplacement','C11094physicalplacement') for x in prior['mandatory_obligations']],
      'source_hashes_before':before,'source_hashes_after':{p:sha(Path(p)) for p in before},'board_written':False,'native_jobs':0,'native_schematic_export_or_ERC':False}
    assert receipt['source_hashes_before']==receipt['source_hashes_after']
    (HERE/'source-correction-r2.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'root_components':len(comps),'power_entry_components':len(integrated),'new_reference':ref,'schematic_sha256':sha(sch),'source_original_unchanged':True,'normal_conservative_CORE_A':prior['source_load_cases']['conservative_module3p6_plus_AUX']['total_CORE_A']}))
if __name__=='__main__':main()
