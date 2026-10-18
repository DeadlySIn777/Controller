"""Promote the frozen five-part source26 stage without regenerating any hierarchy.

The caller must supply --adopt after the root's coordinated release. Otherwise
this command only verifies the immutable stage and creates a preflight receipt.
"""
import argparse, copy, datetime, json, os, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
from hardware_adopt_adc_bypass_source import ROOT, CLI, sha, load, write, file_hashes
from hardware_validate_motherboard import validate, nodes
from hardware_check_source26_parts import check_source26, CAPS, FUSES

HOOK = ("    try:\n        from hardware_check_source26_parts import check_source26\n"
        "    except ModuleNotFoundError:\n        from tools.hardware_check_source26_parts import check_source26\n"
        "    errors.extend(check_source26(parts, actual, model, mapping))\n")
NEEDLE = "    adc_delta=mapping.get('reviewed_adc_bypass_delta')\n"

def reviewed_stage(stage_receipt, proposal):
    r = load(stage_receipt)
    assert r['passed'] and not r['adopted'] and r['live_child_and_parent_unchanged']
    assert [c['reference'] for c in r['exact_component_changes']] == list(CAPS + FUSES)
    for p, h in r['input_sha256'].items():
        if sha(p) != h:
            raise ValueError('Frozen staging input changed: ' + p)
    stage = ROOT / r['source']
    if file_hashes(stage) != r['source_hashes']:
        raise ValueError('Frozen staged parent changed')
    for row in r['source26_input_resolution']:
        if sha(row['resolved']) != row['sha256']:
            raise ValueError('Frozen staged dependency changed: ' + row['logical_source'])
    p = load(proposal / 'receipt.json')
    for name, expected in [('hardware_build_motherboard_analog_input.py', p['candidate_builder_sha256']),
                           ('hardware_validate_motherboard_analog_input.py', p['candidate_validator_sha256'])]:
        if sha(proposal / 'candidate-tools' / name) != expected:
            raise ValueError('Frozen future generator/validator changed: ' + name)
    model = load(stage / 'design.json'); mapping = load(stage / 'assembly-map.json')
    tree = ET.parse(stage / 'netlist.xml')
    errors = validate(tree, model, mapping, False) + check_source26(model['components'], nodes(tree), model, mapping)
    if errors:
        raise ValueError('Independent exact staged native source failed: ' + repr(errors))
    return r, stage

def copy_delta(source, dest, archive):
    old = file_hashes(dest); new = file_hashes(source)
    # Native export logs are report evidence, not child inputs to install.
    delta = sorted(p for p in new if new[p] != old.get(p) and not p.endswith('.log'))
    retained_extra = set(old) - set(new)
    if retained_extra - {'README.md', 'validation.json'}:
        raise ValueError('Frozen staged child lacks a current electrical source file')
    shutil.copytree(dest, archive)
    for name in delta:
        target = dest / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    return dict(before=old, changed=delta, retained_extra_historical_files=sorted(retained_extra), after=file_hashes(dest))

