"""Freeze the minimal ADC bypass proposal and build an isolated native child."""
from __future__ import annotations
import argparse, hashlib, json, shutil, urllib.request, importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CHANGES={
 'C14744':dict(mpn='885012206052',value='1000nF16V',capacitance_f=1e-6,voltage_rating_v=16,
               footprint='Capacitor_SMD:C_0603_1608Metric',role='ADC AVDD pin9 local1uF X7R; direct same-side no-via path'),
 'C14745':dict(mpn='885012206052',value='1000nF16V',capacitance_f=1e-6,voltage_rating_v=16,
               footprint='Capacitor_SMD:C_0603_1608Metric',role='ADC AVDD pin30 local1uF X7R; direct same-side no-via path'),
 'C14746':dict(mpn='GRM21BR71A106MA73L',value='10000nF10V',capacitance_f=10e-6,voltage_rating_v=10,
               footprint='Capacitor_SMD:C_0805_2012Metric',role='ADC DVDD pin34 local10uF X7R; direct same-side no-via path')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def correction():return dict(source='TI SBAS680 p70 §11.1; p9 reference table; p29/31 reference minimums',
    nominal_avdd_bypass_uf=1,nominal_dvdd_bypass_uf=10,
    source_references=list(CHANGES),capacitor_count_unchanged=True,all_capacitor_pin_nets_unchanged=True,
    direct_AVDD_DVDD_REFCAP_no_via_routes_required=True,
    REFIO_same_side_direct_route_is_engineering_target=True,
    existing_REFIO_REFCAP_nominal_banks_uf=[22,1],reference_minimum_effective_uf=10,
    reference_numeric_ESR_limit_in_primary=False,reference_nominal_maximum_not_specified=True,
    reference_effective_bias_age_temp_ESR_qualified=False,all_seven_local_ADC_caps_generic_router_excluded=True,
    additional_AI5_nominal_supply_capacitance_uf=11.7,
    LDO_startup_discharge_transient_new_capacitive_loading_qualified=False)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);before=a.out/'before';before.mkdir();sources=a.out/'primary';sources.mkdir()
    paths=[ROOT/'tools/hardware_build_motherboard_analog_input.py',ROOT/'tools/hardware_validate_motherboard_analog_input.py',
           ROOT/'tests/test_motherboard_analog_input.py']+list((ROOT/'hardware/motherboard_analog_input').rglob('*'))
    paths=[p for p in paths if p.is_file()];hashes={str(p.resolve()):sha(p)for p in paths}
    for p in paths:
        dest=before/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    originals=['reports/motherboard-analog-input-20260930/sources/ads8684a.pdf',
               'reports/motherboard-analog-input-20260930/sources/ads8684a.txt',
               'research/fpga-core/885012206052.pdf','research/fpga-core/885012206052.txt']
    for rel in originals:shutil.copyfile(ROOT/rel,sources/Path(rel).name)
    url='https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM21BR71A106MA73-01A.pdf'
    with urllib.request.urlopen(url,timeout=45)as response:data=response.read()
    if not data.startswith(b'%PDF'):raise ValueError('Official exact Murata response is not PDF')
    (sources/'GRM21BR71A106MA73.pdf').write_bytes(data)
    old=json.loads((ROOT/'hardware/motherboard_analog_input/design.json').read_text(encoding='utf8'))
    parent=json.loads((ROOT/'hardware/motherboard/design.json').read_text(encoding='utf8'))
    for ref,change in CHANGES.items():
        if not any(c.get('mpn')==change['mpn'] for c in parent['components'].values()):
            raise ValueError('Proposed MPN is not already fitted: '+change['mpn'])
        if old['components'][ref]['pins']!={'1':'AI_5V','2':'AI_AGND'}:
            raise ValueError('Old local ADC topology differs')
    proposal=dict(schema_version=1,input_hashes=hashes,changes=[dict(reference=r,
        before=old['components'][r],changed_fields=c,after={**old['components'][r],**c})for r,c in CHANGES.items()],
        scope='Exactly three local ADC capacitors; same count/pins/nets. C14746 footprint grows0603→0805. No reference-bank or other part changes.',
        primary_sources=[dict(path=str(p.resolve()),sha256=sha(p))for p in sources.iterdir()],
        primary_url=url,existing_verified_MPN_reuse=True,correction=correction(),
        proposed_not_adopted=True,source_or_PCB_mutated=False,manufacturing_ready=False)
    write(a.out/'proposal.json',proposal)
    builder=(ROOT/'tools/hardware_build_motherboard_analog_input.py').read_text(encoding='utf8')
    needle=" for pin in [9,30,34]:cap(s5,g,100,'ADC supplypin'+str(pin)+'local bypass')"
    if builder.count(needle)!=1:raise ValueError('Exact old builder statement not unique')
    replacement=" for pin in [9,30,34]:\n  ref=cap(s5,g,100,'ADC supplypin'+str(pin)+'local bypass')\n  parts[ref].update(ADC_BYPASS_CHANGES[ref])"
    builder=builder.replace(needle,replacement)
    pos="ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_analog_input'"
    builder=builder.replace(pos,"ROOT=Path("+repr(str(ROOT))+" );OUT=Path("+repr(str((a.out/'child').resolve()))+")")
    builder=builder.replace('NS=uuid.UUID(', 'ADC_BYPASS_CHANGES='+repr(CHANGES)+'\nADC_BYPASS_CORRECTION='+repr(correction())+'\nNS=uuid.UUID(',1)
    builder=builder.replace(' return d\n',' d[\'adc_bypass_correction\']=ADC_BYPASS_CORRECTION\n d[\'revision\']=\'MB-AI-r03-ADC-local-bypass\'\n return d\n',1)
    candidate=a.out/'hardware_build_motherboard_analog_input.proposed.py';candidate.write_text(builder,encoding='utf8')
    import sys
    sys.path.insert(0,str(ROOT/'tools'))
    spec=importlib.util.spec_from_file_location('adc_proposal',candidate);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.build(a.out/'child')
    actual=json.loads((a.out/'child/design.json').read_text(encoding='utf8'))
    changed=[ref for ref in old['components']if old['components'][ref]!=actual['components'][ref]]
    if changed!=list(CHANGES)or set(actual['components'])!=set(old['components']):raise ValueError('Minimal capacitor-only proposal changed other parts')
    if any(actual['components'][r]['pins']!=c['pins']for r,c in old['components'].items()):raise ValueError('Proposal changed a source pin')
    for p,expected in hashes.items():
        if sha(p)!=expected:raise ValueError('Historical input changed while staging')
    write(a.out/'stage-receipt.json',dict(input_hashes=hashes,proposal_sha256=sha(a.out/'proposal.json'),
        candidate_builder_sha256=sha(candidate),staged_design_sha256=sha(a.out/'child/design.json'),
        exact_changed_references=changed,all_pins_parts_count_preserved=True,live_source_or_PCB_mutated=False))
    print(json.dumps(dict(exact_changed_references=changed,physical_parts=actual['fitted_component_count'],live_source_or_PCB_mutated=False)))
if __name__=='__main__':main()
