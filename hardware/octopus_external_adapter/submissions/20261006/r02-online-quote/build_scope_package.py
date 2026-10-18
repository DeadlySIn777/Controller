from pathlib import Path
import hashlib
import html
import json
import zipfile

OUT = Path(__file__).resolve().parent
NAME = 'OEA-r0.2-PRELIMINARY-QUOTE-SCOPE-NOT-FABRICATION.zip'

text = '''OEA r0.2 — Preliminary full-turnkey quotation scope
6 October 2026 | Engineering review and budget estimate only

This is a proposed revision of the OEA StepStick-to-external-driver adapter. It is not a manufacturing release. The previously submitted r0.1 files describe the old design and must not be used to manufacture or price the revised design as though it were unchanged.

REQUESTED DELIVERY
Please provide a preliminary, itemized estimate for five fully assembled adapters and five matching finished cable harnesses (four axes plus one spare). Quantity and 500 mm harness length are quotation assumptions pending final confirmation. Include PCB fabrication, all component procurement, SMT and through-hole assembly, connector and switch fitting, harness manufacture, inspection, agreed testing, depaneling and protective packaging. No customer soldering, crimping or splicing.

REVISED ELECTRICAL SCOPE
• Accept separately qualified 3.3 V or 5 V STEP, DIR and ENABLE controller signals.
• Provide a two-pole screw terminal labelled EXT+ / GND for a regulated external or separate PSU, with proposed nominal inputs of 5 V, 12 V or 24 V. These are control-supply voltages, not motor-power ratings.
• Fit a non-shorting 5V / EXT selector for driver COM+ only. Change the switch only with power off. It must not switch ground or remove logic power.
• Keep the local logic powered independently from the external terminal in either switch position, using the proposed wide-input 3.3 V regulator.
• In 5V mode, the onboard buck derives the driver's nominal 5 V control supply from 12 V or 24 V terminal input.
• In EXT mode, COM+ follows the protected terminal supply, allowing an external regulated 5 V or an appropriately configured 12 V/24 V driver supply.
• Replace the old 5 V output devices with buffered open-drain/sinking outputs suitable for the reviewed 24 V control-input application. Final voltage, current, switching-rate and thermal ratings remain to be established.
• Protect against terminal reverse polarity and reviewed supply transients. Block reverse current into the buck's 5 V selector leg and coordinate COM+ discharge, startup and host-off behavior.
• Controller and adapter share ground. Do not connect external power to host VIO. The socket motor-voltage contact and plated hole remain omitted. This design is not galvanically isolated.

SUPPLY / SELECTOR MATRIX
Terminal input       Selector   Driver COM+                         Restriction
Regulated 5 V        EXT        External 5 V, less protection loss  Do not use 5V buck mode with a 5 V input.
12 V or 24 V         5V         Regulated nominal 5 V               Exact driver must support its 5 V input setting.
Regulated 24 V       EXT        External 24 V, less protection loss Exact driver must support its 24 V input setting.
12 V                EXT        External 12 V, less protection loss Only where the exact driver manual permits it, with required settings/resistors.

CONNECTORS AND FINISHED HARNESS
Retain the keyed four-position PCB output and matching female cable housing: COM+, PUL−, DIR−, ENA−. Supply the complete proposed 500 mm harness with a factory-made positive fanout to PUL+, DIR+ and ENA+, giving six individually labelled driver-end connections. The prior JST XH concept is a starting point; final connector, wire, ferrule/terminal and stripping dimensions require the revised BOM and exact driver terminal specification. Fit all underside host pins at the factory. Final pin geometry and clearance to adjacent driver sockets require mechanical review.

COMPATIBILITY LIMIT
Target only separately qualified common-positive (common-anode) STEP/DIR/ENABLE driver-input profiles. Do not claim all BTT/SKR boards or all external drivers. Boards with soldered motor drivers may have no suitable plug-in socket. No differential-only, analog, fieldbus, motor-power or safety/STO function is included. Exact host revisions, input current, enable polarity/startup and loaded timing must be verified.

MECHANICAL / FABRICATION BASIS
The old r0.1 board was 15.24 × 20.32 mm. That is a historical starting envelope, not the final r0.2 size. The terminal, switch, protection and power conversion may require a different outline or height. A two-layer, 1.6 mm FR-4, 1 oz PCB with green mask, white legend and ENIG is a preliminary costing basis only; revised layout and DFM will determine the final specification.

CURRENT FILE STATUS
No revised native schematic, routed PCB, exact BOM, placement/CPL, Gerbers or drill files are included or represented as complete in this package. Existing r0.1 ERC/DRC evidence does not validate r0.2. Do not procure components or start fabrication from this scope document. Please identify the information you need for a firm manufacturing quotation after revised design release.

PLEASE RETURN
1. Itemized preliminary costs for PCB, setup/stencil, components, assembly, harnesses, test fixture/testing, packaging and shipping, with currency and lead time.
2. DFM/assembly advice for the terminal, non-shorting selector, underside headers and finished harness, including any minimum panel quantity.
3. An explicit list of estimate assumptions, exclusions, substitutions and files required for the final quote.
4. Confirmation that this is r0.2 preliminary scope and is separate from the old r0.1 manufacturing inputs.

No purchase or production authorization is provided by this document.
'''

