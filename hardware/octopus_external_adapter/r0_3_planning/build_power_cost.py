"""Separate catalogue-price evidence; never rewrites circuit snapshot."""
import json
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parent
spec=json.loads((R/'power_spec.json').read_text())
# quantity100 USD per-piece catalogue observations; not a live basket or quote.
prices={
'SF-1206F050-2':(.5204,'https://www.digikey.com/en/products/detail/bourns-inc/SF-1206F050-2/1948200','Stock not reserved'),
'SMAJ28CA-13-F':(.2300,'https://www.digikey.com/en/products/detail/diodes-incorporated/SMAJ28CA-13-F/765424','Page displayed stock'),
'PMV100EPAR':(.411,'https://www.mouser.com/es/ProductDetail/Nexperia/PMV100EPAR?qs=vmHwEFxEFR%2FYGVY%2F8WC8mQ%3D%3D','Stock not reserved'),
'BZT52C12-7-F':(.079,'https://www.digikey.com/en/products/detail/diodes-incorporated/BZT52C12-7-F/717847','Page displayed out of stock; future delivery. Exact -7-F active, distinct from EOL -7-F-79'),
'RC0603FR-07100KL':(.0122,'https://www.digikey.com/en/products/detail/yageo/RC0603FR-07100KL/729836','Page displayed stock'),
'PMEG6010CEH,115':(.179,'https://www.digikey.com/en/products/detail/nexperia-usa-inc/PMEG6010CEH-115/1589917','Stock not reserved'),
'MP2459GJ-Z':(.860,'https://www.monolithicpower.com/en/products/power-management/switching-converters-controllers/step-down-buck/converters/mp2459.html','Manufacturer direct100-piece tier; delivery not checked'),
'SRN5040-150M':(.264,'https://www.mouser.com/ProductDetail/Bourns/SRN5040-150M?qs=U0ECReq1GB%252BK3VpL6%2Fxonw%3D%3D','Stock not reserved'),
'CL31B475KBHNNNE':(.284,'https://www.mouser.com/en/ProductDetail/Samsung-Electro-Mechanics/CL31B475KBHNNNE?qs=349EhDEZ59puU52XGPBotQ%3D%3D','Page displayed zero stock/future delivery; not purchasable immediately from observed offer'),
'CL10B104KB8NNNC':(.0185,'https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL10B104KB8NNNC/3886658','Page displayed zero stock/future delivery'),
'CL31A226KAHNNNE':(.147,'https://www.mouser.co.za/ProductDetail/Samsung-Electro-Mechanics/CL31A226KAHNNNE?qs=X6jEic%2FHinCdwsjGJII51w%3D%3D','USD catalogue tier observed in search cache; direct page timed out; refresh before procurement'),
'RT0603BRD07124KL':(.0615,'https://www.digikey.com/en/products/detail/yageo/RT0603BRD07124KL/5138963','Page displayed stock'),
'RT0603BRD0723K7L':(.058,'https://www.digikey.com/en/products/detail/yageo/RT0603BRD0723K7L/6616664','Page displayed stock'),
'RC0805FR-0710KL':(.0171,'https://www.digikey.com/en/products/detail/yageo/RC0805FR-0710KL/730482','Page displayed stock'),
'BZT52C5V1-7-F':(.085,'https://www.mouser.vn/ProductDetail/Diodes-Incorporated/BZT52C5V1-7-F?qs=FFy5bLXC7EennpZVc1%2Fcow%3D%3D','USD catalogue tier; stock not reserved'),
'RC0603FR-0710KL':(.0122,'https://www.digikey.com/en/products/detail/yageo/RC0603FR-0710KL/726880','Page displayed stock'),
'ERJ-P08F82R0V':(.0689,'https://www.digikey.com/en/products/detail/panasonic-industry/ERJ-P08F82R0V/21282245','Page displayed zero stock; manufacturer format ERJP08F82R0V'),
'BAT46W-7-F':(.138,'https://br.mouser.com/ProductDetail/Diodes-Incorporated/BAT46W-7-F?qs=rGAXPo9uwV28x6kF8xdfEA%3D%3D','USD catalogue tier; stock not reserved'),
'AP7375-33SA-7':(.194,'https://www.mouser.com/es/ProductDetail/Diodes-Incorporated/AP7375-33SA-7?qs=t7xnP681wgUi6c6GDTa82w%3D%3D','Stock results inconsistent/backorder; basket must verify'),
'CL21B225KAFNNNE':(.0527,'https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL21B225KAFNNNE/3891040','Page displayed stock but NRND. Keep prototype candidate; refresh manufacturer lifecycle/qualified replacement before production'),
'RC0603FR-074K7L':(.0122,'https://www.digikey.com/en/products/detail/yageo/RC0603FR-074K7L/730159','Page displayed stock'),
'RC0805FR-07330RL':(.0171,'https://www.digikey.com/en/products/detail/yageo/RC0805FR-07330RL/727866','Page displayed stock')
}
# Refresh with directly opened US/USD pages; retain no stale regional price mix.
direct_refresh={
'PMV100EPAR':(.2357,'https://www.digikey.com/en/products/detail/nexperia-usa-inc/PMV100EPAR/12325038','DirectUS page displayed only3stock;100-piece tier is not immediately available'),
'MP2459GJ-Z':(.7112,'https://www.digikey.com/en/products/detail/monolithic-power-systems-inc/MP2459GJ-Z/5292061','DirectUS page displayed23190stock'),
'SRN5040-150M':(.2634,'https://www.digikey.com/en/products/detail/bourns-inc/SRN5040-150M/4867716','DirectUS page displayed6560stock'),
'CL31B475KBHNNNE':(.1417,'https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL31B475KBHNNNE/3888447','DirectUS page displayed29723stock; not reserved'),
'CL31A226KAHNNNE':(.182,'https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL31A226KAHNNNE/3891133','DirectUS page displayed zero stock/future delivery'),
'BZT52C5V1-7-F':(.079,'https://www.digikey.com/en/products/detail/diodes-incorporated/BZT52C5V1-7-F/717736','DirectUS page displayed zero stock/past-due delivery'),
'BAT46W-7-F':(.131,'https://www.digikey.com/en/products/detail/diodes-incorporated/BAT46W-7-F/1934440','DirectUS page displayed zero stock/date unavailable'),
'AP7375-33SA-7':(.1935,'https://www.digikey.com/en/products/detail/diodes-incorporated/AP7375-33SA-7/16400213','DirectUS page displayed zero stock/future delivery'),
'PMEG6010CEH,115':(.179,'https://www.digikey.com/en/products/detail/nexperia-usa-inc/PMEG6010CEH-115/1589917','DirectUS page displayed zero stock/future delivery'),
'ERJ-P08F82R0V':(.0689,'https://www.digikey.com/en/products/detail/panasonic-industry/ERJ-P08F82R0V/21282245','DirectUS page displayed3748stock; not reserved')
}
prices.update(direct_refresh)
qty1={
'SF-1206F050-2':.89,'SMAJ28CA-13-F':.59,'PMV100EPAR':.60,'BZT52C12-7-F':.21,
'RC0603FR-07100KL':.10,'PMEG6010CEH,115':.46,'MP2459GJ-Z':1.23,
'SRN5040-150M':.39,'CL31B475KBHNNNE':.37,'CL10B104KB8NNNC':.10,
'CL31A226KAHNNNE':.45,'RT0603BRD07124KL':.11,'RT0603BRD0723K7L':.10,
'RC0805FR-0710KL':.10,'BZT52C5V1-7-F':.21,'RC0603FR-0710KL':.10,
'ERJ-P08F82R0V':.23,'BAT46W-7-F':.34,'AP7375-33SA-7':.37,
'CL21B225KAFNNNE':.15,'RC0603FR-074K7L':.10,'RC0805FR-07330RL':.10
}
group=defaultdict(list)
for p in spec['parts']: group[p['mpn']].append(p['reference'])
rows=[]
for mpn,refs in group.items():
    price,url,status=prices[mpn]
    rows.append(dict(mpn=mpn,references=refs,quantity_per_adapter=len(refs),catalogue_price_tier_pieces=100,unit_usd=price,extended_per_adapter_usd=round(price*len(refs),6),price_source=url,availability_note=status,unit_usd_qty1=qty1.get(mpn),qty1_source=url,minimum_displayed_order_quantity=1,package='Cut tape (not Digi-Reel); no reeling fee assumed',qty1_not_stock_commitment=True))
