"""Actual Source26 four-channel RC filter corners in ngspice.

This deliberately stops at ideal buffer/ADC boundaries. It does not qualify
the OPA4197, ADS8684, protection, calibration, full temperature range or PCB.
"""
from pathlib import Path
import sys,json,math,shutil,itertools,re,argparse,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path.cwd()/'tools'))
import characterize_stepgen12 as h
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--wsl-distro',default='GarciaMechBuilder');args=ap.parse_args()
root=Path.cwd();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
source=root/'hardware/motherboard/design.json';netlist=root/'hardware/motherboard/netlist.xml'
primary=root/'reports/pre-hardware-characterization-20261001/AI-passive-manufacturer-sources-r01'
pdfs=[primary/'murata-GRM1885C1H222JA01.pdf',primary/'vishay-CRCW-20035.pdf']
assert [h.sha(p)for p in pdfs]==['6f8d8821abc96f97f136ebaf8d21f417d8d1ad2e25c7761f4749834585dffd35','27093950db7794935ec5114bb2c516173fab07738873e3daedbbc511077414d0']
frozen={str(p):h.sha(p)for p in(source,netlist,*pdfs,Path(__file__),Path(h.__file__))}
snapshot=out/'retained-inputs';snapshot.mkdir()
for p in(source,netlist,*pdfs,Path(__file__),Path(h.__file__)):shutil.copyfile(p,snapshot/p.name)
parts=json.loads(source.read_text())['components'];nodes={}
for net in ET.parse(netlist).getroot().find('nets'):
 for node in net.findall('node'):nodes[node.attrib['ref'],node.attrib['pin']]=net.attrib['name'].split('/')[-1]
channels=[]
for ch in range(4):
 start=f'AI{ch}_BUFFERED';end=f'AI{ch}_ADC_IN'
 r=[(ref,p)for ref,p in parts.items()if p.get('pins')=={'1':start,'2':end}and p.get('kind')=='R']
 c=[(ref,p)for ref,p in parts.items()if p.get('pins')=={'1':end,'2':'AI_AGND'}and p.get('kind')=='C']
 assert len(r)==len(c)==1
 rr,rp=r[0];cr,cp=c[0]
 assert rp['mpn']=='CRCW060347R0FKEA'and rp['resistance_ohm']==47 and rp['tolerance']==.01 and rp['tcr_ppm_K']==100
 assert cp['mpn']=='GRM1885C1H222JA01D'and math.isclose(cp['capacitance_f'],2.2e-9,rel_tol=1e-12)
 for ref,part in[(rr,rp),(cr,cp)]:
  for pin,net in part['pins'].items():assert nodes[ref,pin]==net,(ref,pin)
 channels.append(dict(channel=ch,resistor_ref=rr,resistor=rp,capacitor_ref=cr,capacitor=cp))
