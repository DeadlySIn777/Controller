"""Exercise only the proposal reader; never call the parent CAD generator."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import runpy
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    target = OUT/'guard-review.json'
    if target.exists():raise RuntimeError('Preserve existing guard receipt')
    builder = ROOT/'tools/hardware_build_motion_card.py'
    source = ROOT/'hardware/motion_card/oscillator-footprint-promotion.json'
    old = [p for p in (ROOT/'hardware/fpga_core').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    old += [ROOT/'hardware/motion_card/design.json',ROOT/'hardware/motion_card/netlist.xml',
            ROOT/'hardware/motion_card/bom.csv',ROOT/'hardware/motion_card/fpga_core.kicad_sch']
    old += list((ROOT/'hardware/board_review/revisions').glob('*/*.kicad_pcb'))
    before = {p.relative_to(ROOT).as_posix():sha(p) for p in old}
    namespace = runpy.run_path(str(builder),run_name='oscillator_guard_review')
    load = namespace['load_oscillator_footprint_promotion']
    original = load()
    tests = []
    cases = {
        'wrong_exact_mpn':lambda p:p.update(mpn='ASE-50.000MHZ-K-C-T'),
        'wrong_pad_order':lambda p:p['expected_source_pins'].update({'2':'FPGA_CLK_SOURCE','3':'LOGIC_GND'}),
        'different_footprint':lambda p:p.update(footprint='Oscillator:unknown'),
        'process_approval_claim':lambda p:p.update(assembly_process_qualified=True),
        'hidden_roundrect_difference':lambda p:p['land_shape_difference'].update(native_stock_shape='rectangular'),
        'stale_manufacturer_hash':lambda p:p['source_sha256'].update({'research/fpga-core/ase.pdf':'0'*64}),
    }
    fixture_dir = OUT/'test-artifacts'
    fixture_dir.mkdir(exist_ok=True)
    for name,mutate in cases.items():
        proposed = deepcopy(original)
        mutate(proposed)
        path = fixture_dir/(name+'.json')
        path.write_text(json.dumps(proposed,indent=2)+'\n',encoding='utf-8')
        try:
            load(path)
        except ValueError as error:
            tests.append({'case':name,'rejected':True,'message':str(error)})
        else:
            raise AssertionError('Unsafe proposal accepted: '+name)
    after = {p.relative_to(ROOT).as_posix():sha(p) for p in old}
    assert before == after
    result = {'schema_version':1,'positive_load_passed':True,'six_negative_controls_rejected':tests,
              'builder_sha256':sha(builder),'ledger_sha256':sha(source),
              'protected_inputs_before':before,'protected_inputs_after':after,
              'protected_inputs_unchanged':True,'parent_generator_run':False,
              'pcb_edited':False,'manufacturing_ready':False}
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'positive_load_passed':True,'negative_controls_rejected':len(tests),
                      'protected_files_unchanged':len(before),'parent_generator_run':False}))


if __name__ == '__main__':main()
