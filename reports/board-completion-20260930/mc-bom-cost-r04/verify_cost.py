"""Independent report-only arithmetic/freshness checks and negative controls."""
import copy
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path(r'C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller')


def rounded(x): return str(x.quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
def hashed(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(result,source,rows):
    problems=[];counts=Counter(r['MPN'] for r in rows)
    refs={mpn:{r['Reference'] for r in rows if r['MPN']==mpn} for mpn in counts}
    offers={o['mpn']:o for o in source['offers']}
    lines={(x['build_boards'],x['mpn']):x for x in result['lines']}
    if len(lines)!=156 or set(lines)!={(q,p) for q in (1,10,100) for p in counts}:
        problems.append('Every exact MPN must appear once at every quantity')
    for build in (1,10,100):
        totals={'cash':Decimal(0),'consumed':Decimal(0),'excess':Decimal(0),'matched':Decimal(0)}
        unpriced=moqs=0
        for mpn,count in counts.items():
            line=lines[build,mpn];demand=count*build
            if (line['required_pieces'],line['per_board_quantity'],set(line['references']))!=(demand,count,refs[mpn]):
                problems.append('Incorrect aggregate demand/references '+mpn)
            if mpn not in offers:
                unpriced+=1
                if any(line[k] is not None for k in ('buy_pieces','unit_usd','published_purchase_cash_usd','consumed_inventory_value_usd')):
                    problems.append('Unpriced part must remain null '+mpn)
                continue
            offer=offers[mpn]
            quotient,remainder=divmod(demand,offer['multiple'])
            buy=offer['multiple']*(quotient+bool(remainder))
            buy=max(buy,offer['minimum'])
            chosen=None
            for tier in sorted(offer['price_breaks'],key=lambda x:x['minimum']):
                if tier['minimum']>buy: break
                chosen=tier
            unit=Decimal(chosen['unit_usd']);cash=unit*buy;used=unit*demand;extra=unit*(buy-demand)
            if (line['buy_pieces'],line['excess_pieces'],line['selected_tier_minimum'])!=(buy,buy-demand,chosen['minimum']):
                problems.append('Wrong MOQ/multiple/tier '+mpn)
            for key,expected in [('unit_usd',unit),('published_purchase_cash_usd',cash),('consumed_inventory_value_usd',used)]:
                if Decimal(line[key])!=expected: problems.append('Incorrect catalogue arithmetic '+mpn+' '+key)
            totals['cash']+=cash;totals['consumed']+=used;totals['excess']+=extra
            if buy==demand: totals['matched']+=cash
            else: moqs+=1
            stock=offer.get('observed_stock_pieces')
            stock=int(stock) if stock is not None else None
            if line['observed_stock_pieces']!=stock: problems.append('Stock evidence mismatch '+mpn)
            if stock is not None:
                if line['observed_stock_covers_required']!=(stock>=demand) or line['observed_stock_covers_buy']!=(stock>=buy):
                    problems.append('Unsupported on-hand claim '+mpn)
                if line['required_stock_shortfall_pieces']!=max(0,demand-stock): problems.append('Missing demand shortfall '+mpn)
            if line['availability_qualified']: problems.append('Unqualified availability claim '+mpn)
        summary=next(s for s in result['summaries'] if s['build_boards']==build)
        if (summary['unpriced_mpn_count'],summary['moq_excess_mpn_count'],summary['quantity_matching_mpn_count'])!=(10,2,40):
            problems.append('Incorrect known/unknown/MOQ counts')
        for key,total in [('known_published_purchase_cash_subtotal_usd','cash'),('known_consumed_inventory_value_subtotal_usd','consumed'),
                          ('known_excess_inventory_value_usd','excess'),('known_quantity_matching_subtotal_usd','matched')]:
            if summary[key]!=rounded(totals[total]): problems.append('Incorrect subtotal '+key)
        if totals['cash']!=totals['consumed']+totals['excess']: problems.append('Cash allocation identity fails')
        if any(summary[k] is not None for k in ('stock_qualified_purchase_total_usd','complete_mc_manufactured_total_usd','complete_controller_total_usd')):
            problems.append('Unsupported complete/available total')
    return problems


def main():
    source=json.loads((HERE/'MC_BOM_PRICE_SOURCES.json').read_text())
    result=json.loads((HERE/'MC_BOM_COST.json').read_text())
    with (HERE/'MC_BOM_INPUT.csv').open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    assert len(rows)==327 and len({r['MPN'] for r in rows})==52
    assert not audit(result,source,rows)
    pbf=[x for x in result['lines'] if x['mpn']=='LTC2962HUD#PBF']
    assert [(x['required_pieces'],x['selected_tier_minimum'],x['required_stock_shortfall_pieces']) for x in pbf]==[(3,1,0),(30,25,0),(300,121,229)]
    known_cash=[s['known_published_purchase_cash_subtotal_usd'] for s in result['summaries']]
    assert known_cash==['11294.31','11902.90','17011.68']
    for p,h in result['current_source_sha256'].items(): assert hashed(ROOT/p)==h
    for p,h in result['historical_r03_artifacts_preserved_sha256'].items(): assert hashed(ROOT/p)==h
    assert result['input_bom_sha256']==hashed(HERE/'MC_BOM_INPUT.csv')==hashed(ROOT/'hardware/motion_card/bom.csv')
    old=json.loads((ROOT/'reports/board-completion-20260930/MC_BOM_PRICE_SOURCES.json').read_text())
    oldoffers={o['mpn']:o for o in old['offers']}
    for o in source['offers']:
        if o['mpn']!='LTC2962HUD#PBF': assert o==oldoffers[o['mpn']]
    assert set(oldoffers)-{o['mpn'] for o in source['offers']}=={'LTC2962HUD#TRPBF'}
    negatives=[]
    def mutated(name,change):
        candidate=copy.deepcopy(result);change(candidate)
        failures=audit(candidate,source,rows);assert failures,name
        negatives.append({'name':name,'rejected':True,'detected':failures})
    def pbf100(j): return next(x for x in j['lines'] if x['mpn']=='LTC2962HUD#PBF' and x['build_boards']==100)
    mutated('aggregate three supervisors before scaling',lambda j:pbf100(j).update(required_pieces=100))
    mutated('no unearned highest-volume tier',lambda j:pbf100(j).update(unit_usd='5.72638'))
    mutated('300-piece demand cannot claim observed 71 covers it',lambda j:pbf100(j).update(observed_stock_covers_required=True))
    mutated('229-piece supervisor shortfall cannot be hidden',lambda j:pbf100(j).update(required_stock_shortfall_pieces=0))
    mutated('unknown part is not zero',lambda j:next(x for x in j['lines'] if x['status']=='unpriced').update(published_purchase_cash_usd='0'))
    mutated('complete controller total remains unknown',lambda j:j['summaries'][0].update(complete_controller_total_usd='11294.31'))
    mutated('only two remaining MOQ lines',lambda j:j['summaries'][0].update(moq_excess_mpn_count=3))
    mutated('catalogue stock is not procurement qualification',lambda j:pbf100(j).update(availability_qualified=True))
    receipt={'schema_version':1,'date_utc':datetime.now(timezone.utc).isoformat(),'pass':True,
             'scope':'Independent Decimal arithmetic, exact-MPN aggregation, tier selection, stock/null negative controls and source/history hash preservation; report-only.',
             'quantity_lines_checked':156,'negative_controls':negatives,'negative_controls_passed':len(negatives),
             'current_bom_sha256':result['input_bom_sha256'],'catalogue_cash_usd':known_cash,
             'ten_unpriced_mpns':sorted({x['mpn'] for x in result['lines'] if x['status']=='unpriced'}),
             'inherited_price_offers_unchanged':41,'historical_r03_files_unchanged':len(result['historical_r03_artifacts_preserved_sha256']),
             'current_source_files_unchanged':len(result['current_source_sha256']),
             'native_exports_rerun':False,'physical_measurements':False,'target_compilation':False,'supplier_contact':False,
             'manufacturing_ready':False,'resistor_changes':False,
             'report_sha256':{p.name:hashed(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='receipt.json'}}
    (HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'pass':True,'lines':156,'negative_controls':len(negatives),'historical_files_unchanged':6,'current_source_files_unchanged':6,'receipt':str(HERE/'receipt.json')}))


if __name__=='__main__': main()
