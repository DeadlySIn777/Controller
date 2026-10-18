"""Source26 four-channel divider/buffer/filter study with unchanged TI OPA model.

This is a partial path: ideal reference, ideal power, protected input boundary,
and a 1 Mohm ADC load approximation. It cannot qualify the ADC or entire board.
"""
from pathlib import Path
import argparse, itertools, json, math, re, shutil, sys
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path.cwd() / 'tools'))
import characterize_stepgen12 as h

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out', type=Path, required=True)
ap.add_argument('--quick', action='store_true')
ap.add_argument('--rshunt', type=float, default=1e12)
ap.add_argument('--max-step-ns', type=float, default=5.0)
args = ap.parse_args()
assert 1e11 <= args.rshunt <= 1e14 and .5 <= args.max_step_ns <= 5
root = Path.cwd()
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=False)
source = root / 'hardware/motherboard/design.json'
native = root / 'hardware/motherboard/netlist.xml'
section = root / 'hardware/motherboard_analog_input/design.json'
base = root / 'reports/pre-hardware-characterization-20261001'
opa = base / 'AI-active-model-discovery-r01/SBOMA34/OPAx197.LIB'
ina = base / 'INA149-active-model-discovery-r01/SBOMC47/ina149.lib'
assert h.sha(opa) == 'fc5b020e63346e511bd808bf41c856b0150b000bcf8a41fe00eeececb1f422a5'
assert h.sha(ina) == '7adccaf61abbb093980aa6fe6604bea72068541cf4112141e22aaaa79a463c8b'
frozen = {str(p): h.sha(p) for p in (source, native, section, opa, ina, Path(__file__), Path(h.__file__))}
retained = out / 'retained-inputs'
retained.mkdir()
for i, p in enumerate(map(Path, frozen)):
    shutil.copyfile(p, retained / (str(i) + '-' + p.name))
parts = json.loads(source.read_text())['components']
block = json.loads(section.read_text())
netnodes = {}
for net in ET.parse(native).getroot().find('nets'):
    for node in net.findall('node'):
        netnodes[node.attrib['ref'], node.attrib['pin']] = net.attrib['name'].split('/')[-1]
channels = []
for ch in block['channels']:
    i = ch['channel']; pins = ch['buffer_pins']
    assert parts[ch['ina_ref']]['mpn'] == 'INA149AIDR'
    assert parts[ch['ina_ref']]['pins'] == {
        '1': 'AI_REF_2V5', '2': ch['terminal_n'], '3': ch['protected_p'],
        '4': 'AI_AGND', '5': 'AI_REF_2V5', '6': ch['shifted'], '7': 'AI_15V', '8': None}
    assert parts['U14713']['mpn'] == 'OPA4197IPWR'
    assert [parts['U14713']['pins'][str(pin)] for pin in pins] == [ch['buffered'], ch['buffered'], ch['scaled']]
    paths = [(ch['shifted'], ch['scaled'], 'TNPW060310K0BEEA', 10000),
             (ch['scaled'], 'AI_AGND', 'TNPW060310K0BEEA', 10000),
             (ch['buffered'], ch['adc_input'], 'CRCW060347R0FKEA', 47)]
    refs = [ch['ina_ref'], 'U14713']
    for n1, n2, mpn, value in paths:
        found = [(r, c) for r, c in parts.items() if c.get('kind') == 'R' and c.get('pins') == {'1': n1, '2': n2}]
        assert len(found) == 1
        ref, comp = found[0]
        assert comp['mpn'] == mpn and comp['resistance_ohm'] == value
        refs.append(ref)
    found = [(r, c) for r, c in parts.items() if c.get('kind') == 'C' and c.get('pins') == {'1': ch['adc_input'], '2': 'AI_AGND'}]
    assert len(found) == 1
    ref, comp = found[0]
    assert comp['mpn'] == 'GRM1885C1H222JA01D' and math.isclose(comp['capacitance_f'], 2.2e-9)
    refs.append(ref)
    for ref in refs:
        for pin, net in parts[ref]['pins'].items():
            if net is not None:
                assert netnodes[ref, pin] == net, (ref, pin)
    assert parts['U14734']['mpn'] == 'ADS8684AIDBTR'
    assert parts['U14734']['pins'][str([16,18,21,23][i])] == ch['adc_input']
    channels.append(dict(channel=i, checked_references=refs, model_pin_order={'INA149': ['3','2','5','1','7','4','6'], 'OPA4197_core': [str(pins[2]),str(pins[1]),'4','11',str(pins[0])]}))

