"""Normalize public price research without manufacturing quotes or zero-filled gaps.

Run without arguments to regenerate research/hardware-cost-model.json and
research/manufacturing-cost-sources.json from the dated observations below.
--check regenerates in memory and fails if either file differs (read-only).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'research'
quantities = [1, 10, 100, 1000]
core = json.loads((R / 'motion-io-cost-sources.json').read_text(encoding='utf-8-sig'))
compute = json.loads((R / 'compute-cost-sources.json').read_text(encoding='utf-8-sig'))
display = json.loads((R / 'display-cost-sources.json').read_text(encoding='utf-8-sig'))
lines = []

def add(scope, key, label, mpn, qty, prices, notes, url=''):
    assert len(prices) == 4
    assert all(p is None or (isinstance(p, (int, float)) and p >= 0) for p in prices)
    # A price without a recorded source URL is flagged, never silently given another
    # line's link (the mains-cord price once reused the PSU listing).
    if url:
        price_source = 'url_recorded'
    elif any(p is not None for p in prices):
        price_source = 'unrecorded'
    else:
        price_source = 'not_priced'
    lines.append(dict(id=key, scope=scope, label=label, mpn=mpn, qty=qty,
                      prices=prices, notes=notes, url=url, price_source=price_source))

def unknown(scope, key, label, notes):
    add(scope, key, label, 'Quote / design required', 1, [None]*4, notes)

totals_by_mpn = {}
for line in core['component_lines']:
    mpn = line['manufacturer_part_number']
    totals_by_mpn[mpn] = totals_by_mpn.get(mpn, 0) + line['quantity_per_controller']

for line in core['component_lines']:
    offer = line['offers'][0]
    mpn = line['manufacturer_part_number']
    breaks = {int(k): v for k, v in offer['published_unit_price_breaks_usd'].items()}
    prices = []
    for q in quantities:
        demand = q * totals_by_mpn[mpn]
        # One price is not evidence of a volume ladder.
        if len(breaks) == 1 and demand > 1:
            prices.append(None)
        else:
            threshold = max(k for k in breaks if k <= demand)
            prices.append(breaks[threshold])
    note = 'Public piece-price ladder; last tier held without extra discount. Stock and bulk supply unquoted.'
    if mpn == 'ISO7740FDBQR':
        note = 'Tier uses 6 ICs per controller across both roles. Field power must preserve isolation.'
    if line['id'] == 'fpga':
        note = 'Only quantity-one price evidenced. T20 gateware/package unqualified; volume prices blank.'
    if line['id'] == 'field_inputs':
        note = '11 dual isolated inputs cover all 22 channels. External resistors/filtering remain unpriced.'
    if line['id'] == 'field_outputs':
        note = '4 quad protected sourcing drivers, 14 used. Current ratings and support parts unresolved.'
    if line['id'] == 'input_tvs_provision':
        note = 'One TVS per input is a costing provision, not a qualified clamp network.'
    if line['id'] in ['field_headers', 'field_mating_plugs']:
        note = '12 eight-way pieces; pair with the separate mating half. 96 positions are provisional.'
    add('Common',line['id'],line['block'],mpn,line['quantity_per_controller'],prices,note,offer['source_url'])

# Same electronics/power basis in every procurement approach.
add('Common','main_psu','Control/display mains adapter','MEAN WELL GST90A24-P1M',1,
    [30.80,28.00,27.20,27.20],
    '24 V / 90 W reference; 25+ public tier held. Power sizing and DC conversion unqualified.',
    'https://www.digikey.com/en/products/detail/mean-well-usa-inc/GST90A24-P1M/7703720')
add('Common','mains_cord','Regional mains cord reference','Phihong AC30UNA-R',1,[5.89,None,None,None],
    'North American C13 cord reference; $5.89 unit price source not recorded, re-verify before quoting. Regional approvals/length to confirm.',
    '')
add('Common','hdmi_cable','HDMI video cable reference','Adafruit 608, 1 metre',1,[4.95,4.46,3.96,3.96],
    'Full-size HDMI on both ends assumed; remove only after package inclusion is confirmed.',
    'https://www.adafruit.com/product/608')

a, b = compute['candidates']
add('AC','module','Linux module incl. RAM / eMMC',a['sku'],1,[55,None,None,None],
    '2 GB / 16 GB / no Wi-Fi. Bulk quotes absent. Two carrier connectors and Ethernet PHY extra.',a['urls'][0])
add('AC','module_sink','Module heatsink reference','HS-RDX-CM3',1,[0.99,None,None,None],
    'CM3 passive heatsink; CM3S clearance and enclosed thermal performance unqualified.',a['costed_accessories'][0]['url'])
add('AC','module_fan','Cooling fan reference','Sunon MF40100V2-1000U-A99',1,[4.87,3.981,3.1591,2.90758],
    '5 V / 40 mm fan only. Last 400+ price held; ducting, guard and mounting remain unpriced.',
    'https://www.digikey.com/en/products/detail/sunon-fans/MF40100V2-1000U-A99/6198733')
add('B','sbc','Linux SBC incl. ports','Radxa ROCK 3C RS112-D2',1,[44.90,None,None,None],
    '2 GB board; storage/cooling below. SPI/LinuxCNC/graphics unqualified; no volume quotes.',b['urls'][0])
for accessory in b['costed_accessories']:
    add('B',accessory['sku'], 'OS storage' if accessory['role']=='local_storage' else 'SBC heatsink / fan',
        accessory['sku'],1,[accessory['prices'][0]['usd'],None,None,None],
        'Public unit price only; no volume quotes. Exact revision and system performance require testing.',accessory['url'])

sources = {s['id']:s['url'] for s in display['sources']}
monitor = display['candidates'][0]
add('AB','complete_monitor','21.5-inch complete touch monitor','OSCY OTM-2150',1,
    [monitor['advertised_unit_usd_by_order_quantity'][str(q)] for q in quantities],
    'Capacitive option/package unconfirmed. Sample at 1; no tier at 10; indexed bulk offers at 100/1000.',
    sources['oscy_listing'])
component_display = display['candidates'][3]
roles_to_use = {'bare_lcd_with_leds':'Bare 21.5-inch LCD',
                'hdmi_to_lvds_controller':'HDMI-to-LVDS controller',
                'pcap_overlay_and_usb_controller':'21.5-inch PCAP / USB controller',
                'backlight_constant_current_driver':'Backlight driver / package check',
                'lvds_backlight_usb_and_power_harnesses':'Display LVDS / touch / power harness'}
for part in component_display['parts_bundle']:
    if part['role'] not in roles_to_use:
        continue
    url = sources.get(part.get('source_ids',[''])[0],'')
    note = {
      'bare_lcd_with_leds':'Old exact-part panel; seller revision/dimensions need confirmation. Touch/backlight driver extra.',
      'hdmi_to_lvds_controller':'Seller names selected panel. Firmware, LVDS cable and backlight inclusion unconfirmed.',
      'pcap_overlay_and_usb_controller':'HX2151801 view window is plausible; exact fit and price unconfirmed. Required cost remains blank.',
      'backlight_constant_current_driver':'Required unless included in verified controller package. Never assumed free.',
      'lvds_backlight_usb_and_power_harnesses':'Panel-specific pinout/length and USB touch cable inclusion not established.'
    }[part['role']]
    add('C',part['role'],roles_to_use[part['role']],part['part'] or 'Quote / configuration required',1,
        [part['advertised_unit_usd_by_order_quantity'][str(q)] for q in quantities],note,url)

# Complete scope coverage: gaps remain explicit, never numeric zero.
for row in core['unpriced_required_support']:
    if row['id'] == 'other_connectors':
        continue # Split by procurement approach below to avoid double-counting.
    labels = {'input_passives':'Input threshold / filter passives', 'diff_front_end_support':'Differential protection / encoder supply',
              'output_support':'Output protection / current-setting parts', 'spindle_support':'Analog spindle support / inhibit',
              'regulator_support':'FPGA rails and converter support parts', 'fpga_configuration_clock_debug':'FPGA flash / clock / debug',
              'supervision_support':'Reset / inhibit / ESP service support'}
    unknown('Common',row['id'],labels[row['id']], 'Exact circuit, fitted quantities and supplier prices required.')

common_gaps = [
 ('logic_power','24 V input / 12 V and 5 V conversion','Includes protection, logic isolation as required, 5 V/3 A compute path and display supply.'),
 ('internal_link','Host SPI / ESP links and service wiring','Dedicated host SPI; bounded separate ESP link; connectors, harnesses and protection.'),
 ('expansion','Rated expansion interface','Electrical type and timing class still to be selected; reserve an actual priced circuit.'),
 ('usb_touch','USB touch cable / power connector','Package inclusion unresolved; includes mating DC connector and internal power harness.'),
 ('programming','Programming / serialization','Unit cycle time, labor, fixture and software image not established.'),
 ('test','Electrical / functional test','Probe fixture, coverage, per-unit labor and run time require a test plan.'),
 ('yield','Scrap / rework per good unit','Do not assume 100% yield; no pilot measurements or production allowance approved.'),
 ('thermal_mount','Cooling attachment / guard / thermal parts','Sink/fan reference does not include attachment, enclosure airflow or qualification.'),
 ('enclosure','Final enclosure / bezel / display mount','21.5-inch physical drawings and mounting design required before fabrication quote.'),
 ('integration','Final assembly / wiring / labels','Housing labor, cable routing, fasteners, labels and inspection not quoted.'),
 ('packaging','Product packaging','Display protection, inserts and cartons; no packaging quotation obtained.'),
 ('freight','Inbound freight / duties / brokerage','Destination and supplier shipment terms unknown; recoverable taxes excluded.'),
 ('factory_fixture','Factory fixture/tooling allocation','Separate from product development; amortization over build quantity must be defined.'),
]
for key,label,note in common_gaps:
    unknown('Common',key,label,note)
for scope, board in [('AC','module carrier / motion board'), ('B','SBC motion / I/O board')]:
    unknown(scope,'pcb_'+scope,'PCBWay PCB fabrication',f'Separate quote for {board}; dimensions, stackup, finish and panel not finalized.')
    unknown(scope,'pcba_'+scope,'PCBWay turnkey sourcing / assembly',
            'Assembly, procurement uplift, minimum packs/overbuy, inspection and applicable setup fees unquoted; public parts are references, not PCBWay-supplied prices.')
unknown('AC','module_carrier','SODIMM / J1 sockets and Ethernet PHY','CM3S GMAC is on J1: two connectors plus PHY, clock, magnetics, RJ45 and passives.')
unknown('AC','module_ports','Module HDMI / USB connectors and ESD','Provide display/touch/service ports; not included in module price.')
unknown('B','sbc_mount','SBC mounts and inter-board cable','Standalone board requires mounting and retained SPI/power connections.')
unknown('AB','monitor_integration','Monitor power / touch package check','Exact USB/cable/PSU/bracket inclusions unknown; shared PSU/converter is already budgeted.')
unknown('C','panel_stack','Panel/glass bonding / bezel integration','Bare-panel spacer/gasket or bonding, glass retention, optical inspection and breakage allowance.')

configs = [
 dict(id='A',label='Module + complete monitor',scopes=['Common','AC','AB'],
      compute='CM3 SODIMM, 2 GB RAM / 16 GB eMMC',display='OSCY 21.5-inch FHD capacitive monitor lead',
      qualification='Carrier PHY/ports extra; motion and local graphics unqualified.'),
 dict(id='B',label='SBC + complete monitor',scopes=['Common','B','AB'],
      compute='ROCK 3C, 2 GB + 64 GB microSD + AE007 cooling',display='Same OSCY 21.5-inch FHD capacitive monitor lead',
      qualification='Assembled ports simplify integration; SPI and RT stack unqualified.'),
 dict(id='C',label='Module + separate panel parts',scopes=['Common','AC','C'],
      compute='Same CM3 SODIMM configuration as A',display='M215HGE-L21 + NJY video board + HX2151801 touch candidate',
      qualification='Touch price, backlight package, fit and harnesses unresolved.'),
]
model = dict(date='2026-09-28',currency='USD',quantities=quantities,target=249,configurations=configs,lines=lines,
             conclusion=['A/B public sample baskets exceed $249 before manufacturing gaps are filled.',
                         'No volume winner is established. C has no demonstrated display-cost saving.'],
             price_policy='No invented volume discounts. Multi-break component ladders use the largest qualifying threshold, holding the final published tier as an unquoted reference. Single-price compute/FPGA/accessories are blank at unquoted volumes. Display tiers obey explicit bounds. Component purchase demand aggregates identical MPNs. Cut-tape/reference quantities omit overbuy, reel/setup fees and stock assurance.',
             scope_notes=['Same six joints, 22 inputs, 14 outputs, two encoders and 0-10 V spindle in all approaches.',
                          'Reference adds isolated output controls, 16-bit DAC and 96 terminals; these are costing choices, not user-frozen requirements.',
                          'Main 24 V / 90 W PSU reference serves control/display; external drives and field-load supplies are machine equipment outside this controller bundle.',
                          'C uses the same main PSU and unpriced converters; the display-only 12 V adapter is excluded to avoid duplicate power cost.',
                          'PCBWay turnkey is the chosen board manufacturing route. Supplier quotation must replace public component references; sourcing uplift and overbuy remain unpriced.',
                          'AI compute is an optional separately costed add-on; no AI module is included in these three base configurations.',
                          'Warranty, sales fees, outbound fulfillment and engineering are outside manufactured cost; account for them before declaring a selling price viable.'])
assert len({l['id'] for l in lines}) == len(lines), 'line ids must be unique'
line_by_id = {l['id']: l for l in lines}
assert line_by_id['main_psu']['mpn'] == 'MEAN WELL GST90A24-P1M'
# No two different parts may cite the same product listing as their price source.
_url_owner = {}
for l in lines:
    if l['url']:
        assert _url_owner.setdefault(l['url'], l['mpn']) == l['mpn'], (l['id'], l['url'])
ancillary = dict(date=model['date'],currency='USD',sources=[
 {'part':'GST90A24-P1M','url':line_by_id['main_psu']['url'],'prices':{'1':30.8,'5':29.3,'10':28,'25':27.2}},
 {'part':'MF40100V2-1000U-A99','url':'https://www.digikey.com/en/products/detail/sunon-fans/MF40100V2-1000U-A99/6198733','prices':{'1':4.87,'10':3.981,'25':3.6408,'50':3.394,'100':3.1591,'400':2.90758}},
 {'service':'PCBWay turnkey board fabrication, procurement and assembly',
  'url':'https://www.pcbway.com/quotesmt.aspx',
  'quote_status':'Not requested; design files incomplete', 'prices':{'1':None,'10':None,'100':None,'1000':None},
  'note':'Chosen vendor. JLCPCB tariffs excluded. Assembly form prices exclude fabrication and components. Stencil is included in assembly quotations; programming/test and box-build scope require explicit pricing.',
  'files':'https://www.pcbway.com/assembly-file-requirements.html',
  'stencil':'https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Should_I_submit_a_stencil_order_for_SMT_project_made_by_PCBWay_.html',
  'procurement':'https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Why_the_unit_cost_of_components_is_higher_than_suppliers_such_as_Digiky_.html',
  'testing':'https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Can_you_do_test_after_assembly__What_documents_should_I_offer_.html'}])
outputs = {R / 'hardware-cost-model.json': json.dumps(model,indent=2)+'\n',
           R / 'manufacturing-cost-sources.json': json.dumps(ancillary,indent=2)+'\n'}
if '--check' in sys.argv[1:]:
    stale = [p.relative_to(ROOT).as_posix() for p, text in outputs.items()
             if not p.is_file() or p.read_bytes() != text.encode('utf-8')]
    if stale:
        sys.exit('stale generated cost data (rerun without --check): ' + ', '.join(stale))
    print('read-only check passed: generated cost data matches this script')
else:
    for p, text in outputs.items():
        # LF on every platform: newline='' stops Windows from writing CRLF.
        with open(p, 'w', encoding='utf-8', newline='') as handle:
            handle.write(text)
for c in configs:
    chosen=[l for l in lines if l['scope'] in c['scopes']]
    print(c['id'],[(q,round(sum(l['qty']*l['prices'][i] for l in chosen if l['prices'][i] is not None),5),sum(l['prices'][i] is None for l in chosen)) for i,q in enumerate(quantities)])
