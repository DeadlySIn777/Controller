"""Current r04 exact-MPN catalogue costing, forked from the retained r03 audit.

Report-only writes. Explicit project root avoids relocated HERE.parent assumptions.
No quote, order, availability guarantee, hardware edits or fabrication outputs.
"""
from __future__ import annotations
import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r'C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller')
BUILD_QUANTITIES = (1, 10, 100)


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    historical = json.loads((HERE/'historical-r03-hashes.json').read_text())
    assert all(sha(ROOT/p) == h for p,h in historical.items()), 'Historical r03 evidence changed'
    current = ROOT/'hardware/motion_card'
    source_paths = [current/p for p in ('bom.csv','design.json','assembly-map.json','netlist.xml',
                                      'validation.json','component-substitutions.json')]
    current_hashes = {p.relative_to(ROOT).as_posix():sha(p) for p in source_paths}
    model = json.loads((current/'design.json').read_text())
    validation = json.loads((current/'validation.json').read_text())
    assert model['revision'] == 'motion-card-r0.4-proposed-IS2'
    assert validation['pass'] and validation['evidence']['fitted_source_pins_checked'] == 1229
    assert not model['manufacturing_ready'] and not model['physical_qualification']
    snapshot = HERE/'MC_BOM_INPUT.csv'
    snapshot.write_bytes((current/'bom.csv').read_bytes())
    sources_path = HERE/'MC_BOM_PRICE_SOURCES.json'
    source = json.loads(sources_path.read_text(encoding='utf-8'))
    offers = {p['mpn']:p for p in source['offers']}
    groups = defaultdict(list)
    with snapshot.open(newline='',encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row['Scope'] == 'physical_component_candidate': groups[row['MPN']].append(row)
    assert sum(map(len,groups.values())) == 327 and len(groups) == 52
    assert len(groups['GRM188R72A104KA35D']) == 41
    assert {r['Reference'] for r in groups['LTC2962HUD#PBF']} == {'U2003','U2004','U2005'}
    assert all(r['Value']=='LTC2962HUD#TRPBF' and r['Footprint']=='CNC_MC_Power:LTC2962_UD16'
               for r in groups['LTC2962HUD#PBF'])
    assert 'GRM188R71E104KA01D' not in groups and 'LTC2962HUD#TRPBF' not in groups
    lines, summaries = [], []
    for build in BUILD_QUANTITIES:
        cash = consumption = matched = excess_value = Decimal(0)
        priced_count = unknown_count = moq_count = priced_pieces = 0
        stock_short = stock_unknown = 0
        for mpn,components in sorted(groups.items()):
            required = len(components)*build
            offer = offers.get(mpn)
            line = dict(mpn=mpn,build_boards=build,per_board_quantity=len(components),
                        required_pieces=required,references=[r['Reference'] for r in components],
                        buy_pieces=None,excess_pieces=None,selected_tier_minimum=None,unit_usd=None,
                        consumed_inventory_value_usd=None,published_purchase_cash_usd=None,
                        quantity_matched_purchase_cash_usd=None,source_url=None,
                        observed_date='2026-09-30',status='unpriced',observed_stock_pieces=None,
                        observed_stock_covers_required=None,observed_stock_covers_buy=None,
                        required_stock_shortfall_pieces=None,buy_stock_shortfall_pieces=None,
                        availability_qualified=False,
                        note=source['unknown_notes'].get(mpn,
                            'No exact primary published USD offer found; no substitute price or inferred discount.'))
            if offer:
                minimum,multiple = offer['minimum'],offer['multiple']
                buy = max(minimum,((required+multiple-1)//multiple)*multiple)
                tier = max((t for t in offer['price_breaks'] if t['minimum'] <= buy),key=lambda t:t['minimum'])
                unit = Decimal(tier['unit_usd'])
                spent,consumed,excess = buy*unit,required*unit,buy-required
                stock = offer.get('observed_stock_pieces')
                stock = int(stock) if stock is not None else None
                line.update(buy_pieces=buy,excess_pieces=excess,selected_tier_minimum=tier['minimum'],
                            unit_usd=str(unit),consumed_inventory_value_usd=str(consumed),
                            published_purchase_cash_usd=str(spent),
                            quantity_matched_purchase_cash_usd=str(spent) if excess==0 else None,
                            source_url=offer['source_url'],supplier=offer['supplier'],
                            packaging=offer['packaging'],minimum=minimum,multiple=multiple,
                            status='priced_request_quantity' if excess==0 else 'priced_moq_excess_required',
                            observed_stock_pieces=stock,
                            observed_stock_covers_required=stock>=required if stock is not None else None,
                            observed_stock_covers_buy=stock>=buy if stock is not None else None,
                            required_stock_shortfall_pieces=max(0,required-stock) if stock is not None else None,
                            buy_stock_shortfall_pieces=max(0,buy-stock) if stock is not None else None,
                            availability_status='catalogue_stock_covers_buy_unreserved' if stock is not None and stock>=buy
                                else 'catalogue_stock_insufficient' if stock is not None else 'stock_unknown',
                            note=offer['availability_note'])
                cash += spent; consumption += consumed; excess_value += excess*unit
                priced_count += 1; priced_pieces += required
                if excess: moq_count += 1
                else: matched += spent
                if stock is None: stock_unknown += 1
                elif stock < buy: stock_short += 1
            else:
                unknown_count += 1
            lines.append(line)
        assert consumption+excess_value == cash
        assert (priced_count,unknown_count,moq_count) == (42,10,2)
        summaries.append(dict(build_boards=build,physical_component_pieces=327*build,
            exact_unique_mpns=52,publicly_priced_mpn_count=priced_count,unpriced_mpn_count=unknown_count,
            quantity_matching_mpn_count=priced_count-moq_count,moq_excess_mpn_count=moq_count,
            publicly_priced_component_pieces=priced_pieces,unpriced_component_pieces=327*build-priced_pieces,
            known_quantity_matching_subtotal_usd=money(matched),
            known_quantity_matching_per_board_usd=money(matched/build),
            known_consumed_inventory_value_subtotal_usd=money(consumption),
            known_consumed_inventory_value_per_board_usd=money(consumption/build),
            known_published_purchase_cash_subtotal_usd=money(cash),
            known_published_purchase_cash_per_board_usd=money(cash/build),
            known_excess_inventory_value_usd=money(excess_value),
            priced_mpn_observed_stock_shortfall_count=stock_short,
            priced_mpn_stock_unknown_count=stock_unknown,
            procurement_availability_qualified=False,stock_qualified_purchase_total_usd=None,
            complete_mc_manufactured_total_usd=None,complete_controller_total_usd=None))
    result = dict(schema_version=2,date='2026-09-30',currency='USD',
        scope='Parent integrated MC r0.4 candidate; 327 physical components, 52 exact MPNs. Component catalogue pricing only; final architecture unresolved.',
        current_bom_path='hardware/motion_card/bom.csv',input_bom_snapshot=snapshot.name,
        input_bom_sha256=sha(snapshot),current_source_sha256=current_hashes,
        price_source_path=sources_path.name,price_source_sha256=sha(sources_path),
        component_substitution_record='hardware/motion_card/component-substitutions.json',
        historical_r03_artifacts_preserved_sha256=historical,
        tier_semantics='Aggregate exact MPN across references before scaling builds. Apply MOQ/multiple rounding, then the highest published component-piece tier covering the purchase quantity. No interpolated or inferred discounts, reel-price credit for cut tape, or Digi-Reel selection.',
        summary_semantics=dict(
            known_quantity_matching_subtotal='Catalogue-priced lines whose order quantity equals fitted demand; excludes the two MOQ-excess lines and ten unpriced lines. It does not establish stock availability.',
            known_consumed_inventory_value_subtotal='Fitted part value allocated at the selected purchase tier; not the purchasing cash for a small batch.',
            known_published_purchase_cash_subtotal='Sum of published catalogue prices including MOQ excess, regardless of stock. Ten exact MPNs and manufacture extras are omitted as null. This is not a stock-covered basket or supplier quotation.',
            stock_qualified_purchase_total='Null at every build because parts are unpriced, stock is insufficient or unknown and no inventory is reserved.'),
        summaries=summaries,lines=lines,offers=source['offers'],
        excluded_reference_offers=source['excluded_reference_offers'],
        separately_costed_off_board_items=[dict(item=x,fitted_to_this_mc=False,selected_mpn=None,quantity=None,cost_usd=None) for x in [
            'Linux compute module / off-the-shelf board','ESP32 service/recovery module','Optional AI compute module',
            'Complete display/touch/cables/power/mounting packages for 7/10/12/14/18/21-inch classes and further qualified sizes']],
        manufacturing_extras_unknown=[dict(item=x,cost_usd=None) for x in [
            'PCBWay turnkey procurement, accepted exact parts/quantities and delivery',
            'PCB stackup, fabrication, impedance, yield and SMT/BGA assembly',
            'Stencil, setup, feeders, attrition, reeling and tube/tray handling',
            'Programming, functional test, fixtures, calibration and traceability',
            'Omitted connectors and interfaces required by the reconciled architecture',
            'Cooling, input protection, PSU, enclosure, wiring and mounting',
            'Shipping, tariffs, taxes, sourcing fees, packaging and warranty allowance']],
        conditional_known_packaging_charge=dict(item='Coilcraft below-reel leader/trailer option',
            supplier_charge_usd_per_mpn='25.00',two_mpn_charge_usd='50.00',included=False,
            note='Ordinary below-reel tape is not machine-ready; PCBWay accepted format is unknown.'),
        resistor_substitutions_applied=False,manufacturing_ready=False,physical_qualification=False,
        engineering_limits=['Report-only source inspection and Decimal arithmetic.',
            'No supplier contact, upload, order, hardware edit or fabrication outputs.',
            'Null amounts are unknown, not zero. Public prices are not delivery commitments.'])
    (HERE/'MC_BOM_COST.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    fields=['mpn','build_boards','per_board_quantity','required_pieces','buy_pieces','excess_pieces',
        'selected_tier_minimum','unit_usd','consumed_inventory_value_usd','published_purchase_cash_usd',
        'quantity_matched_purchase_cash_usd','status','supplier','packaging','minimum','multiple',
        'observed_stock_pieces','observed_stock_covers_required','observed_stock_covers_buy',
        'required_stock_shortfall_pieces','buy_stock_shortfall_pieces','availability_status',
        'availability_qualified','observed_date','source_url','note']
    with (HERE/'MC_BOM_COST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(lines)
    render_markdown(result,groups,offers,source)
    assert all(sha(ROOT/p)==h for p,h in current_hashes.items()), 'Current source changed during costing'
    assert all(sha(ROOT/p)==h for p,h in historical.items()), 'Historical r03 evidence changed'
    print(json.dumps({'bom_sha256':sha(snapshot),'summaries':summaries},indent=2))


def render_markdown(result,groups,offers,source):
    out=['# MC r0.4 exact-MPN component pricing','',
        '30 September 2026; USD. Current MC: **327 physical components / 52 exact MPNs**. All 52 lines are included at 1, 10 and 100 board builds. These partial catalogue totals exclude ten unpriced MPNs and all manufacture extras; no complete controller, stock-covered purchase basket, PCBWay quotation or manufacture approval exists.','',
        '| Boards | Qty-matching catalogue subtotal | Fitted inventory value, priced parts | Catalogue purchase cash, including excess | Unpriced MPNs |',
        '|---:|---:|---:|---:|---:|']
    for s in result['summaries']:
        out.append(f"| {s['build_boards']} | ${s['known_quantity_matching_subtotal_usd']} | ${s['known_consumed_inventory_value_subtotal_usd']} | ${s['known_published_purchase_cash_subtotal_usd']} | {s['unpriced_mpn_count']} |")
    out += ['', '**42 MPNs are priced: 40 match fitted demand and two require MOQ excess.** Quantity matching describes the purchase arithmetic, not availability. Some priced catalogue parts show zero stock and others have unknown stock. Stock-qualified purchase totals remain null at every quantity.','',
        '[Exact BOM snapshot](MC_BOM_INPUT.csv), [source catalogue](MC_BOM_PRICE_SOURCES.json), [complete JSON](MC_BOM_COST.json), and [all 156 quantity lines in CSV](MC_BOM_COST.csv) retain piece-tier and null data. Historical r03 artifacts were preserved unchanged; only the parent packaging substitution changes this current costing.','',
        '## Current supervisor packaging and stock','',
        'Parent MC-PACK-001 changes **U2003/U2004/U2005** to **LTC2962HUD#PBF**, H-grade UD 3 × 3 mm QFN-16 plus exposed ground pad 17, in tube packaging. The inherited schematic Value stays LTC2962HUD#TRPBF; electrical circuitry and the original child blocks remain unchanged. [ADI ordering specification](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC2962-2963-2964.pdf), [exact DigiKey offer](https://www.digikey.com/en/products/detail/analog-devices-inc/LTC2962HUD-PBF/9555593), [engineering receipt](../SOURCING_OPTIMIZATION_PROPOSAL.md).','',
        'Published tube tiers (component pieces): 1 $9.56000; 10 $7.43600; 25 $6.90640; 121 $6.26033; 363 $5.95245; 605 $5.83864; 1,089 $5.72638. Supplier MOQ/multiple are 1/1; the manufacturer standard package of 121 is not an order minimum. Packaging below the standard package may change through distributor services.','',
        '| Boards | Supervisor demand | Selected piece tier | Catalogue subtotal | Observed stock | Required stock shortfall |',
        '|---:|---:|---:|---:|---:|---:|']
    for build in BUILD_QUANTITIES:
        x=next(x for x in result['lines'] if x['mpn']=='LTC2962HUD#PBF' and x['build_boards']==build)
        out.append(f"| {build} | {x['required_pieces']} | {x['selected_tier_minimum']} | ${money(Decimal(x['published_purchase_cash_usd']))} | {x['observed_stock_pieces']} | {x['required_stock_shortfall_pieces']} |")
    out += ['', 'The 71 observed supervisors are unreserved and cover only the 3- and 30-piece demand for this one line. **300 pieces exceed observed stock by 229; $1,878.10 is a published-price calculation, not an available 100-board supply.** No full-build availability is inferred from this line. Delivery, tube handling, assembly fees, shipping, tariffs and tax remain unknown.','',
        '## Remaining MOQ excess','',
        '| Exact MPN | Per board | MOQ/multiple | USD/unit at MOQ | Minimum cash | Excess at 1 / 10 / 100 boards |',
        '|---|---:|---:|---:|---:|---:|']
    constrained=[mpn for mpn in sorted(groups) if any(x['mpn']==mpn and x['excess_pieces'] for x in result['lines'])]
    assert len(constrained)==2
    for mpn in constrained:
        o=offers[mpn];tier=max((t for t in o['price_breaks'] if t['minimum']<=o['minimum']),key=lambda t:t['minimum'])
        excess=' / '.join(str(next(x for x in result['lines'] if x['mpn']==mpn and x['build_boards']==b)['excess_pieces']) for b in BUILD_QUANTITIES)
        out.append(f"| [{mpn}]({o['source_url']}) | {len(groups[mpn])} | {o['minimum']}/{o['multiple']} | ${tier['unit_usd']} | ${money(Decimal(tier['unit_usd'])*o['minimum'])} | {excess} |")
    out += ['', 'The original PLT precision-resistor requirements are retained. No conditional lower-cost resistor proposal is applied. Eight other PLT values remain unpriced; generic cut-tape selectors do not waive the two listed 1,000-piece lot constraints.','',
        '## Ten unpriced exact MPNs','']
    for mpn in sorted(groups):
        if mpn not in offers:
            out.append(f"- **{mpn}**, {len(groups[mpn])}/board: {source['unknown_notes'].get(mpn,'No exact primary public USD offer verified; cost remains null.')}")
    out += ['', '## Separate modules and manufacture extras','',
        'Linux compute, ESP32 service/recovery, optional AI and complete touchscreen packages for 7-, 10-, 12-, 14-, 18- and 21-inch classes and further qualified sizes are absent from this MC. Their exact parts, quantity and cost remain separate null lines; display size does not change motion-channel scope. Required omitted interfaces, connectors and final architecture also remain unfinished.','',
        'PCBWay sourcing, bare PCB/stackup, assembly/stencil/setup/attrition, feeders/reeling/tube handling, programming/test fixtures, calibration, cooling, protection/PSU, enclosure, harnesses, shipping/tariffs/tax, packaging and warranty remain unknown. The optional Coilcraft leader/trailer charge is $25 per MPN ($50 for two); accepted assembly format is unquoted and no packaging fee is assumed zero.','',
        'The active Murata GRM188R72A104KA35D replacement remains 41 pieces per board. All other offers are retained from the dated r03 source catalogue. Full-reel prices are not credited to cut-tape quantities, discounts are not interpolated, and fitted inventory value is not substituted for purchasing cash.','',
        f"Frozen current BOM SHA256: `{result['input_bom_sha256']}`. Decimal arithmetic confirms purchasing cash equals fitted inventory value plus excess inventory value before display rounding at all quantities. This task did not change source, rerun native ERC/DRC, compile targets or make physical measurements."]
    (HERE/'MC_BOM_COST.md').write_text('\n'.join(out)+'\n',encoding='utf-8')


if __name__=='__main__': main()