prefix=['wsl.exe','-d',args.wsl_distro,'--'];version=h.run(out,'ngspice-version',prefix+['ngspice','--version']);assert not version['returncode']
results=[]
for number,(temp,rsign,csign,rtc,ctc,amplitude)in enumerate(itertools.product((25,55),(-1,1),(-1,1),(-1,1),(-1,1),(.1,1.,5.))):
 rvalue=47*(1+rsign*.01)*(1+rtc*100e-6*(temp-25))
 cvalue=2.2e-9*(1+csign*.05)*(1+ctc*30e-6*(temp-25))
 expected_fc=1/(2*math.pi*rvalue*cvalue);expected_tau=rvalue*cvalue
 lines=[f'Source26 AI passive-only corner{number}; ideal external boundaries',f'.temp {temp}','.options reltol=1e-7 abstol=1e-12 vntol=1e-9']
 for ch in channels:
  i=ch['channel'];lines.extend([f'* actual {ch["resistor_ref"]}47ohm CRCW / {ch["capacitor_ref"]}2.2nF GRM',f'V{i} IN{i} 0 DC 0 AC 1 PULSE(0 {amplitude} 0 1p 1p 5u 10u)',f'R{i} IN{i} OUT{i} {rvalue:.16g}',f'C{i} OUT{i} 0 {cvalue:.16g}'])
 lines.extend(['.control','set noaskquit','ac dec 150 1k 100Meg'])
 for i in range(4):lines.extend([f'let m{i}=mag(v(OUT{i}))',f'meas ac f3_{i} when m{i}=0.7071067811865476 fall=1'])
 lines.append('tran 1n 2u')
 for i in range(4):lines.append(f'meas tran t63_{i} when v(OUT{i})={amplitude*(1-math.exp(-1)):.16g} rise=1')
 lines.extend(['quit','.endc','.end'])
 deck=out/f'corner-{number:03}.cir';deck.write_text('\n'.join(lines)+'\n')
 run=h.run(out,f'corner-{number:03}',prefix+['ngspice','-b',h.linux_path(deck)])
 text=Path(run['log']).read_text();measurements={k:float(v)for k,v in re.findall(r'(?m)^\s*((?:f3|t63)_\d)\s*=\s*([\d.eE+-]+)',text)}
 passed=run['returncode']==0 and len(measurements)==8 and all(math.isclose(measurements[f'f3_{i}'],expected_fc,rel_tol=.001)and math.isclose(measurements[f't63_{i}'],expected_tau,rel_tol=.001)for i in range(4))
 results.append(dict(case=number,passed=passed,temperature_C=temp,step_amplitude_V=amplitude,R_tolerance_sign=rsign,C_tolerance_sign=csign,R_TCR_sign=rtc,C_TCR_sign=ctc,resistance_ohm=rvalue,capacitance_F=cvalue,analytical_fc_Hz=expected_fc,analytical_tau_s=expected_tau,ngspice_measurements=measurements,deck_sha256=h.sha(deck),run=run))
 if not passed:break
assert all(h.sha(Path(p))==v for p,v in frozen.items()),'Frozen input changed'
passed=len(results)==96 and all(r['passed']for r in results)
summary=dict(passed=passed,source_unchanged=True,manufacturing_ready=False,physical_qualified=False,scope='Source26 four actual RC input-filter sections only, ideal buffer output and infinite-impedance ADC. Numerical agreement of native SPICE response with independent first-order transfer/step equation.',input_sha256=frozen,ngspice_version=version,source_channels=channels,cases=results,required_cases=96,component_temperature_corners_C=[25,55],temperature_range_0_to_55_complete=False,capacitor_temperature_provenance='Murata current downloaded Jun19,2026 reference: page2 5% capacitance and0+/-30ppm/C from25to125C at25C reference; page3 no-bias measurement. Values below25C require TableA and complete application review, not extrapolation.',resistor_provenance='Vishay document20035 Apr14,2026 page3 F=1%,K=100ppm/K; exact Source26 CRCW060347R0FKEA',model_limitations=['No capacitor ESR/ESL/DC-bias/frequency or hysteresis/load-aging model','No amplifier source impedance, output drive, stability, slew or input/common-mode behavior','No ADC input model, acquisition kickback, reference noise, quantization or calibration','No signal/copper parasitics or full routed-board extraction','Stepped voltage scenarios exercise an ideal linear transfer, not measured voltage independence','No startup, fault, thermal, protection or complete analog-accuracy qualification'],hardware_qualified_bandwidth_Hz=None,whole_analog_chain_passed=False,physical_validation_required=True)
if passed:summary['simulated_passive_fc_range_Hz']=[min(r['ngspice_measurements']['f3_0']for r in results),max(r['ngspice_measurements']['f3_0']for r in results)]
h.write(out/'receipt.json',summary)
print(json.dumps(dict(passed=passed,cases=len(results),scope='passive_filter_only',bandwidth=summary.get('simulated_passive_fc_range_Hz'))),flush=True)
assert passed
