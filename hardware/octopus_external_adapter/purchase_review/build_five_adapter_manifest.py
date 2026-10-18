"""Read-only BOM reconciliation; writes procurement review artifacts only."""
from pathlib import Path
import json
import hashlib
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
native_path = ROOT / 'r0_3' / 'parts.json'
cost_path = ROOT / 'r0_3_planning' / 'full-bom-cost.json'
native = json.loads(native_path.read_text(encoding='utf-8'))
cost = json.loads(cost_path.read_text(encoding='utf-8'))
canonical = lambda x: x.replace('ERJP08F82R0V', 'ERJ-P08F82R0V')
refs = defaultdict(list)
for ref, part in native['parts'].items():
    if part['in_bom']:
        refs[canonical(part['mpn'])].append(ref)

verified_ids = {
    'AP7375-33SA-7': '31-AP7375-33SA-7CT-ND',
    'PMV100EPAR': '1727-PMV100EPARCT-ND',
    'BAT46W-7-F': 'BAT46W-7FDICT-ND',
    'PMEG6010CEH,115': '1727-PMEG6010CEH,115CT-ND',
    'BZT52C12-7-F': 'BZT52C12-FDICT-ND',
    'BZT52C5V1-7-F': 'BZT52C5V1-FDICT-ND',
    'CL10B104KB8NNNC': '1276-1000-1-ND',
    'CL31A226KAHNNNE': '1276-3047-1-ND',
    'ATTINY202-SSNR': 'ATTINY202-SSNRCT-ND',
    'NX6008NBKR': '1727-NX6008NBKRCT-ND',
    'ERJ-P08F82R0V': '10-ERJ-P08F82R0VCT-ND',
    'SF-1206F050-2': 'SF-1206F050-2CT-ND',
    'SRN5040-150M': 'SRN5040-150MCT-ND',
    'MP2459GJ-Z': '1589-1895-1-ND',
    'SMAJ28CA-13-F': 'SMAJ28CA-FDICT-ND',
    'LTST-C190KRKT': '160-1436-1-ND',
    'CL21B225KAFNNNE': '1276-2954-1-ND',
    'CL31B475KBHNNNE': '1276-2789-1-ND',
    'RC0603FR-07100KL': '311-100KHRCT-ND',
    'RC0603FR-0710KL': '311-10.0KHRCT-ND',
    'RC0603FR-071KL': '311-1.00KHRCT-ND',
    'RC0603FR-074K7L': '311-4.70KHRCT-ND',
    'RC0805FR-0710KL': '311-10.0KCRCT-ND',
    'RC0805FR-07330RL': '311-330CRCT-ND',
    'RT0603BRD07100KL': 'YAG1235CT-ND',
    'RT0603BRD07124KL': 'YAG1515CT-ND',
    'RT0603BRD0723K7L': 'YAG4508CT-ND',
    'RT0603BRD073K9L': 'YAG1656CT-ND',
}
refreshed = {
    'AP7375-33SA-7': {'in_stock': 0, 'note': 'No estimated in-stock date displayed.'},
    'PMV100EPAR': {'in_stock': 3, 'note': 'Five are required; shortage of two at this observation.'},
    'BAT46W-7-F': {'in_stock': 0, 'note': 'No estimated in-stock date displayed.'},
    'PMEG6010CEH,115': {'in_stock': 0, 'note': '3,000 expected 18-Oct-2027 displayed; not a delivery guarantee.'},
    'CL31A226KAHNNNE': {'in_stock': 0, 'note': 'Exact part out of stock.'},
}
rows=[]
for row in cost['rows']:
    mpn=canonical(row['mpn'])
    assert set(refs[mpn]) == set(row['references']), (mpn, refs[mpn], row['references'])
    assert len(refs[mpn]) == row['quantity_per_adapter']
    rows.append({
        'mpn':mpn, 'manufacturer':row['manufacturer'],
        'references':row['references'], 'values':row['values'],
        'quantity_per_adapter':len(refs[mpn]),
        'quantity_for_five_adapters':5*len(refs[mpn]),
        'extra_spares':0,
        'supplier':'DigiKey',
        'supplier_part_number':verified_ids.get(mpn),
        'supplier_part_number_status': 'Refreshed from exact DigiKey product page' if mpn in verified_ids else 'Exact MPN/product URL supplied; parent will resolve package in cart',
        'supplier_product_url':row['sources'][0],
        'preferred_packaging':'Cut tape or bulk as appropriate; no Digi-Reel or full reel',
        'earlier_availability_notes':row['availability_notes'],
        'current_independent_check':refreshed.get(mpn, {'in_stock':None,'note':'Stock not independently refreshed in this review; actual cart is authoritative.'}),
    })