total=round(sum(r['extended_per_adapter_usd'] for r in rows),6)
out=dict(date='2026-10-06',scope='Power subsystem only; catalogue observations at100-piece tier, not complete adapter or Amazon basket',circuit_revision=spec['revision'],fitted_part_count=len(spec['parts']),unique_mpn_count=len(rows),power_consumed_parts_usd_per_adapter=total,power_consumed_parts_usd_100_adapters=round(total*100,2),pcb_parent_observed_hasl_usd_per_adapter_at100=.9876,power_plus_provisional_hasl_pcb_only_usd=round(total+.9876,6),exclusions=['logic sinks and gate resistors','all connectors,headers,selector switch and matched four-wire harness','indicator MCU,LEDs,divider and its decoupling','component freight,taxes,duties,tariffs,minimum packs and spares','assembly,stencil,paste,hotplate,programmer,programming,inspection,test,loss/yield','packaging,sales fees,outbound freight,returns,support and profit'],procurement_ready=False,amazon_exact_mpn_basket_verified=False,catalogue_prices_not_stock_guarantees=True,rows=rows)
out['cost_revision']='US-direct-qty1-and100-2'
out['supersedes_initial_mixed_seller_power_subtotal_usd']=4.3945
out['power_qty1_tiers_consumed_subtotal_usd']=round(sum(r['quantity_per_adapter']*r['unit_usd_qty1'] for r in rows),6)
(R/'power-cost-observations.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['R0.3 power cost observations,2026-10-06','UNRELEASED; no parts ordered. This is consumed component cost, not a live quote.','MPN | refs | quantity/adapter | USD/part at100 | USD/adapter']
lines += [f"{r['mpn']} | {','.join(r['references'])} | {r['quantity_per_adapter']} | {r['unit_usd']:.5f} | {r['extended_per_adapter_usd']:.5f}" for r in rows]
lines += [f'POWER SUBSYSTEM ONLY: ${total:.5f}/adapter; ${total*100:.2f}/100.',f'Power plus provisional purple HASL PCB alone: ${total+.9876:.5f}/adapter.','The complete adapter and landed cost are higher; every exclusion remains to add.','Several exact offers are out of stock or NRND. Price evidence is not an immediately purchasable basket.','Same-MPN items conservatively use their100-piece tier, even where100 adapters consume200/300 pieces.','The old $4.98–6.83 planning envelope and $0.65–1.10 PCB+harness allowance are superseded.','The $6 landed target is not established. Keep the $15 resale ceiling without presenting it as manufacturing cost.','','Source URLs and availability notes:']
for r in rows: lines += [r['mpn']+': '+r['price_source'],r['availability_note']]
(R/'power-cost-observations.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
