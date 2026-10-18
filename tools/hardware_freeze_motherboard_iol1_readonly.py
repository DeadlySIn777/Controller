"""Record completed disconnected evidence, without target execution claims."""
from pathlib import Path
import hashlib,json,subprocess,sys,re,urllib.request
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/motherboard-iol1-firmware-20260930'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=REPORT/'readonly-r01'
    if out.exists():raise SystemExit('Immutable receipt directory exists')
    build=REPORT/'target-r09';r=json.loads((build/'receipt.json').read_text())
    assert r['tool_exit']==0 and r['inputs_unchanged'] and r['host_C_checks']==5389
    assert r['backend_synthesis'] and not r['target_execution']
    # The only post-build change fixes the documentation's ST license label.
    changed=[x['path'] for x in r['inputs'] if digest(ROOT/x['path'])!=x['sha256']]
    assert changed==['firmware/motherboard_iol1_readonly/README.md'],changed
    old=(build/'inputs'/changed[0]).read_text();new=(ROOT/changed[0]).read_text()
    assert new==old.replace('ST BSD and ARM Apache2 licenses','ST and ARM Apache2 licenses')
    hist=json.loads((REPORT/'historical-r01/receipt.json').read_text())
    assert hist['passed'] and hist['checks']==60 and not hist['source_changed_during_run']
    out.mkdir()
    tests=['tests/test_motherboard_iol1_readonly.py','tests/test_motherboard_iol1_clock_taps.py',
           'tests/test_motherboard_io_control.py','tests/test_motherboard_acc_control.py',
           'tests/test_motherboard_identity_io.py','tests/test_motherboard_watchdogs.py']
    p=subprocess.run([sys.executable,'-X','utf8','-m','pytest',*tests,'-q'],cwd=ROOT,capture_output=True,text=True)
    (out/'host-tests.log').write_text(p.stdout+p.stderr)
    assert p.returncode==0 and '154 passed' in p.stdout,p.stdout+p.stderr
    from hardware_validate_motherboard_iol1_firmware import validate
    review=validate();assert review['ok'];(out/'source-review.json').write_text(json.dumps(review,indent=2)+'\n')
    # Retain exact primary simulator-only headers/license provenance separately.
    v=[]
    for name in ['vpi_user.h','_pli_types.h.in','COPYING']:
        url='https://raw.githubusercontent.com/steveicarus/iverilog/v13_0/'+name
        with urllib.request.urlopen(url,timeout=30) as q:raw=q.read()
        path=ROOT/'firmware/motherboard_iol1_readonly/vendor/Icarus'/name
        assert raw==path.read_bytes(),name
        v.append(dict(path=path.relative_to(ROOT).as_posix(),url=url,sha256=digest(path),
                      target_linked=False,internal_simulator_only=True))
    (out/'icarus-source-receipt.json').write_text(json.dumps(v,indent=2)+'\n')
    pins=json.loads((ROOT/'reports/motherboard-watchdog-20260930/pin-map-r01.json').read_text())
    assert pins['passed'];pins['wrapper']='gateware/motherboard_iol1_target_bringup/cnc_motherboard_iol1_target_bringup.v'
    pins['same_ports_as_historical_wrapper']=True
    (out/'pin-map.json').write_text(json.dumps(pins,indent=2)+'\n')
    synth=json.loads((build/'synthesized.json').read_text())
    from collections import Counter
    stats=dict(Counter(c['type'] for c in synth['modules']['cnc_motherboard_iol1_target_bringup']['cells'].values()))
    paths=[p for d in ['firmware/motherboard_iol1_readonly','gateware/motherboard_iol1_target_bringup'] for p in (ROOT/d).rglob('*') if p.is_file()]
    paths += [ROOT/p for p in tests]+[ROOT/'tools/hardware_check_motherboard_iol1_firmware.py',ROOT/'tools/hardware_validate_motherboard_iol1_firmware.py',Path(__file__).resolve()]
    paths += [build/'receipt.json',build/'synthesized.json',REPORT/'historical-r01/receipt.json',REPORT/'clock-taps-r01/receipt.json',REPORT/'vendor-source-receipt.json']
    receipt=dict(schema_version=1,passed=True,scope='four actual fitted-node read-only prototype images; held-reset acquisition is explicitly unavailable',
      source_review=review,host_pytest=154,host_C=5389,hdl_C_checks=78,M_pulses=5,O_pulses=77,
      target_compiled_nodes=4,target_sizes=r['target_sizes'],synthesis_cells=stats,
      backend_synthesis=True,vendor_fit_timing_bitstream=False,target_executed=False,
      target_MMIO_simulated=False,physical_qualified=False,factory_options_provisioned=False,
      twelve_axis_runtime=False,production_firmware=False,manufacturing_ready=False,
      historical_checks={'endpoint_default':252,'endpoint_ABI2':27,'permission':49,'watchdog_synthetic':60},
      documentation_only_postbuild_delta=changed,ST_license='Apache-2.0, retained primary LICENSE.md',
      engineering_gates=['Production target CRC/configuration/commissioning and output-authority implementation',
       'Live ACC acquisition requires separate safe commissioning/reset release; current held-reset validity stays unavailable',
       'Commercial identity/configuration/bootloader and target option-byte provisioning',
       'Vendor package fit, routed timing and bitstream'],
      physical_gates=['SPI/timer synchronizer/ISR/reply deadlines on all four loaded fitted nodes',
       'Actual IWDG reset and end-to-end20ms inhibit measurements, voltage/thermal/EMC/fault injection'],
      inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=digest(p)) for p in sorted(set(paths))])
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['passed','host_pytest','host_C','hdl_C_checks','synthesis_cells','target_executed','production_firmware']},indent=2))
if __name__=='__main__':main()
