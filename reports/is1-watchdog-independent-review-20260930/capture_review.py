"""Read-only independent examination of final standalone watchdog files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

REPORT=Path(__file__).resolve().parent
ROOT=REPORT.parents[1]
CORE=ROOT/'hardware/is1_watchdogs'
if (REPORT/'review.json').exists():
    raise RuntimeError('Completed independent evidence capture may not be overwritten')

files=[p for p in CORE.rglob('*') if p.is_file()]
files += [ROOT/p for p in ('tools/hardware_build_is1_watchdogs.py','tools/hardware_validate_is1_watchdogs.py',
                           'tests/test_is1_watchdogs.py','tools/hardware_build_tx_schematic.py','tools/hardware_build_logic_power.py')]
files += [p for p in (ROOT/'research/is1-watchdogs').iterdir() if p.is_file()]
files += [ROOT/'research/fpga-core/trion20-ds-v6.0.pdf',ROOT/'research/fpga-core/trion20-ds-v6.0.txt']
hashes={}
for path in files:
    rel=path.relative_to(ROOT).as_posix()
    hashes[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
    target=REPORT/'source'/rel
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)

# Manual fixtures reviewed against the manufacturer's actual primary tables.
# No import of the schematic builder or its validator expectations.
functions={'TPS3851':{'1':'VDD','2':'CWD','3':'MR','4':'GND','5':'SET1','6':'WDI','7':'WDO','8':'RESET','9':'EP'},
           'LVC1G34':{'1':'NC','2':'A','3':'GND','4':'Y','5':'VCC'},
           'LVC2G17':{'1':'1A','2':'GND','3':'2A','4':'2Y','5':'VCC','6':'1Y'}}
aliases={'MR_N':'MR','WDO_N':'WDO','RESET_N':'RESET'}
tree=ET.parse(REPORT/'source/hardware/is1_watchdogs/netlist.xml')
actual={name:{p.attrib['num']:aliases.get(p.attrib['name'],p.attrib['name'])
              for lib in tree.findall('libparts/libpart') if lib.attrib['part']==name for p in lib.findall('pins/pin')}
        for name in functions}
assert actual==functions, 'Physical functions differ from manual manufacturer fixture'

conductors={}
for net in tree.findall('nets/net'):
    for pin in net.findall('node'):
        if pin.attrib['ref'].startswith('U'):
            key=(pin.attrib['ref'],pin.attrib['pin'])
            assert key not in conductors, 'Duplicate physical pin conductor'
            conductors[key]=net.attrib['name'].removeprefix('/')

for timer,buf,tag,request in (('U1','U3','M','FPGA_MOTION_REQUEST'),('U2','U4','O','FPGA_OUTPUT_REQUEST')):
    expected={'1':'IO_3V3','2':f'WD_{tag}_CWD','4':'LOGIC_GND','5':request,
              '6':f'WD_{tag}_WDI_BUF','7':f'WD_{tag}_HEALTH_RAW','8':f'WD_{tag}_HEALTH_RAW','9':'LOGIC_GND'}
    assert {p:conductors[(timer,p)] for p in expected}==expected, 'Timer physical conductors mismatch'
    assert conductors[(timer,'3')].startswith('unconnected-'), 'MR is not NC'
    expected_buf={'2':f'FPGA_PROGRESS_{tag}','3':'LOGIC_GND','4':f'WD_{tag}_WDI_BUF','5':'IO_3V3'}
    assert {p:conductors[(buf,p)] for p in expected_buf}==expected_buf, 'WDI buffer conductor mismatch'
    assert conductors[(buf,'1')].startswith('unconnected-'), 'Buffer unused physical pin is connected'
expected_health={'1':'WD_M_HEALTH_RAW','2':'LOGIC_GND','3':'WD_O_HEALTH_RAW',
                 '4':'WD_O_OK','5':'IO_3V3','6':'WD_M_OK'}
assert {p:conductors[('U5',p)] for p in expected_health}==expected_health, 'Separate health Schmitt mismatch'

model=json.loads((REPORT/'source/hardware/is1_watchdogs/design.json').read_text(encoding='utf-8'))
for flag in ('manufacturing_ready','assembly_integrated','physical_qualification','complete_permission_chain','startup_defaults_qualified'):
    assert model[flag] is False, 'Unearned scope: '+flag
erc=json.loads((REPORT/'source/hardware/is1_watchdogs/erc.json').read_text(encoding='utf-8'))
assert sum(len(s['violations']) for s in erc['sheets'])==0, 'Recorded native ERC contains violations'

# Additional read-only validation of final current sources. No build/export/output mutation.
argv=[sys.executable,str(ROOT/'tools/hardware_validate_is1_watchdogs.py'),'--check']
proc=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
(REPORT/'validator.stdout.txt').write_text(proc.stdout,encoding='utf-8')
(REPORT/'validator.stderr.txt').write_text(proc.stderr,encoding='utf-8')
assert proc.returncode==0, 'Final read-only validator failed: '+proc.stdout+proc.stderr
assert all(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h for rel,h in hashes.items()), 'Files changed during review'

screen=[]
for resistor in (100000,1800,1000):
    hi=resistor*1.01
    eq=1/(1/27000+1/hi)
    screen.append({'pull_down_nominal_ohm':resistor,'default_v_no_added_leakage':3.465*eq/27000,
                   'default_v_assumed_10ua_source_leakage':(3.465/27000+10e-6)*eq,
                   'default_v_assumed_12ua_source_leakage':(3.465/27000+12e-6)*eq,
                   'run_high_pd_current_max_a':3.465/(resistor*.99),
                   'run_high_pd_dissipation_max_w':3.465**2/(resistor*.99)})
review={'captured_utc':datetime.now(timezone.utc).isoformat(),'scope':'Independent read-only standalone watchdog pin/net/default-state review',
        'revision':model['revision'],'source_sha256':hashes,'manual_primary_physical_functions':actual,
        'manual_conductor_checks_pass':True,'native_components_including_unfitted_boundary':len(tree.findall('components/comp')),
        'native_nets_including_four_no_connect_nets':len(tree.findall('nets/net')),
        'physical_parts':sum(p['physical'] for p in model['components'].values()),
        'native_recorded_erc_version':erc['kicad_version'],'native_recorded_erc_violations':0,
        'native_recorded_erc_included_severities':erc['included_severities'],'native_recorded_erc_ignored_checks':erc['ignored_checks'],
        'read_only_validator':{'argv':argv,'cwd':str(ROOT),'exit_code':proc.returncode},
        'source_inspection':True,'native_erc_rerun_by_this_review':False,'host_tests_rerun_by_this_review':False,
        'scope_flags':{key:model[key] for key in ('manufacturing_ready','assembly_integrated','physical_qualification','complete_permission_chain','startup_defaults_qualified')},
        'strong_pd_screen':screen,
        'findings':['T20 internal configuration pull-up defeats 100k default-LOW assumption; integration/default conditioning revision required.',
                    'SET1 directly driven LOW needs LVCMOS33 and loaded low-margin check; LVTTL VOL does not meet 0.25V VIL.',
                    'Qualified CDONE/rail/latch field containment does not ensure raw SET1 remains disabled during FPGA configuration.',
                    'Timers, health wiring and copper footprint are candidates; full permission, sticky latches, partial power and physical20ms proof remain absent.']}
(REPORT/'review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manual_primary_pin_match':True,'manual_native_conductor_match':True,'read_only_validator_exit':proc.returncode,
                  'recorded_native_erc_violations':0,'physical_parts':review['physical_parts'],'reviewed_files':len(hashes)}))
