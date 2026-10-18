"""Record exact-MPN primary catalogue observations, never replace old receipts.

Manual transcription of primary public pages returned through web lookup on
30 Sep 2026 local / 1 Oct 2026 UTC. Stock is dated, unreserved and unqualified.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json

HERE=Path(__file__).resolve().parent
prior=HERE/'CATALOGUE_OBSERVATIONS-v2.json'
data=json.loads(prior.read_text())
data['previous_ledger_sha256']=hashlib.sha256(prior.read_bytes()).hexdigest()
data['revision_note']='Add source-reviewed complete-parent exact MPN catalogue observations; preserve all original MC and v2 dated offers. Module/accessory costs remain separate.'
data['created_utc']=datetime.now(timezone.utc).isoformat()
data['date']='2026-09-30'
data['observed_local_date']='2026-09-30'
data['observed_utc_date']='2026-10-01'
data['module_offers']=[]
data['accessory_offers']=[]

def add(mpn,slug,mfr,stock,ladder,package,packaging='Cut Tape',minimum=1,multiple=1,target='offers',note='Returned primary catalogue page; stock is not reserved'):
    assert not any(p['mpn']==mpn for p in data[target]),mpn
    data[target].append(dict(mpn=mpn,manufacturer=mfr,supplier='DigiKey',currency='USD',
        source_url='https://www.digikey.com/en/products/detail/'+slug,
        observed_date='2026-09-30',observed_utc_date='2026-10-01',source_cache_note=note,
        packaging=packaging,minimum=minimum,multiple=multiple,
        price_breaks=[dict(minimum=n,unit_usd=str(p)) for n,p in ladder],
        observed_stock_pieces=stock,supplier_package=package,
        price_kind='published_catalogue',availability_qualified=False,
        availability_note='Dated public catalogue only. No delivery, revision, PCBWay handling, reeling, tariff, shipping or tax qualification. Expected future inventory is not available stock.'))

add('INA149AIDR','texas-instruments/INA149AIDR/2795673','Texas Instruments',0,
    [(1,'8.48000'),(10,'6.57200'),(25,'6.09520'),(100,'5.57100'),(250,'5.44376')],'D: SOIC8')
add('TPS274C65ASRHAR','texas-instruments/TPS274C65ASRHAR/22106845','Texas Instruments',818,
    [(1,'6.37000'),(10,'4.88800'),(25,'4.51840'),(100,'4.11140'),(250,'3.96576')],'RHA: VQFN40 / 6x6mm')
add('ISO7762FDBQR','texas-instruments/ISO7762FDBQR/9371255','Texas Instruments',232,
    [(1,'3.55000'),(10,'2.66400'),(25,'2.44240'),(100,'2.19910'),(250,'2.08296'),(500,'2.05482'),(1000,'1.93851')],'DBQ: SSOP16')
add('ADS8684AIDBTR','texas-instruments/ADS8684AIDBTR/6571586','Texas Instruments',0,
    [(2000,'10.97096')],'DBT: TSSOP38','Tape & Reel',2000,2000,
    note='Exact -R MPN is non-stocked and only a 2000-piece reel tier was posted. MOQ cash is explicit; no sibling non-R or older non-A price applied.')
add('AD5683RBRMZ-3','analog-devices-inc/AD5683RBRMZ-3/4866815','Analog Devices',0,
    [(1,'10.91000'),(10,'8.53000'),(50,'7.57520'),(100,'7.27980'),(250,'6.96780'),(500,'6.77980'),(1000,'6.62503')],'RM: MSOP10','Tube',
    note='Exact tube MPN. The stocked -RL7 suffix is excluded, not silently substituted.')
add('ESP32-S3-DEVKITC-1-N8R8','espressif-systems/ESP32-S3-DEVKITC-1-N8R8/15295894','Espressif Systems',0,
    [(1,'15.00000')],'DevKitC development module','Bulk',target='module_offers',
    note='Only one public price tier. Catalog capitalization matches the selected type name; actual required v1.1 PCB revision is not identified or stock-qualified.')
for mpn,slug in [('ISOW1044DFMR','ISOW1044DFMR/15856616'),('ISOW1432DFMR','ISOW1432DFMR/21520469')]:
    add(mpn,'texas-instruments/'+slug,'Texas Instruments',0,
        [(1,'10.00000'),(10,'7.79400'),(25,'7.24280'),(100,'6.63670'),(250,'6.53156')],'DFM: SOIC20 / 7.5mm body')
add('ISO7720FDWR','texas-instruments/ISO7720FDWR/6590806','Texas Instruments',4228,
    [(1,'2.81000'),(10,'2.09400'),(25,'1.91520'),(100,'1.71900'),(250,'1.62544'),(500,'1.56902'),(1000,'1.52261')],'DW: SOIC16 / 7.5mm body',
    note='Reopened primary page today; earlier search-cache 2.60 USD was superseded before this ledger was issued.')
add('TMR 1-2412','traco-power/TMR-1-2412/9383377','TRACO Power',56,
    [(1,'10.14000'),(5,'9.76000'),(10,'9.60200'),(30,'9.35667'),(50,'9.24460'),(100,'9.09430'),(250,'8.89912'),(500,'8.75402')],'SIP6 / four electrical leads','Tube',
    note='56 distributor pieces only; displayed factory-stock 70 not aggregated with distributor inventory.')
add('1844317','phoenix-contact/1844317/349202','Phoenix Contact',0,
    [(1,'4.97000'),(10,'4.03900')],'12-position 3.5mm right-angle through-hole header','Bulk')
add('1844333','phoenix-contact/1844333/2528017','Phoenix Contact',0,
    [(1,'5.77000'),(10,'4.69000')],'14-position 3.5mm right-angle through-hole header','Bulk')
add('STM32G031K8T6','stmicroelectronics/STM32G031K8T6/10300267','STMicroelectronics',21631,
    [(1,'2.83000'),(10,'2.09700'),(50,'1.80360'),(100,'1.71290'),(250,'1.61708'),(500,'1.55932')],'LQFP32 / 7x7mm / 0.8mm pitch','Tray')
add('STM32G031C8T6','stmicroelectronics/STM32G031C8T6/10300269','STMicroelectronics',1766,
    [(1,'2.68000'),(10,'1.98800'),(50,'1.71040'),(100,'1.62440'),(250,'1.53364'),(500,'1.47888')],'LQFP48 / 7x7mm / 0.5mm pitch','Tray',
    note='Reopened primary page today; older search-cache 2.42 USD and 524 stock were excluded before ledger issuance.')
add('LM70660RRXR','texas-instruments/LM70660RRXR/25811544','Texas Instruments',0,
    [(3000,'4.37360')],'RRX: VQFN29 / 6x6mm','Tape & Reel',3000,3000,
    note='Exact -R non-stocked product only posts 3000-piece reel; no smaller-package type or family estimate applied.')
add('MCP2518FDT-E/SL','microchip-technology/MCP2518FDT-E-SL/10231405','Microchip Technology',18825,
    [(1,'1.96000'),(25,'1.63720')],'SL: SOIC14')
add('MAX17612AATB+T','analog-devices-inc-maxim-integrated/MAX17612AATB-T/9833469','Analog Devices',3166,
    [(1,'4.45000'),(10,'3.37300'),(25,'3.10400'),(100,'2.80800'),(250,'2.66688'),(500,'2.66220')],'TDFN10 EP / 3x3mm')
add('ISO1540DR','texas-instruments/ISO1540DR/3587222','Texas Instruments',8371,
    [(1,'4.68000'),(10,'3.55300'),(25,'3.27160'),(100,'2.96200'),(250,'2.81520')],'D: SOIC8',
    note='Reopened primary page today: 8371 distributor pieces, not the older cached zero-stock search.')
add('ISO7761FDWR','texas-instruments/ISO7761FDWR/8322808','Texas Instruments',1809,
    [(1,'4.29000'),(10,'3.24600'),(25,'2.98600'),(100,'2.69950'),(250,'2.56292'),(500,'2.55458')],'DW: SOIC16 / 7.5mm body')
add('TCA9517ADGKR','texas-instruments/TCA9517ADGKR/4162317','Texas Instruments',24420,
    [(1,'1.22000'),(10,'0.88300'),(25,'0.79800'),(100,'0.70500'),(250,'0.66060'),(500,'0.63898'),(1000,'0.60282')],'DGK: VSSOP8')
add('ADS1115IDGSR','texas-instruments/ADS1115IDGSR/2231567','Texas Instruments',40653,
    [(1,'5.28000'),(10,'4.02300'),(25,'3.71000'),(100,'3.36560'),(250,'3.21760')],'DGS: VSSOP10')

add('TMR 4-2412WI','traco-power/TMR-4-2412WI/13402381','Traco Power',151,
    [(1,'17.51000'),(5,'16.86400'),(10,'16.59000'),(30,'16.16567'),(50,'15.97160'),(100,'15.71170'),(250,'15.37420'),(500,'15.12344')],'SIP8 / seven physical leads','Tube',
    note='Reopened primary US/USD catalogue before ledger issue; older cached16.20 price and154 stock were excluded. Manufacturer1600VDC functional isolation is controlling; distributor1.92kV field is not design qualification.')
for mpn,slug,stock in [('TMR 4-2413WI','TMR-4-2413WI/13402397',11),('TMR 4-2415WI','TMR-4-2415WI/13402390',20)]:
    add(mpn,'traco-power/'+slug,'Traco Power',stock,
        [(1,'16.20000'),(5,'15.59800'),(10,'15.34400'),(30,'14.95167'),(50,'14.77200'),(100,'14.53180'),(250,'14.21956'),(500,'13.98760')],'SIP8 / seven physical leads','Tube')
add('TPS7A2650DRVR','texas-instruments/TPS7A2650DRVR/10715893','Texas Instruments',4715,
    [(1,'1.16000'),(10,'0.84200'),(25,'0.76080'),(100,'0.67190'),(250,'0.62948'),(500,'0.60390'),(1000,'0.59058')],'DRV: WSON6 /2x2mm +EP7',
    note='Use source primary590mV maximum dropout at500mA, not distributor0.33V attribute as a guarantee. Exact fixed5V part.')
add('TPS3702CX50DDCR','texas-instruments/TPS3702CX50DDCR/5226750','Texas Instruments',5827,
    [(1,'2.66000'),(10,'1.97800'),(25,'1.80800'),(100,'1.62140'),(250,'1.53228'),(500,'1.49634')],'DDC: SOT23-6thin',
    note='ExactCX50 SET HIGH factory4.80/5.20V thresholds; siblingCX33 andQ1 suffix not priced as substitutions.')

path=HERE/'CATALOGUE_OBSERVATIONS-v3.json'
if path.exists():raise SystemExit('Refusing to replace issued ledger; archive another version')
path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(len(data['offers']),'exact PCB part offers;',len(data['module_offers']),'module offers')