assert len(rows)==33
assert sum(x['quantity_per_adapter'] for x in rows)==52
assert sum(x['quantity_for_five_adapters'] for x in rows)==260
assert len(set(ref for row in rows for ref in row['references']))==52
result={
    'date':'2026-10-06', 'design_revision':'OEA r0.3 prototype candidate, not released',
    'purpose':'Five-adapter cart preparation and independent exact-MPN quantity reconciliation; not a manufacturing release',
    'board_quantity':5, 'fitted_components_per_adapter':52, 'unique_mpns':33,
    'total_components_without_extra_spares':260, 'cart_mutated_by_this_agent':False,
    'excluded':['Three bare PCB test pads per adapter (no purchased component)', 'Blank PCB', 'Matching cable assemblies', 'Programmer/jig', 'Soldering equipment and consumables'],
    'notes':[
        'Quantities cover five assemblies: four working axes plus one complete spare adapter. No 100-board purchasing batch and no extra loose-part spares.',
        'All rows reconcile directly to the 52 purchased native schematic references.',
        'ERJP08F82R0V (native) and ERJ-P08F82R0V (supplier) are the same documented Panasonic ordering identifier with display punctuation.',
        'JST B4B-XH-A(LF)(SN) is supplied via the exact B4B-XH-A catalogue product, consistent with the existing manufacturer label-notation review.',
        'A distributor cut-tape suffix is packaging selection for the same manufacturer part, not an electrical substitution.',
        'No manufacturer part substitutions approved. DigiKey Suggested/Similar/Direct substitutes are not automatically accepted.',
        'Stock observations are not reserved and may differ from the browser cart. Backorder dates are not delivery promises.',
        'Mouser alternative-source searches produced stale or inaccessible stock pages; no currently verified alternate stock is asserted.',
        'PMEG6010CEH,115 and its DigiKey identifier contain commas; use quoted CSV/tab-separated bulk input or add individually to avoid delimiter ambiguity.',
    ],
    'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [native_path,cost_path]},
    'rows':rows,
}
out=ROOT/'purchase_review'/'five-adapter-exact-parts-20261006.json'
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
ct_result={
    'date':result['date'],
    'basis':'Each supplier part identifier transcribed from exact DigiKey product page DigiKey Part Number line, explicitly labelled Cut Tape (CT). No TR-to-CT guessing.',
    'complete_28_smt_mapping':len(verified_ids)==28,
    'cart_mutation_performed':False,
    'rows':[{k:r[k] for k in ['mpn','supplier_part_number','quantity_for_five_adapters','references','supplier_product_url']} for r in rows if r['supplier_part_number']],
}
(out.parent/'digikey-cuttape-mapping-20261006.json').write_text(json.dumps(ct_result,indent=2)+'\n',encoding='utf-8')
if len(verified_ids)==28:
    assert sum(r['quantity_for_five_adapters'] for r in ct_result['rows'])==235
    bulk_lines=[f"{r['quantity_for_five_adapters']}\t{r['supplier_part_number']}\tOEA r0.3 {','.join(r['references'])}" for r in ct_result['rows']]
    (out.parent/'digikey-cuttape-28-bulk-20261006.txt').write_text('\n'.join(bulk_lines)+'\n',encoding='utf-8')
lines=['OEA r0.3 — five-adapter procurement review, 2026-10-06',
       '52 fitted components/adapter; 33 exact MPNs; 260 pieces for five adapters.',
       'No extra loose-part spares. Cart mutation and stock reservation are not performed by this report.',
       'Prototype candidate; no manufacturing release.', '',
       'Qty | Manufacturer part | References | Source']
lines += [f"{r['quantity_for_five_adapters']:>3} | {r['mpn']} | {','.join(r['references'])} | {r['supplier_product_url']}" for r in rows]
lines += ['', 'Independently refreshed shortages:']
lines += [f"{mpn}: stock {s['in_stock']}. {s['note']}" for mpn,s in refreshed.items()]
lines += ['', *result['notes']]
out.with_suffix('.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'output':str(out),'mpns':len(rows),'pieces':260,'checks':'PASS'}))
