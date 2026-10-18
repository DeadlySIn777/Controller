"""Append primary catalogue observations to immutable v4; never replace it."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

HERE=Path(__file__).resolve().parent
prior=HERE/'CATALOGUE_OBSERVATIONS-v4.json'
data=json.loads(prior.read_text(encoding='utf-8'))
data['previous_ledger_sha256']=hashlib.sha256(prior.read_bytes()).hexdigest()
data['created_utc']=datetime.now(timezone.utc).isoformat()
data['revision_note']='Add final r20b exact power and peripheral catalogue observations; no supplier substitution, stock reservation or orders.'

def add(mpn, slug, mfr, stock, ladder, package, minimum=1, multiple=1,
        packaging='Cut Tape', note='Primary distributor ordinary cut-tape tiers; no DigiReel fee or discount applied'):
    assert not any(p['mpn']==mpn for p in data['offers']),mpn
    data['offers'].append(dict(mpn=mpn, manufacturer=mfr, supplier='DigiKey', currency='USD',
        source_url='https://www.digikey.com/en/products/detail/'+slug,
        observed_date='2026-09-30',observed_utc_date='2026-10-01',source_cache_note=note,
        packaging=packaging,minimum=minimum,multiple=multiple,
        price_breaks=[dict(minimum=n,unit_usd=str(p)) for n,p in ladder],
        observed_stock_pieces=stock,supplier_package=package,
        price_kind='published_catalogue',availability_qualified=False,
        availability_note='Dated unreserved catalogue only. Shipping, tax, tariff, attrition and PCBWay sourcing/handling are unknown. Expected stock is not available stock.'))

add('OPA4197IPWR','texas-instruments/OPA4197IPWR/6553891','Texas Instruments',0,
    [(1,'4.72'),(10,'3.589'),(25,'3.3048'),(100,'2.9928'),(250,'2.8458')],'PW: TSSOP14')
add('TBU-CA025-050-WH','bourns-inc/TBU-CA025-050-WH/2407270','Bourns',30363,
    [(1,'2.89'),(10,'1.866'),(100,'1.2809'),(500,'1.03072'),(1000,'.95931')],'CA: 6.5 x 4 mm SMD')
add('TPS26630RGER','texas-instruments/TPS26630RGER/10820326','Texas Instruments',0,
    [(1,'4.52'),(10,'3.431'),(25,'3.1576'),(100,'2.8573'),(250,'2.71412'),(500,'2.71116')],'RGE: VQFN24')
add('74LVC125APW,118','nexperia-usa-inc/74LVC125APW-118/946678','Nexperia',0,
    [(1,'.25'),(10,'.169'),(25,'.1496'),(100,'.128'),(250,'.11768'),(500,'.1115'),(1000,'.10641')],'PW: TSSOP14')
add('10164227-1001A1RLF','amphenol-cs-fci/10164227-1001A1RLF/16908921','Amphenol ICC',13451,
    [(1,'1.75'),(10,'1.483'),(25,'1.39'),(50,'1.3236'),(100,'1.2604'),(250,'1.1814'),(500,'1.125'),(1000,'1.07129'),(2500,'1.04066')],
    '100-position 0.4 mm pitch mezzanine; 1.5 mm mated height')
add('TPS2553DBVR-1','texas-instruments/TPS2553DBVR-1/2047901','Texas Instruments',4978,
    [(1,'1.13'),(10,'.811'),(25,'.7324'),(100,'.6458'),(250,'.60448'),(500,'.57952'),(1000,'.56439')],'DBV: SOT23-6',
    note='Ordinary CT table only; separate cheaper DigiReel table plus $7 fee is excluded.')
add('TPS3700DDCR','texas-instruments/TPS3700DDCR/3137548','Texas Instruments',0,
    [(1,'2.52'),(10,'1.869'),(25,'1.7076'),(100,'1.5298'),(250,'1.44496'),(500,'1.4076')],'DDC: SOT23-6',
    note='Exact DDCR. Cheaper DDCR2 packing/type is not substituted; future receipts are not stock.')
add('LM706A0RRXR','texas-instruments/LM706A0RRXR/25811449','Texas Instruments',0,
    [(3000,'4.60306')],'RRX: VQFN-HR22',minimum=3000,multiple=3000,packaging='Tape & Reel',
    note='Available to order/not normally stocked. Only exact 3000-piece reel tier. Different MPN from remaining LM70660RRXR; its MOQ cannot be shared.')

# Exact manufacturer USD page shows single-piece tiers but no numerical stock.
# Below-full-reel tape is explicitly offered; machine-ready leader/trailer is a
# separate conditional $25 fee and remains outside this component-price basket.
data['offers'].append(dict(mpn='XAL1010-472MED',manufacturer='Coilcraft',supplier='Coilcraft',currency='USD',
    source_url='https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xal/xal1010/xal1010-472/',
    observed_date='2026-09-30',observed_utc_date='2026-10-01',
    source_cache_note='US-dollar catalogue tier and exact MED configuration. Numeric stock absent and page also contains unavailable-configuration text; no order availability inferred.',
    packaging='D: 13-inch reel / less-than-full-reel tape',minimum=1,multiple=1,
    price_breaks=[dict(minimum=n,unit_usd=p) for n,p in [(1,'5.96'),(100,'5.22'),(300,'3.91'),(600,'2.36'),(1200,'1.84'),(2400,'1.58'),(5000,'1.46')]],
    observed_stock_pieces=None,supplier_package='10.9 x 10.4 mm molded inductor; MED 4.7uH 20%',
    price_kind='published_catalogue',availability_qualified=False,
    availability_note='Full reel300. Below full reel available in non-machine-ready tape or with $25 leader/trailer; fee is conditional and excluded. Exact supply acceptance, handling, attrition and stock unknown. No SGD/CAD converted prices or JLC assembly-only stock used.',
    conditional_machine_ready_fee_usd='25.00',full_reel_pieces=300))

target=HERE/'CATALOGUE_OBSERVATIONS-v5.json'
assert not target.exists(),target
target.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(path=str(target),offers=len(data['offers']),modules=len(data['module_offers']),accessories=len(data['accessory_offers']),sha256=hashlib.sha256(target.read_bytes()).hexdigest())))
