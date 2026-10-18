"""Bounded exact-MPN source-backed cost arithmetic; never a quotation or order."""
from __future__ import annotations
import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BUILD_QUANTITIES = (1, 10, 100)

def money(value: Decimal) -> str:
    return str(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    src = ROOT / 'hardware/motion_card/bom.csv'
    snapshot = HERE / 'MC_BOM_INPUT.csv'
    snapshot.write_bytes(src.read_bytes())
    sources_path = HERE / 'MC_BOM_PRICE_SOURCES.json'
    source = json.loads(sources_path.read_text(encoding='utf-8'))
    offers = {p['mpn']: p for p in source['offers']}
    groups = defaultdict(list)
    with snapshot.open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['Scope'] == 'physical_component_candidate':
                groups[r['MPN']].append(r)
    assert sum(map(len, groups.values())) == 327
    assert len(groups) == 52
    assert len(groups['GRM188R72A104KA35D']) == 41
    assert 'GRM188R71E104KA01D' not in groups
    lines = []
    summaries = []
    for build in BUILD_QUANTITIES:
        cash = Decimal(0)
        consumption = Decimal(0)
        matched = Decimal(0)
        priced_count = unknown_count = moq_count = priced_pieces = 0
        excess_value = Decimal(0)
        for mpn, components in sorted(groups.items()):
            required = len(components) * build
            offer = offers.get(mpn)
            line = dict(mpn=mpn, build_boards=build, per_board_quantity=len(components),
                        required_pieces=required, references=[r['Reference'] for r in components],
                        buy_pieces=None, excess_pieces=None, selected_tier_minimum=None,
                        unit_usd=None, consumed_inventory_value_usd=None,
                        published_purchase_cash_usd=None, quantity_matched_purchase_cash_usd=None,
                        source_url=None, observed_date='2026-09-30', status='unpriced',
                        note=source['unknown_notes'].get(mpn,
                            'No exact primary published USD offer found. No substitute price or inferred volume discount.'))
            if offer:
                minimum, multiple = offer['minimum'], offer['multiple']
                buy = max(minimum, ((required + multiple - 1) // multiple) * multiple)
                tier = max((t for t in offer['price_breaks'] if t['minimum'] <= buy),
                           key=lambda t: t['minimum'])
                unit = Decimal(tier['unit_usd'])
                spent, consumed = buy * unit, required * unit
                excess = buy - required
                line.update(buy_pieces=buy, excess_pieces=excess,
                            selected_tier_minimum=tier['minimum'], unit_usd=str(unit),
                            consumed_inventory_value_usd=str(consumed),
                            published_purchase_cash_usd=str(spent),
                            quantity_matched_purchase_cash_usd=str(spent) if excess == 0 else None,
                            source_url=offer['source_url'], supplier=offer['supplier'],
                            packaging=offer['packaging'], minimum=minimum, multiple=multiple,
                            status='priced_request_quantity' if excess == 0 else 'priced_moq_excess_required',
                            observed_stock_pieces=offer.get('observed_stock_pieces'),
                            note=offer['availability_note'])
                cash += spent
                consumption += consumed
                excess_value += excess * unit
                priced_count += 1
                priced_pieces += required
                if excess:
                    moq_count += 1
                else:
                    matched += spent
            else:
                unknown_count += 1
            lines.append(line)
        assert consumption + excess_value == cash
        summaries.append(dict(build_boards=build, physical_component_pieces=327 * build,
                              exact_unique_mpns=52, publicly_priced_mpn_count=priced_count,
                              unpriced_mpn_count=unknown_count, quantity_matching_mpn_count=priced_count-moq_count,
                              moq_excess_mpn_count=moq_count, publicly_priced_component_pieces=priced_pieces,
                              unpriced_component_pieces=327 * build-priced_pieces,
                              known_quantity_matching_subtotal_usd=money(matched),
                              known_quantity_matching_per_board_usd=money(matched/build),
                              known_consumed_inventory_value_subtotal_usd=money(consumption),
                              known_consumed_inventory_value_per_board_usd=money(consumption/build),
                              known_published_purchase_cash_subtotal_usd=money(cash),
                              known_published_purchase_cash_per_board_usd=money(cash/build),
                              known_excess_inventory_value_usd=money(excess_value),
                              complete_mc_manufactured_total_usd=None,
                              complete_controller_total_usd=None))
    result = dict(schema_version=1, date='2026-09-30', currency='USD',
                  scope='Parent integrated MC r0.3 candidate, 327 physical components,52 exact MPNs; architecture clarification pending. Component sourcing only.',
                  current_bom_path='hardware/motion_card/bom.csv', input_bom_snapshot='MC_BOM_INPUT.csv',
                  input_bom_sha256=sha(snapshot), price_source_path=sources_path.name,
                  price_source_sha256=sha(sources_path), component_substitution_record='hardware/motion_card/component-substitutions.json',
                  historical_r02_bom_sha256='8be0b0d37c4a19c70b75c903b32520b24e81189b22e36e162c265d276f053f86',
                  tier_semantics='Aggregate exact MPN across all references before scaling board build. Select highest published minimum that covers required pieces, after explicit MOQ/multiple rounding. No interpolated or inferred discount. No cheaper full-reel tier used for cut tape. Published final cut-tape tier is retained unchanged beyond its minimum; no additional discount is inferred. No Digi-Reel selected.',
                  summary_semantics=dict(
                      known_quantity_matching_subtotal='Priced lines purchasable in the required piece count; excludes unpriced lines and the3 full-lot lines.',
                      known_consumed_inventory_value_subtotal='Value of fitted parts at the selected published purchase tier. Includes allocation of full-lot unit cost but is NOT the money required to purchase a small batch.',
                      known_published_purchase_cash_subtotal='Cost of all priced purchase quantities including MOQ excess. Still incomplete because10 exact MPNs and manufacture extras are unpriced. Availability and tariffs unqualified.'),
                  summaries=summaries, lines=lines, offers=source['offers'],
                  excluded_reference_offers=source['excluded_reference_offers'],
                  separately_costed_off_board_items=[
                      dict(item='Linux compute module / off-the-shelf board', fitted_to_this_mc=False,selected_mpn=None,quantity=None,cost_usd=None),
                      dict(item='ESP32 service/recovery module', fitted_to_this_mc=False,selected_mpn=None,quantity=None,cost_usd=None),
                      dict(item='Optional AI compute module', fitted_to_this_mc=False,selected_mpn=None,quantity=None,cost_usd=None),
                      dict(item='Display/touch/cables/power/mounting by qualified screen tier', fitted_to_this_mc=False,selected_mpn=None,quantity=None,cost_usd=None)],
                  manufacturing_extras_unknown=[dict(item=x,cost_usd=None) for x in [
                      'PCBWay turnkey component procurement quote / accepted exact parts and quantities',
                      'Bare PCB stackup, fabrication, controlled impedance and yield',
                      'PCBWay SMT/BGA assembly, stencil, setup, feeder minimums, attrition and excess parts',
                      'Machine-ready tape/reeling and mixed-packaging handling',
                      'Programming, functional test, fixtures, calibration and production traceability',
                      'Connectors and other omitted physical/interface components required by final architecture',
                      'Cooling, power input protection, PSU, cables, enclosure and mounting',
                      'Shipping, tariffs, tax, PCBWay sourcing charges, packaging and warranty allowance']],
                  conditional_known_packaging_charge=dict(item='Coilcraft below-reel leader/trailer option',
                      supplier_charge_usd_per_mpn='25.00',two_mpn_charge_usd='50.00',included=False,
                      note='Manufacturer says below-reel ordinary tape is not machine-ready. PCBWay must specify accepted format; this option is not assumed required.'),
                  engineering_limits=['Source inspection and decimal arithmetic only; no procurement availability guarantee.',
                      'No upload, supplier contact, order, manufacture release or source circuit modification.',
                      'No complete controller or complete MC fabrication/assembly cost established.',
                      'Unpriced values remain null and must not be interpreted as zero.'])
    (HERE / 'MC_BOM_COST.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    fields=['mpn','build_boards','per_board_quantity','required_pieces','buy_pieces','excess_pieces',
            'selected_tier_minimum','unit_usd','consumed_inventory_value_usd','published_purchase_cash_usd',
            'quantity_matched_purchase_cash_usd','status','supplier','packaging','minimum','multiple',
            'observed_date','source_url','note']
    with (HERE / 'MC_BOM_COST.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); writer.writeheader(); writer.writerows(lines)
    out=['# Current MC exact-MPN sourcing cost','',
         '30 September2026; USD. The parent MC r0.3 candidate contains **327 physical components /52 exact MPNs**. This is a bounded source-backed component cost sheet, with all52 lines included at1,10 and100 board builds. It is not a PCBWay quotation, complete controller cost or manufacture approval. The architecture clarification remains pending.','',
         'The active100nF Murata replacement now used41 times is included. The obsolete25V part remains historical evidence only. [Source ledger](MC_BOM_PRICE_SOURCES.json), [exact current BOM snapshot](MC_BOM_INPUT.csv), [complete data](MC_BOM_COST.json), and [CSV](MC_BOM_COST.csv) preserve the source links, piece-level tiers, actual purchase quantities and null unknowns.','',
         '| Board build quantity | Qty-matching known subtotal | Fitted inventory value of all priced parts | Actual known purchase cash, including excess | Unpriced exact MPNs |',
         '|---:|---:|---:|---:|---:|']
    for s in summaries:
        out.append(f"| {s['build_boards']} | ${s['known_quantity_matching_subtotal_usd']} | ${s['known_consumed_inventory_value_subtotal_usd']} | ${s['known_published_purchase_cash_subtotal_usd']} | {s['unpriced_mpn_count']} |")
    out += ['', '**42 of52 exact MPNs have a published price**;39 can be costed at the requested piece count and3 require excess purchases. Stock or delivery availability remains unqualified even for priced lines. Fitted inventory value is an accounting allocation; use the purchase-cash column when assessing prototype cash needs. None of these partial subtotals includes the10 unpriced lines or manufacture extras.','',
            '| MOQ-constrained exact part | Used per board | Minimum purchase | Published USD/unit at MOQ | Minimum cash | Excess at1 /10 /100 boards |',
            '|---|---:|---:|---:|---:|---:|']
    for mpn in ['LTC2962HUD#TRPBF','PLT0603Z1001LST1','PLT0603Z1002LST1']:
        o=offers[mpn]; tier=o['price_breaks'][0]
        excess=' / '.join(str(next(x for x in lines if x['mpn']==mpn and x['build_boards']==b)['excess_pieces']) for b in BUILD_QUANTITIES)
        out.append(f"| [{mpn}]({o['source_url']}) | {len(groups[mpn])} | {o['minimum']} | ${tier['unit_usd']} | ${money(Decimal(tier['unit_usd'])*o['minimum'])} | {excess} |")
    out += ['', 'LCSC lists exact LTC2962 cut quantities but stock is zero and prices are explicitly reference-only; they are retained as excluded research, not usable procurement cost. Mouser generic cut-tape controls do not override the precision-resistor minimum1000/multiple1000. Eight other PLT values have no exact primary public offer found. A different resistor tolerance or temperature coefficient requires engineering reanalysis before substitution.','',
            'All quantity tiers mean **component pieces**. For example4 TI244A devices per MC means4,40 and400 pieces: published CT tiers1,25 and250 apply, yielding$2.08,$12.96 and$104.592 respectively. The exact FPGA is **T20F256I4**; the cheaper C4 price is excluded. Cut-tape prices are used even when a cheaper reel price exists; no reel discount is applied to a small cut-tape order. No discount is inferred at an unpublished board-build quantity.','',
            '## Remaining unpriced lines','']
    for mpn in sorted(groups):
        if mpn not in offers:
            out.append(f"- {mpn}: {len(groups[mpn])}/board. {source['unknown_notes'].get(mpn,'No exact primary USD purchase offer found. Supplier quote needed.')}")
    out += ['', '## Active bypass-capacitor sourcing closure','',
            'The parent recorded [MC-CAP-001](../../hardware/motion_card/component-substitutions.json): Murata **GRM188R72A104KA35D**,100nF±10%,X7R,100V,0603,1.6±0.1×0.8±0.1×0.8±0.1mm. Murata lists the nominal package, temperature range−55…125°C and terminal dimensions; DigiKey identifies it as active and offers CT. This preserves the selected nominal capacitance, dielectric, tolerance and0603 geometry while increasing the voltage rating from25V to100V. It does not establish biased capacitance, impedance, mounting/process or physical performance equivalence. [Manufacturer](https://www.murata.com/products/productdetail?partno=GRM188R72A104KA35%23), [exact active distributor offer](https://www.digikey.com/en/products/detail/murata-electronics/GRM188R72A104KA35D/702549).','',
            'The published CT tiers are1:$0.16,10:$0.087,50:$0.06120,100:$0.05320,500:$0.03980. The41/410/4100 required pieces therefore cost$3.567/$21.812/$163.18 using CT tiers10/100/500. The cheaper4000-reel price$0.02739 is not assigned to4100CT pieces; a separately quoted4000reel+100CT order could differ.','',
            '## Off-board items and manufacture extras','',
            'Linux compute, ESP32 service/recovery and optional AI modules are absent from this MC. No exact off-the-shelf module is fixed in this sourcing sheet; their separately costed lines remain null. Displays and complete screen packages across7/10/12/14/18/21-inch classes remain separate. The final board architecture, I/O/interface parts and connectors must be reconciled before this becomes a controller BOM.','',
            'PCBWay procurement, PCB fabrication, SMT/BGA assembly, stencil/setup, attrition, programming/test fixtures, cooling, input protection/PSU, enclosure, cables, shipping/tariffs/tax and warranty costs remain unknown. Coilcraft publishes$25 per MPN for leader/trailer on below-reel tape ($50 for the two inductors if selected); ordinary tape is not machine-ready, so PCBWay must specify its accepted format. No reeling or optional packaging fee is silently treated as zero.','',
            f"Frozen input BOM SHA256: `{sha(snapshot)}`. Decimal arithmetic verified that purchased cash equals fitted inventory value plus excess inventory value before display rounding at all three quantities."]
    (HERE / 'MC_BOM_COST.md').write_text('\n'.join(out)+'\n',encoding='utf-8')
    print(json.dumps({'bom_sha256':sha(snapshot),'summaries':summaries},indent=2))

if __name__ == '__main__':
    main()