prefix = ['wsl.exe', '-d', 'GarciaMechBuilder']
version = h.run(out, 'ngspice-version', prefix + ['--', 'ngspice', '--version'])
assert version['returncode'] == 0
results = []
matrix = list(itertools.product([14.39,15,15.61], [25,55], [-1,1]))
if args.quick: matrix = matrix[:1]
for index, (rail, temp, corner) in enumerate(matrix):
    case = out / f'case-{index:02}'
    case.mkdir()
    # Normal actual AGND=0 coordinate; the isolated OPA buffer model converges here.
    gauge = 0.0
    rhi = 10000*(1+corner*.001)*(1+corner*25e-6*(temp-25))
    rlo = 10000*(1-corner*.001)*(1-corner*25e-6*(temp-25))
    rf = 47*(1+corner*.01)*(1+corner*100e-6*(temp-25))
    cf = 2.2e-9*(1+corner*.05)*(1+corner*30e-6*(temp-25))
    lines = ['Source26 buffer-only partial path; unchanged TI OPA model; ideal upstream boundary',
             f'.include "{h.linux_path(opa)}"', f'.include "{h.linux_path(ina)}"',
             f'VGROUND AGND 0 {gauge:.16g}', f'VCC VCC AGND {rail}', 'VREF REF AGND 2.5',
             f'.temp {temp}', f'.options method=gear maxord=2 rshunt={args.rshunt:.16g} itl1=500 itl4=500']
    settings = []
    for i, (cm, initial, final) in enumerate([(-10,0,10),(-10,10,0),(10,4,6),(10,6,4)]):
        settings.append(dict(channel=i, common_mode_V=cm, initial_differential_V=initial, final_differential_V=final))
        lines += [f'VD{i} D{i} 0 DC {initial} AC 1 PULSE({initial} {final} 5u 10n 10n 40u 80u)',
                  f'BP{i} P{i} AGND V={cm}+v(D{i})/2', f'BN{i} N{i} AGND V={cm}-v(D{i})/2',
                  f'BSHIFT_APPROX{i} SHIFT{i} AGND V=v(D{i})+2.5',
                  f'RUP{i} SHIFT{i} SCALED{i} {rhi:.16g}', f'RDOWN{i} SCALED{i} AGND {rlo:.16g}',
                  f'XBUF{i} SCALED{i} BUF{i} VCC AGND BUF{i} OPAx197',
                  f'RFILTER{i} BUF{i} ADC{i} {rf:.16g}', f'CFILTER{i} ADC{i} AGND {cf:.16g}',
                  f'RADC_APPROX{i} ADC{i} AGND 1Meg']
    lines += ['.control','set noaskquit','set wr_singlescale','set wr_vecnames','ac dec 100 10 10Meg']
    for i in range(4):
        lines += [f'let gain{i}=mag(v(adc{i})-v(agnd))', f'meas ac fc{i} when gain{i}={rlo/(rhi+rlo)/(2**.5):.16g} fall=1']
    lines += [f'tran {args.max_step_ns:.16g}n 40u']
    for i in range(4): lines += [f'let output{i}=v(adc{i})-v(agnd)']
    lines += ['wrdata transient.txt ' + ' '.join(f'v(d{i}) output{i}' for i in range(4)), 'quit','.endc','.end']
    deck = case / 'actual-path.cir'; deck.write_text('\n'.join(lines)+'\n')
    run = h.run(case, 'ngspice', prefix + ['--cd', h.linux_path(case),'--','ngspice','-n','-D','ngbehavior=psa','-b',h.linux_path(deck)])
    log = Path(run['log']).read_text()
    errors = re.findall(r'(?im)^.*(?:error:|simulation\(s\) aborted|timestep too small|no such vector|failed!).*$',log)
    warnings = re.findall(r'(?im)^warning:.*$',log)
    waveform = case / 'transient.txt'
    parsed = []
    if waveform.exists():
        for row in waveform.read_text().splitlines()[1:]:
            vals = [float(x) for x in row.split()]
            assert len(vals) == 9 and all(math.isfinite(x) for x in vals)
            parsed.append(vals)
    measurements = {k:float(v) for k,v in re.findall(r'(?m)^\s*(fc\d)\s*=\s*([\d.eE+-]+)',log)}
    checks = []
    if parsed and parsed[-1][0] >= 39.999e-6:
        for i,s in enumerate(settings):
            col = 2+2*i
            final_samples = [r[col] for r in parsed if 35e-6 <= r[0] <= 40e-6]
            observed_final = sum(final_samples)/len(final_samples)
            ideal_final = (s['final_differential_V']+2.5)*rlo/(rhi+rlo)*1e6/(1e6+rf)
            post = [(r[0],r[col]) for r in parsed if r[0]>=5.01e-6]
            # This is a settling screen, not ENOB or absolute calibration.
            half_12bit_input_span = (10/2)/4096/2
            outside = [t for t,v in post if abs(v-observed_final)>half_12bit_input_span]
            settling = (max(outside)-5.01e-6) if outside else 0.0
            ripple = max(final_samples)-min(final_samples)
            checks.append(dict(channel=i, observed_final_V=observed_final, nominal_final_with_passive_corner_V=ideal_final,
                               modeled_untrimmed_residual_V=observed_final-ideal_final, settle_to_final_half_12bit_span_s=settling,
                               settling_target_screen_s=30e-6, final_peak_to_peak_V=ripple,
                               min_after_step_V=min(v for t,v in post),max_after_step_V=max(v for t,v in post),
                               passed=settling<30e-6 and ripple<half_12bit_input_span and abs(observed_final-ideal_final)<.01 and all(0<v<10.24 for t,v in post)))
    passed = run['returncode']==0 and not errors and len(measurements)==4 and len(checks)==4 and all(c['passed'] for c in checks)
    result = dict(case=index, passed=passed, rail_V=rail, temperature_C=temp, correlated_passive_corner=corner,
                  gauge_offset_V=gauge, solver_rshunt_ohm=args.rshunt, max_step_ns=args.max_step_ns, settings=settings, Rupper_ohm=rhi,Rlower_ohm=rlo,
                  Rfilter_ohm=rf,Cfilter_F=cf, errors=errors,warnings=warnings, measurements=measurements, channel_checks=checks,
                  deck_sha256=h.sha(deck),waveform_sha256=h.sha(waveform)if waveform.exists()else None,run=run)
    results.append(result);h.write(out/'checkpoint.json',dict(cases=results))
    print(json.dumps(dict(case=index,passed=passed,errors=len(errors),checks=checks)),flush=True)
    if not passed: break

