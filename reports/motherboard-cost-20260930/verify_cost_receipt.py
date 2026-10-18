"""Independent frozen-input/cost verification and in-memory negative controls.

Uses no build/calculate functions, does not change input receipts, and never
qualifies supplier stock or hardware. Writes only a fresh verification receipt.
"""
from pathlib import Path
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
import argparse, copy, csv, hashlib, json

HERE=Path(__file__).resolve().parent
MCREL=Path("reports/board-completion-20260930/mc-bom-cost-r04")


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def amount(v): return str(v.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP))


def validate(payload, frozen, model, original, additional):
    groups=defaultdict(list)
    for row in frozen: groups[row['MPN']].append(row)
    offers={p['mpn']:p for p in original['offers']}
    assert len(offers)==len(original['offers'])
    for p in additional['offers']:
        assert p['mpn'] not in offers
        offers[p['mpn']]=p
    assert payload['original_MC_offers']==original['offers']
    assert payload['additional_exact_MPN_offers']==additional['offers']
    assert payload['manufacturing_ready'] is False
    assert payload['physical_qualification'] is False
    assert payload['procurement_qualified'] is False
    assert payload['supplier_contact'] is False and payload['orders'] is False
    assert len(payload['lines'])==3*len(groups)
    line_lookup={(r['build_boards'],r['mpn']):r for r in payload['lines']}
    assert len(line_lookup)==len(payload['lines'])
    errors=[]
    for boards in (1,10,100):
        sums=dict(cash=Decimal(0),used=Decimal(0),extra=Decimal(0),matched=Decimal(0))
        counts=dict(priced=0,unknown=0,priced_pieces=0,unknown_pieces=0,moq=0,short=0,unknown_stock=0)
        for mpn, components in groups.items():
            r=line_lookup[boards,mpn]
            refs=sorted(p['Reference'] for p in components if not model['components'][p['Reference']].get('dnp',False))
            dnp=sorted(p['Reference'] for p in components if model['components'][p['Reference']].get('dnp',False))
            need=boards*len(refs)
            assert r['physical_footprints_per_board']==len(components)
            assert r['fitted_per_board']==len(refs) and r['dnp_per_board']==len(dnp)
            assert r['fitted_references']==refs and r['dnp_references']==dnp
            assert r['required_pieces']==need
            o=offers.get(mpn)
            if o and need:
                minimum,multiple=int(o['minimum']),int(o['multiple'])
                buy=minimum
                if buy<need: buy=((need+multiple-1)//multiple)*multiple
                if buy%multiple: buy=((buy+multiple-1)//multiple)*multiple
                # Select the last satisfied tier without the builder's max/generator.
                eligible=sorted((p for p in o['price_breaks'] if p['minimum']<=buy),key=lambda p:p['minimum'])
                t=eligible[-1]; price=Decimal(t['unit_usd'])
                consumed=price*need;cash=price*buy; excess=buy-need
                assert r['minimum']==minimum and r['multiple']==multiple
                assert r['buy_pieces']==buy and r['excess_pieces']==excess
                assert r['selected_tier_minimum']==t['minimum']
                assert Decimal(r['unit_usd'])==price
                assert Decimal(r['consumed_inventory_value_usd'])==consumed
                assert Decimal(r['published_purchase_cash_usd'])==cash
                assert r['quantity_matched_purchase_cash_usd']==(str(cash) if excess==0 else None)
                assert r['source_url']==o['source_url'] and r['observed_date']==o['observed_date']
                assert r['supplier']==o['supplier'] and r['packaging']==o['packaging']
                stock=o.get('observed_stock_pieces')
                stock=int(stock) if stock is not None else None
                assert r['observed_stock_pieces']==stock
                assert r['observed_stock_covers_required']==(stock>=need if stock is not None else None)
                assert r['observed_stock_covers_buy']==(stock>=buy if stock is not None else None)
                assert r['required_stock_shortfall_pieces']==(max(0,need-stock) if stock is not None else None)
                assert r['buy_stock_shortfall_pieces']==(max(0,buy-stock) if stock is not None else None)
                assert r['availability_qualified'] is False
                sums['cash']+=cash;sums['used']+=consumed;sums['extra']+=excess*price
                counts['priced']+=1;counts['priced_pieces']+=need
                if excess: counts['moq']+=1
                else:sums['matched']+=cash
                if stock is None:counts['unknown_stock']+=1
                elif stock<buy:counts['short']+=1
            elif need:
                assert r['status']=='unpriced'
                for k in ['unit_usd','consumed_inventory_value_usd','published_purchase_cash_usd',
                          'quantity_matched_purchase_cash_usd','observed_stock_pieces','source_url','selected_tier_minimum']:
                    assert r[k] is None, f'Unknown is not zero or borrowed price: {mpn}/{k}'
                counts['unknown']+=1;counts['unknown_pieces']+=need
                if mpn.startswith('PLT0603') and mpn.endswith('T1'):
                    assert r['minimum']==1000 and r['multiple']==1000
                    assert r['buy_pieces']==max(1000,((need+999)//1000)*1000)
            else:assert r['status']=='DNP_only_no_purchase'
        s=next(s for s in payload['summaries'] if s['build_boards']==boards)
        assert s['physical_footprint_pieces']==len(frozen)*boards
        total=sum(not p.get('dnp',False) for p in model['components'].values())*boards
        assert s['fitted_component_pieces']==total
        assert s['dnp_footprint_pieces']==len(frozen)*boards-total
        assert s['unique_BOM_mpns']==len(groups)
        assert s['priced_mpn_count']==counts['priced'] and s['unpriced_mpn_count']==counts['unknown']
        assert s['priced_fitted_component_pieces']==counts['priced_pieces']
        assert s['unpriced_fitted_component_pieces']==counts['unknown_pieces']
        assert s['quantity_matching_mpn_count']==counts['priced']-counts['moq']
        assert s['MOQ_excess_priced_mpn_count']==counts['moq']
        assert s['priced_mpn_observed_stock_shortfall_count']==counts['short']
        assert s['priced_mpn_stock_unknown_count']==counts['unknown_stock']
        assert sums['cash']==sums['used']+sums['extra']
        assert s['known_quantity_matching_subtotal_usd']==amount(sums['matched'])
        assert s['known_consumed_inventory_value_subtotal_usd']==amount(sums['used'])
        assert s['known_consumed_inventory_value_per_board_usd']==amount(sums['used']/boards)
        assert s['known_catalogue_purchase_cash_subtotal_usd']==amount(sums['cash'])
        assert s['known_excess_inventory_value_usd']==amount(sums['extra'])
        for k in ['full_component_purchase_total_usd','stock_qualified_purchase_total_usd',
                  'complete_manufactured_custom_board_total_usd','complete_controller_kit_total_usd']:
            assert s[k] is None, f'Unsupported complete total: {k}'
    for p in payload['unselected_off_board_modules']:
        assert p['selected_mpn'] is None and p['cost_usd_by_build']=={'1':None,'10':None,'100':None}
    assert len(payload['unselected_off_board_modules'])==10
    for p in payload['manufacturing_extras_unknown']:
        assert p['quote_exists'] is False and all(v is None for v in p['cost_usd_by_build'].values())
    for p in payload['missing_motherboard_source_regions']:
        assert p['missing_part_count'] is None and p['missing_cost_usd'] is None
    part=next(p for p in payload['nominal_package_screen'] if p['mpn']=='T20F256I4')
    assert '13x13mm/0.8mm' in part['nominal_package'], 'Wrong Efinix package envelope'
    # Same-pin DFF names must not be misrepresented as a dual/14-pin package.
    for p in payload['nominal_package_screen']:
        if p['mpn']=='SN74LVC2G74DCUR':
            assert any('SINGLE 8-pin' in n for n in p['sourcing_notes'])
    return len(payload['lines'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('snapshot');args=parser.parse_args()
    out=HERE/args.snapshot
    snapshot=json.loads((out/'snapshot.json').read_text())
    issued=json.loads((out/'receipt.json').read_text())
    for rel,h in snapshot['files_sha256'].items():assert sha(out/'inputs'/rel)==h
    for rel,h in issued['artifacts_sha256'].items():assert sha(out/rel)==h
    assert sha(out/'snapshot.json')==issued['input_snapshot_sha256']
    assert sha(out/'CATALOGUE_OBSERVATIONS.json')==issued['observation_sha256']
    assert sha(out/'motherboard_cost_audit.py')==issued['issued_tool_sha256']
    result=json.loads((out/'MOTHERBOARD_COST.json').read_text())
    model=json.loads((out/'inputs/hardware/motherboard/design.json').read_text())
    with (out/'inputs/hardware/motherboard/bom.csv').open(newline='') as f:frozen=list(csv.DictReader(f))
    original=json.loads((out/'inputs'/MCREL/'MC_BOM_PRICE_SOURCES.json').read_text())
    additional=json.loads((out/'CATALOGUE_OBSERVATIONS.json').read_text())
    count=validate(result,frozen,model,original,additional)
    def line(data,build,mpn):return next(r for r in data['lines'] if r['build_boards']==build and r['mpn']==mpn)
    controls=[]
    def reject(name,mutate):
        broken=copy.deepcopy(result);mutate(broken)
        try:validate(broken,frozen,model,original,additional)
        except (AssertionError,ValueError,TypeError,StopIteration,KeyError) as error:
            controls.append(dict(name=name,rejected=True,reason=str(error)));return
        raise AssertionError(f'Negative control accepted: {name}')
    reject('DNP physical termination footprint is not a fitted purchase',
        lambda d:line(d,1,'CRCW1210120RFKEA').update(fitted_per_board=16,required_pieces=16))
    unknown=next(r['mpn'] for r in result['lines'] if r['status']=='unpriced')
    reject('unknown unit price must not become zero',lambda d:line(d,1,unknown).update(unit_usd='0'))
    reject('MOQ lot cash must not equal two fitted resistors',
        lambda d:line(d,1,'PLT0603Z1001LST1').update(buy_pieces=2,published_purchase_cash_usd='11.26'))
    reject('71 supervisors cannot cover 300-piece demand',
        lambda d:line(d,100,'LTC2962HUD#PBF').update(observed_stock_covers_required=True,required_stock_shortfall_pieces=0))
    reject('unit discount tier requires actual piece demand',
        lambda d:line(d,1,'CRCW060310K0FKEA').update(unit_usd='0.00893',selected_tier_minimum=1000))
    reject('complete manufactured board total remains null',
        lambda d:d['summaries'][0].update(complete_manufactured_custom_board_total_usd='0'))
    reject('unselected compute SKU cannot acquire an invented cost',
        lambda d:d['unselected_off_board_modules'][0].update(selected_mpn='invented',cost_usd_by_build={'1':'40','10':'40','100':'40'}))
    reject('unpriced MPN count cannot understate unknowns',
        lambda d:d['summaries'][0].update(unpriced_mpn_count=d['summaries'][0]['unpriced_mpn_count']-1))
    reject('Efinix exact source package must remain 13mm/0.8mm',
        lambda d:next(p for p in d['nominal_package_screen'] if p['mpn']=='T20F256I4').update(nominal_package='9x9mm/0.5mm'))
    for mpn in ['TLP3640A(TPL,E)','TLP4176A(TP,F)']:
        if (1,mpn) in {(r['build_boards'],r['mpn']) for r in result['lines']}:
            reject('punctuation-distinct MPN price cannot be borrowed: '+mpn,
                lambda d,m=mpn:line(d,1,m).update(unit_usd='1.00',published_purchase_cash_usd='12.00'))
    verification=dict(schema_version=1,scope='Independent immutable hash, exact-MPN grouping, Decimal purchase/consumption/MOQ/stock/null/DNP checks and negative controls only.',
        snapshot=args.snapshot,frozen_files_verified=len(snapshot['files_sha256']),quantity_lines_checked=count,
        negative_controls=controls,negative_controls_passed=len(controls),
        source_hardware_changed=False,native_ERC_DRC=False,physical_measurements=False,
        source_cost_json_sha256=sha(out/'MOTHERBOARD_COST.json'),verifier_sha256=sha(Path(__file__)))
    verification['pass']=True
    (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps({k:v for k,v in verification.items() if k!='negative_controls'},indent=2))


if __name__=='__main__':main()
