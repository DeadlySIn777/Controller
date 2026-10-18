"""Check actual native export parity and package pins; not physical evidence."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import pcbnew

ROOT = Path(__file__).resolve().parent
LIBROOT = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
data = json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))
parts = data['parts']
tree = ET.parse(ROOT/'adapter.net.xml').getroot()
issues = []

def require(test, message):
    if not test:
        issues.append(message)

components = {c.attrib['ref']: c for c in tree.findall('./components/comp')}
require(set(parts) == set(components), 'Native netlist component set mismatch')
native_nets = {}
for net in tree.findall('./nets/net'):
    # KiCad prefixes root-sheet local labels with one '/'. Keep hierarchy
    # paths distinct; this design has exactly one native root sheet.
    name = net.attrib['name']
    if name.startswith('/') and name.count('/') == 1:
        name = name[1:]
    for node in net.findall('node'):
        native_nets[(node.attrib['ref'], node.attrib['pin'])] = name

pad_total = 0
tp_flags = {}
assembly_counts = {'smt':0, 'through_hole':0, 'pcb_test_pads':0}
for ref,p in parts.items():
    comp = components.get(ref)
    if comp is None:
        continue
    require(comp.findtext('footprint') == p['footprint'], f'{ref}: footprint field differs')
    require(comp.findtext('value') == p['value'], f'{ref}: value field differs')
    require(comp.findtext('tstamps') == p['uuid'], f'{ref}: schematic UUID differs')
    props = {n.attrib['name']:n.attrib.get('value','') for n in comp.findall('property')}
    require(props.get('MPN','') == p['mpn'], f'{ref}: MPN differs')
    for num,expected in p['pins'].items():
        actual = native_nets.get((ref,num))
        if expected is None:
            require(actual is None or actual.startswith('unconnected-'), f'{ref}.{num}: NC pin connected to {actual}')
        else:
            require(actual == expected, f'{ref}.{num}: expected {expected}, actual {actual}')
    lib,name = p['footprint'].split(':')
    folder = ROOT/(lib+'.pretty') if (ROOT/(lib+'.pretty')).exists() else LIBROOT/(lib+'.pretty')
    fp = pcbnew.FootprintLoad(str(folder), name)
    require(fp is not None, f'{ref}: footprint load failed')
    if fp is None:
        continue
    pads = [pad for pad in fp.Pads() if pad.GetNumber()]
    pad_total += len(pads)
    require({pad.GetNumber() for pad in pads} == set(p['pins']), f'{ref}: package pad set differs')
    if not p['in_bom']:
        assembly_counts['pcb_test_pads'] += 1
        attrs = fp.GetAttributes()
        require(bool(attrs & pcbnew.FP_EXCLUDE_FROM_BOM), f'{ref}: pad lacks native BOM exclusion')
        require(bool(attrs & pcbnew.FP_EXCLUDE_FROM_POS_FILES), f'{ref}: pad lacks native CPL exclusion')
        require(not p['in_position_files'] and not p['mpn'] and not p['manufacturer'], f'{ref}: fake purchased-part identity')
        require(all(not pad.IsOnLayer(pcbnew.F_Paste) and not pad.IsOnLayer(pcbnew.B_Paste) for pad in pads), f'{ref}: paste on bare test contact')
        tp_flags[ref] = {'net':p['pins']['1'], 'excluded_from_bom':True, 'excluded_from_cpl':True, 'no_paste':True}
    elif fp.GetAttributes() & pcbnew.FP_SMD:
        assembly_counts['smt'] += 1
    elif fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE:
        assembly_counts['through_hole'] += 1
    else:
        require(False, f'{ref}: no SMT/THT attribute on purchased footprint')

# Independently transcribed from manufacturer pin tables, not inferred from PCB.
primary_pin_maps = {
    'U20': {'1':'BST','2':'GND','3':'FB','4':'EN','5':'IN','6':'SW'},
    'U21': {'1':'IN','2':'OUT','3':'GND'},
    'Q1': {'1':'G','2':'S','3':'D'},
    'Q2': {'1':'G','2':'S','3':'D'},
    'Q3': {'1':'G','2':'S','3':'D'},
    'Q20': {'1':'G','2':'S','3':'D'},
    'U50': {'1':'VDD','2':'PA6_LED5','3':'PA7_LED12','4':'PA1_AIN1','5':'PA2_LED24','6':'PA0_UPDI','7':'PA3_EXTCLK_NC','8':'GND'},
}
for ref,expected in primary_pin_maps.items():
    require(parts[ref]['pin_labels'] == expected, f'{ref}: independent primary pin-map mismatch')
require(parts['J2']['pins']['6'] is None, 'Host VIO must remain NC')
require(parts['U50']['pins']['6'] == 'IND_UPDI', 'UPDI physical pin6 mismatch')
require(parts['U50']['pins']['7'] is None, 'PA3 physical pin7 must be NC')
require(parts['SW1']['pins'] == {'1':'V5_SELECT','2':'COM_PLUS','3':'V_EXT_PROT'}, 'Selector contract mismatch')
require(parts['D25']['pins'] == {'1':'V5_SELECT','2':'V5_REG'}, 'Buck output reverse-block orientation mismatch')
require(parts['D26']['pins'] == {'1':'V_IND_IN','2':'IND_FEED_R'}, 'Indicator input diode orientation mismatch')
require(parts['R26']['pins'] == {'1':'COM_PLUS','2':'IND_FEED_R'}, 'Indicator inrush resistor mismatch')
require(parts['R53']['pins'] == {'1':'COM_PLUS','2':'IND_ADC'}, 'ADC top-divider mismatch')
require(parts['R54']['pins'] == {'1':'IND_ADC','2':'GND'}, 'ADC bottom-divider mismatch')
motion_nets = {'STEP','DIR','EN','STEP_GATE','DIR_GATE','EN_GATE','PUL_MINUS','DIR_MINUS','ENA_MINUS'}
require(not motion_nets.intersection(parts['U50']['pins'].values()), 'MCU connected to motion commands')

erc = json.loads((ROOT/'evidence/schematic-erc.json').read_text(encoding='utf-8-sig'))
require((ROOT/'evidence/schematic-erc.json').stat().st_mtime >= (ROOT/'adapter.kicad_sch').stat().st_mtime, 'ERC predates native schematic')
require((ROOT/'adapter.net.xml').stat().st_mtime >= (ROOT/'adapter.kicad_sch').stat().st_mtime, 'Netlist predates native schematic')
violations = [v for sheet in erc.get('sheets',[]) for v in sheet.get('violations',[])]
require(not violations, f'Actual ERC has {len(violations)} violation(s)')
require(not erc.get('violations',[]), 'ERC root violations present')
pro = json.loads((ROOT/'adapter.kicad_pro').read_text(encoding='utf-8'))
require(not pro.get('erc',{}).get('erc_exclusions',[]), 'ERC exclusions present')
for category in ['single_global_label','four_way_junction','footprint_filter']:
    require(pro.get('erc',{}).get('rule_severities',{}).get(category) == 'warning', f'{category} not explicitly enabled')

report = {
    'status':'PASS' if not issues else 'FAIL',
    'evidence_kind':'Actual KiCad netlist/ERC and native-library pin parity; independent primary pin-table review',
    'native_footprints':len(parts),
    'purchased_parts':sum(p['in_bom'] for p in parts.values()),
    'unique_purchased_mpns':len({p['mpn'] for p in parts.values() if p['in_bom']}),
    'numbered_pads_checked':pad_total,
    'actual_footprint_assembly_counts':assembly_counts,
    'test_pad_checks':tp_flags,
    'enabled_erc_violations':len(violations),
    'erc_ignored_checks_as_reported':erc.get('ignored_checks',[]),
    'erc_violation_exclusions':pro.get('erc',{}).get('erc_exclusions',[]),
    'primary_pin_maps_checked':primary_pin_maps,
    'primary_sources':{
        'MP2459':'https://www.monolithicpower.com/media/document/MP2459_r1.01.pdf',
        'AP7375-SA':'https://www.diodes.com/datasheet/download/AP7375.pdf',
        'NX6008NBK':'https://assets.nexperia.com/documents/data-sheet/NX6008NBK.pdf',
        'PMV100EPA':'https://assets.nexperia.com/documents/data-sheet/PMV100EPA.pdf',
        'ATtiny202':'https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATtiny202-204-402-404-406-DataSheet-DS40002318A.pdf',
    },
    'issues':issues,
    'sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['parts.json','adapter.kicad_sch','adapter.kicad_pro','adapter.net.xml','power_spec.json','logic_spec.json','indicator_spec.json']},
    'limits':['No PCB/DRC/fabrication release from this check.','No circuit simulation or physical measurements.','Regulator collapse/protection, loaded command timing, exact host fit, firmware and calibration remain unresolved prototype work.','SPICE model checks are ignored because no simulation models or simulation are claimed.'],
    'manufacturing_ready':False,
}
report_path = ROOT/'evidence/schematic-review.json'
if report_path.exists():
    previous = json.loads(report_path.read_text(encoding='utf-8'))
    visual = previous.get('pdf_visual_review', {})
    pdf_path = ROOT/'adapter-schematic.pdf'
    if (pdf_path.exists() and visual.get('pdf_sha256') == hashlib.sha256(pdf_path.read_bytes()).hexdigest()
            and previous.get('sha256',{}).get('adapter.kicad_sch') == report['sha256']['adapter.kicad_sch']):
        report['pdf_visual_review'] = visual
report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','native_footprints','purchased_parts','unique_purchased_mpns','numbered_pads_checked','enabled_erc_violations','issues']}))
raise SystemExit(bool(issues))