unchanged = all(h.sha(Path(p))==v for p,v in frozen.items())
passed = unchanged and len(results)==len(matrix) and all(r['passed'] for r in results)
receipt = dict(passed=passed,numerical_shunt_ohm=args.rshunt,max_step_ns=args.max_step_ns,source_unchanged=unchanged,input_sha256=frozen,source_channels=channels,tool=version,
    cases=results,expected_cases=len(matrix),quick_mode=args.quick,manufacturing_ready=False,physical_qualified=False,
    scope='Actual Source26 10k/10k divider -> OPA4197 unity buffer -> 47ohm/2.2nF filter; four independent active OPA macromodel cores. IDEAL INA149 output boundary and 1Mohm ADC load approximation. The actual INA149 macromodel FAILED the attempted full-path study; this scoped buffer run does not close that failure.',
    solver_notes=['Unmodified OPAx197 model used under ngspice PSA compatibility, at actual AGND=0. INA149 is intentionally absent because its complete four-channel model did not converge. Ideal voltage boundary explicitly substitutes ONLY that upstream block and receives no device validation claim.',
                  'Gear2 and the recorded numerical shunt/max step on simulator nodes are explicit. Shunt/timestep sensitivity requires independent comparison before relying on precision limits.',
                  'Convergence fallback warnings retained; actual analysis abort/missing measurements always fail despite ngspice exit0.'],
    limitations=['Not the complete analog input circuit: NO INA149 model, TBU/current relay/burden/terminal surge behavior',
                 'No actual ADC macro: official ADS868x model is encrypted TINA library; 1Mohm approximation has no sample/hold, reference, quantization or conversion noise',
                 'Reference and supplies ideal, so no rail coupling/reference errors/brownout/startup',
                 'Four OPA cores lack quad-package crosstalk/shared-rail thermal coupling',
                 'Manufacturer nominal models do not guarantee IC process min/max corners; passive corner signs sampled, not exhaustive Monte Carlo',
                 '25C/55C only; full0..55C passive temperature dependency incomplete',
                 'No actual PCB parasitic extraction/cables/EMC/target acquisition firmware',
                 'Settling relative to final voltage is not absolute accuracy/ENOB or a hardware rate rating'])
h.write(out/'receipt.json',receipt)
assert passed, 'Partial active circuit sweep failed; inspect actual retained analyses'