requirements = {
    'project': 'OEA', 'revision': 'r0.2', 'date': '2026-10-06',
    'status': 'preliminary_scope_only', 'manufacturing_ready': False,
    'production_authorized': False, 'quote_channel': 'PCBWay website account; no email',
    'quote_assumptions': {'assembled_boards': 5, 'finished_harnesses': 5, 'harness_length_mm': 500},
    'turnkey': ['PCB fabrication', 'component procurement', 'SMT assembly', 'through-hole assembly', 'fitted underside host pins', 'fitted terminal and selector', 'fully finished harness with positive fanout and labelled driver ends', 'inspection', 'agreed testing', 'depaneling', 'protective packaging'],
    'host_inputs_nominal_V': [3.3, 5],
    'external_terminal': {'poles': 2, 'labels': ['EXT+', 'GND'], 'nominal_V': [5, 12, 24]},
    'selector': {'positions': ['5V', 'EXT'], 'type': 'non-shorting', 'changes': 'driver COM+ only', 'power_off_operation': True},
    'matrix': [
        {'input_V': 5, 'position': 'EXT', 'COM': 'protected external 5 V; 5V buck mode not supported'},
        {'input_V': [12, 24], 'position': '5V', 'COM': 'regulated nominal 5 V'},
        {'input_V': 24, 'position': 'EXT', 'COM': 'protected external 24 V; exact driver must support 24 V setting'},
        {'input_V': 12, 'position': 'EXT', 'COM': 'protected external 12 V; only with exact driver approval and required settings/resistors'}
    ],
    'logic_supply': 'independent wide-input 3.3 V regulator from external terminal; powered in either selector position',
    'outputs': 'buffered sinking outputs for separately reviewed 24 V control-input operation; final ratings pending',
    'grounds': 'shared controller/adapter ground, not galvanically isolated',
    'host_VIO_power_backfeed': 'prohibited',
    'socket_VM_contact_and_hole': 'omitted',
    'protection_requirements': ['reverse polarity', 'reviewed supply transients', 'reverse current into buck selector leg', 'coordinated COM discharge', 'startup and host-off behavior'],
    'output_pins': {'1': 'COM+', '2': 'PUL-', '3': 'DIR-', '4': 'ENA-'},
    'harness_driver_ends': ['PUL+', 'PUL-', 'DIR+', 'DIR-', 'ENA+', 'ENA-'],
    'compatible_profiles': 'separately qualified common-positive STEP/DIR/ENABLE only',
    'universal_compatibility_claim': False,
    'historical_r01_outline_mm': [15.24, 20.32], 'r02_final_outline_mm': None,
    'preliminary_fabrication_basis': {'layers': 2, 'thickness_mm': 1.6, 'material': 'FR-4', 'copper_oz': 1, 'mask': 'green', 'legend': 'white', 'finish': 'ENIG'},
    'included_native_CAD_BOM_CPL_Gerbers_drills': False,
    'r01_must_not_be_used_as_r02': True,
    'release_dependencies': ['native schematic', 'exact components and footprints', 'mechanical fit', 'routing and native ERC/DRC', 'source/net/assembly parity', 'power and transient review', 'host-off/reset tests', 'driver-specific current/timing/enable tests', 'PCBWay DFM', 'complete quote', 'first-article verification'],
}

(OUT / 'QUOTE_SCOPE.txt').write_text(text, encoding='utf-8')
page = '<!doctype html><html lang="en"><meta charset="utf-8"><title>OEA r0.2 preliminary quotation scope</title><style>body{font:16px/1.5 system-ui,sans-serif;max-width:980px;margin:40px auto;padding:0 24px;color:#202b38}pre{font:inherit;white-space:pre-wrap}h1{font-size:26px}.status{background:#fff3cd;padding:16px;border-left:5px solid #b87800}</style><h1>OEA r0.2 · Preliminary quotation scope</h1><p class="status">Engineering review and budget estimate only. Revised manufacturing files are not included. No fabrication authorization.</p><pre>' + html.escape(text) + '</pre></html>'
(OUT / 'QUOTE_SCOPE.html').write_text(page, encoding='utf-8')
(OUT / 'requirements.json').write_text(json.dumps(requirements, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
files = ['QUOTE_SCOPE.txt', 'QUOTE_SCOPE.html', 'requirements.json']
manifest = {'project': 'OEA r0.2', 'status': 'preliminary_scope_only', 'files': {name: {'bytes': (OUT/name).stat().st_size, 'sha256': hashlib.sha256((OUT/name).read_bytes()).hexdigest()} for name in files}}
(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
with zipfile.ZipFile(OUT/NAME, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in files + ['manifest.json']:
        archive.write(OUT/name, arcname=name)
with zipfile.ZipFile(OUT/NAME) as archive:
    assert archive.testzip() is None
    assert set(archive.namelist()) == set(files + ['manifest.json'])
    for name in files:
        assert hashlib.sha256(archive.read(name)).hexdigest() == manifest['files'][name]['sha256']
receipt = {'status': 'prepared_locally_not_submitted', 'archive': NAME, 'bytes': (OUT/NAME).stat().st_size, 'sha256': hashlib.sha256((OUT/NAME).read_bytes()).hexdigest(), 'entries': files + ['manifest.json'], 'manufacturing_ready': False, 'production_authorized': False}
(OUT/'package-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, indent=2))