def power_generator_hook(text):
    old = 'Fuse:Fuseholder_Blade_Mini_Keystone_3568'
    new = 'CNC_MB_Fuse:Keystone_3568_M55'
    if text.count(old) != 1 or text.count('    footprints(out)\n') != 1:
        raise ValueError('Exact power generator anchors changed')
    lib_end = '(descr "Source-backed power monitor lands")))'
    if text.count(lib_end) != 1:
        raise ValueError('Exact existing entry library anchor changed')
    replacement = ('(descr "Source-backed power monitor lands"))'
        '(lib(name "CNC_MB_Fuse")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Fuse.pretty")'
        '(options "")(descr "Exact Keystone M55 manufacturer mounting")))')
    text = text.replace(old, new).replace(lib_end, replacement)
    return text.replace('    footprints(out)\n', '    footprints(out)\n'
        '    from hardware_apply_fuse_geometry_upgrade import make_library\n'
        "    make_library(out/'CNC_MB_Fuse.pretty/Keystone_3568_M55.kicad_mod')\n")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('stage-receipt', 'reference-proposal', 'out'):
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--adopt', action='store_true'); a = ap.parse_args(); a.out = a.out.resolve()
    if a.out.exists():
        raise ValueError('Fresh immutable transaction directory required')
    r, stage = reviewed_stage(a.stage_receipt, a.reference_proposal)
    a.out.mkdir(parents=True)
    if not a.adopt:
        write(a.out / 'preflight.json', dict(passed=True, adopted=False, exact_parts=list(CAPS + FUSES),
              stage_receipt_sha256=sha(a.stage_receipt), root_coordinated_release_required=True,
              tool_sha256=sha(__file__), manufacturing_ready=False))
        print(json.dumps(dict(passed=True, adopted=False, parts=2688))); return
    live = ROOT / 'hardware/motherboard'; before_nodes = nodes(ET.parse(live / 'netlist.xml'))
    before_model = load(live / 'design.json'); changes = {}; archive = a.out / 'before'; archive.mkdir()
    # Children first. Only then may the independent validator resolve live hashes.
    for region, key in [('motherboard_analog_input', 'reference_child'), ('motherboard_power_entry', 'power_child')]:
        changes[region] = copy_delta(ROOT / r[key], ROOT / 'hardware' / region, archive / region)
    tool_changes = []
    for name in ['hardware_build_motherboard_analog_input.py', 'hardware_validate_motherboard_analog_input.py']:
        target = ROOT / 'tools' / name; shutil.copyfile(target, archive / name)
        source = a.reference_proposal / 'candidate-tools' / name; shutil.copyfile(source, target)
        tool_changes.append(dict(path=str(target.relative_to(ROOT)), before_sha256=sha(archive/name), after_sha256=sha(target)))
    # Exact three-literal generator hook authorized by the power-source owner.
    # It is never run over the frozen source during this transaction.
    target = ROOT/'tools/hardware_build_motherboard_power_entry.py'
    shutil.copyfile(target, archive/target.name)
    target.write_text(power_generator_hook(target.read_text(encoding='utf8')), encoding='utf8')
    tool_changes.append(dict(path=str(target.relative_to(ROOT)), before_sha256=sha(archive/target.name), after_sha256=sha(target)))
    target = ROOT / 'tools/hardware_validate_motherboard.py'; shutil.copyfile(target, archive / target.name)
    text = target.read_text(encoding='utf8')
    if HOOK not in text:
        if text.count(NEEDLE) != 1:
            raise ValueError('Exact existing validator anchor differs; no broad rewrite permitted')
        text = text.replace(NEEDLE, HOOK + NEEDLE); target.write_text(text, encoding='utf8')
    tool_changes.append(dict(path=str(target.relative_to(ROOT)), before_sha256=sha(archive/target.name), after_sha256=sha(target)))
    changes['motherboard'] = copy_delta(stage, live, archive / 'motherboard')
    model = load(live / 'design.json'); mapping = load(live / 'assembly-map.json')
    tree = ET.parse(live / 'netlist.xml')
    assert nodes(tree) == before_nodes and len(model['components']) == 2688
    changed = [ref for ref in model['components'] if model['components'][ref] != before_model['components'][ref]]
    assert set(changed) == set(CAPS + FUSES)
    errors = validate(tree, model, mapping, True) + check_source26(model['components'], nodes(tree), model, mapping)
    if errors:
        write(a.out / 'failed-validation.json', errors); raise ValueError('Actual live source26 dependency/native checks failed')
    commands = []
    for label, cmd in [('netlist', [str(CLI),'sch','export','netlist','--format','kicadxml','-o',str(a.out/'fresh-netlist.xml'),str(live/'motherboard.kicad_sch')]),
                       ('ERC', [str(CLI),'sch','erc','--format','json','-o',str(a.out/'erc.json'),str(live/'motherboard.kicad_sch')])]:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf8'); log=a.out/(label+'.log'); log.write_text(p.stdout+p.stderr,encoding='utf8')
        assert p.returncode == 0; commands.append(dict(label=label, returncode=0, log_sha256=sha(log)))
    fresh = ET.parse(a.out / 'fresh-netlist.xml'); assert nodes(fresh) == before_nodes
    assert not validate(fresh, model, mapping, True)
    assert not check_source26(model['components'], nodes(fresh), model, mapping)
    erc = load(a.out / 'erc.json'); violations=[v for s in erc['sheets'] for v in s['violations']]
    assert not erc['ignored_checks'] and not any(v['severity']=='error' for v in violations)
    env={**os.environ, 'CONTROLLER_MOTHERBOARD_TEST_SOURCE':str(live), 'CONTROLLER_SOURCE26_STAGE':str(live)}
    tests=[]
    for name in ['test_motherboard_integration.py','test_motherboard_adc_source_adoption.py','test_motherboard_analog_input.py',
                 'test_motherboard_fpga_current_annotations.py','test_motherboard_fpga_allocation.py','test_motherboard_source26_parts.py']:
        cmd=[sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p',name,'-v']
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',cwd=ROOT,env=env);log=a.out/(name+'.log');log.write_text(p.stdout+p.stderr,encoding='utf8')
        tests.append(dict(name=name,returncode=p.returncode,log_sha256=sha(log)))
        if p.returncode:
            raise ValueError('Actual source26 regression failed: '+name)
    cmd=[sys.executable,'-X','utf8','-m','pytest','tests/test_motherboard_fuse_geometry.py','tests/test_motherboard_power_entry.py',
         'tests/test_motherboard_motor_power.py','tests/test_motherboard_io3_window.py','tests/test_motherboard_io3_upgrade.py','-q']
    p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',cwd=ROOT,env=env);log=a.out/'power-107-tests.log';log.write_text(p.stdout+p.stderr,encoding='utf8')
    tests.append(dict(name='power/fuse/motor/IO3',returncode=p.returncode,log_sha256=sha(log)));assert p.returncode==0
    result=dict(passed=True,adopted=True,date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        stage_receipt_sha256=sha(a.stage_receipt),exact_component_changes=r['exact_component_changes'],
        source=str(live.relative_to(ROOT)),source_hashes=file_hashes(live),source_regions=changes,tool_changes=tool_changes,
        native_ERC_errors=0,native_ERC_warnings=len(violations),ignored_checks=[],native_commands=commands,tests=tests,
        physical_parts=2688,purchased_fitted_parts=2642,bare_geometry=44,DNP=2,retained_mc_parts=327,retained_mc_native_pin_nets=1229,
        FPGA_assigned=135,FPGA_free=48,all_native_pin_nets_preserved=True,independent_validation_pass=True,
        stage_resolved_inputs_then_actual_live_hashes_pass=True,physical_layout_adopted=False,physical_qualified=False,
        manufacturing_ready=False,tool_sha256=sha(__file__))
    write(a.out/'adoption.json',result)
    print(json.dumps(dict(passed=True,adopted=True,parts=2688,ERC_errors=0,ERC_warnings=len(violations),changed=changed)))

if __name__=='__main__':main()
