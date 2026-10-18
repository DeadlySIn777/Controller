"""Record manually reviewed primary catalogue observations, without supplier contact.

Public pages were read through the web tool on 2026-09-30. Returned catalogue
content can be cached; observed stock is not a fresh inventory reservation.
No third-party price aggregator or substitute-part price enters selected offers.
"""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
offers = []


def add(mpn, slug, manufacturer, stock, ladder, package, supplier="DigiKey", source_url=None,
        cache="Returned cached catalogue page, reviewed 2026-09-30; not reserved"):
    offers.append(dict(mpn=mpn, manufacturer=manufacturer, supplier=supplier, currency="USD",
        source_url=source_url or f"https://www.digikey.com/en/products/detail/{slug}",
        observed_date="2026-09-30", source_cache_note=cache,
        packaging="Cut Tape", minimum=1, multiple=1,
        price_breaks=[dict(minimum=int(n), unit_usd=u) for n,u in ladder],
        observed_stock_pieces=stock, supplier_package=package,
        price_kind="published_catalogue", availability_qualified=False,
        availability_note="Catalogue stock is dated, unreserved and not an assembly procurement commitment. Shipping, tariffs, tax and PCBWay handling not included."))


R0603 = [(1,"0.10000"),(10,"0.03200"),(25,"0.02400"),(50,"0.01940"),
         (100,"0.01590"),(250,"0.01244"),(500,"0.01048"),(1000,"0.00895")]
add("AM26C31IPWR","texas-instruments/AM26C31IPWR/1689912","Texas Instruments",2213,
    [(1,"1.24000"),(10,"0.89900"),(25,"0.81360"),(100,"0.71940"),(250,"0.67452"),(500,"0.64742"),(1000,"0.63495")],"PW: 16-TSSOP 4.4mm body")
add("AM26LV32EIPWR","texas-instruments/AM26LV32EIPWR/1896013","Texas Instruments",41379,
    [(1,"2.31000"),(10,"1.71100"),(25,"1.56160"),(100,"1.39670"),(250,"1.31812"),(500,"1.27908")],"PW: 16-TSSOP 4.4mm body")
add("ISO1212DBQR","texas-instruments/ISO1212DBQR/7931888","Texas Instruments",11985,
    [(1,"1.33000"),(10,"0.96300"),(25,"0.87160"),(100,"0.77170"),(250,"0.72408"),(500,"0.69532"),(1000,"0.68391")],"DBQ: 16-SSOP 3.9mm body")
add("SN74LVC07APWR","texas-instruments/SN74LVC07APWR/377393","Texas Instruments",0,
    [(1,"0.43000"),(10,"0.30000"),(25,"0.26720"),(100,"0.23130"),(250,"0.21424"),(500,"0.20398"),(1000,"0.19584")],"PW: 14-TSSOP 4.4mm body")
add("TPS22918DBVR","texas-instruments/TPS22918DBVR/5994601","Texas Instruments",0,
    [(1,"0.55000"),(10,"0.39000"),(25,"0.34920"),(100,"0.30380"),(250,"0.28224"),(500,"0.26920"),(1000,"0.25847")],"DBV: SOT-23-6")
add("SMBJ33CA-E3/52","vishay-general-semiconductor-diodes-division/SMBJ33CA-E3-52/1119279","Vishay",10573,
    [(1,"0.55000"),(10,"0.33600"),(50,"0.24300"),(100,"0.21290")],"DO-214AA / SMB")
add("CRCW0603220RFKEA","vishay-dale/CRCW0603220RFKEA/1174590","Vishay",57065,R0603,"0603 / 1608")
add("CRCW0603562RFKEA","vishay-dale/CRCW0603562RFKEA/1179781","Vishay",10992,R0603,"0603 / 1608")
add("CRCW0603820RFKEA","vishay-dale/CRCW0603820RFKEA/1174658","Vishay",2748,R0603,"0603 / 1608")
add("CRCW1210120RFKEA","vishay-dale/CRCW1210120RFKEA/3231976","Vishay",46510,
    [(1,"0.21000"),(10,"0.10400"),(25,"0.08240"),(50,"0.06980"),(100,"0.06020"),(250,"0.05040"),(500,"0.04478"),(1000,"0.04033")],"1210 / 3225")
add("C0603C152J5GACTU","kemet/C0603C152J5GACTU/2199972","KEMET",162699,
    [(1,"0.52000"),(10,"0.31100"),(50,"0.22940"),(100,"0.20430"),(500,"0.16190")],"0603 / 1608")
add("06033C104JAT2A",None,"KYOCERA AVX",5459,
    [(1,"0.23"),(10,"0.136"),(100,"0.082"),(500,"0.062"),(2000,"0.043")],"0603 / 1608",supplier="Mouser",
    source_url="https://www.mouser.com/en/ProductDetail/KYOCERA-AVX/06033C104JAT2A?qs=9m8RHjAONzC2EgWOJLFcaw%3D%3D")

# Exact added MPNs being evaluated by motor engineering. They only enter costing
# if the frozen motherboard BOM contains precisely these orderable strings.
add("SN74LVC1G74DCUR","texas-instruments/SN74LVC1G74DCUR/2195376","Texas Instruments",41447,
    [(1,"0.60000"),(10,"0.42200"),(25,"0.37840"),(100,"0.32980"),(250,"0.30676"),(500,"0.29284"),(1000,"0.28611")],"DCU: 8-VSSOP 2.3x2.0mm body")
add("74LVC07APW,118","nexperia-usa-inc/74LVC07APW-118/946747","Nexperia",0,
    [(1,"0.25000"),(10,"0.17100"),(25,"0.15160"),(100,"0.12990"),(250,"0.11948"),(500,"0.11322"),(1000,"0.10806")],"PW: TSSOP14 / SOT402-1")
add("74LVC14APW,118","nexperia-usa-inc/74LVC14APW-118/946731","Nexperia",51887,
    [(1,"0.23000"),(10,"0.15900"),(25,"0.14040"),(100,"0.12000"),(250,"0.11016"),(500,"0.10428"),(1000,"0.09942")],"PW: TSSOP14 / SOT402-1")
add("SN74LVC00APWR","texas-instruments/SN74LVC00APWR/276859","Texas Instruments",1292,
    [(1,"0.46000"),(10,"0.32400"),(25,"0.28920"),(100,"0.25050"),(250,"0.23212"),(500,"0.22104"),(1000,"0.21246")],"PW: 14-TSSOP 4.4mm body")
add("LTC6994IS6-2#TRPBF","analog-devices-inc/LTC6994IS6-2-TRPBF/2399245","Analog Devices",6,
    [(1,"6.28000"),(10,"4.81800"),(25,"4.45160"),(100,"4.04860"),(250,"3.85648"),(500,"3.82500")],"S6: TSOT-23-6")
add("74AHCT1G17GVH","nexperia-usa-inc/74AHCT1G17GVH/5035649","Nexperia",4810,
    [(1,"0.12000"),(10,"0.08100"),(25,"0.07080"),(100,"0.05960"),(250,"0.05432"),(500,"0.05114"),(1000,"0.04849")],"GV: TSOP5 / SOT753 / SC-74A")
add("CRCW0603330RFKEA","vishay-dale/CRCW0603330RFKEA/1179752","Vishay",42327,R0603,"0603 / 1608")

# These supplier strings differ from the inherited source's final ')' spelling.
# No automatic punctuation normalization or alternate-MPN pricing is allowed.
add("TLP3640A(TPL,E","toshiba-semiconductor-and-storage/TLP3640A-TPL-E/25697899","Toshiba",6785,
    [(1,"2.26000"),(10,"2.01300"),(25,"1.92240"),(50,"1.85660"),(100,"1.79310"),(250,"1.71228"),(500,"1.65354"),(1000,"1.59677")],"4-SO; Toshiba 11-3C1")
add("TLP4176A(TP,F","toshiba-semiconductor-and-storage/TLP4176A-TP-F/16678343","Toshiba",4358,
    [(1,"2.74000"),(10,"1.98200"),(100,"1.53170"),(500,"1.33372"),(1000,"1.26920")],"4-SOP; Toshiba 11-5H1S")

data = dict(schema_version=1, date="2026-09-30", currency="USD",
    method="Manual transcription of exact manufacturer-product-number, currency, package, cut-tape tiers and observed stock from primary distributor pages returned by web lookup. Not a live quotation or supplier contact.",
    offers=offers,
    excluded_reference_offers=[
        dict(mpn="C2012C0G2A103J125AA",supplier="DigiKey Canada",currency="CAD",stock=771,
             source_url="https://www.digikey.ca/en/products/detail/tdk/C2012C0G2A103J125AA/4278008",
             price_breaks=[dict(minimum=n,unit_cad=u) for n,u in [(1,"0.50000"),(10,"0.29000"),(50,"0.21100"),(100,"0.18720"),(500,"0.14658")]],
             excluded_reason="Exact part and 0805/100V/C0G package verified, but accessible primary page is CAD. USD conversion or another tolerance part's USD price is not applied."),
        dict(mpn="SMM02040C1001FB300",supplier="LCSC",currency="USD",stock=0,
             source_url="https://www.lcsc.com/product-image/C1884622.html",
             price_breaks=[dict(minimum=n,unit_usd=u) for n,u in [(20,"0.0377"),(200,"0.0297"),(600,"0.0253"),(3000,"0.0227"),(9000,"0.0204"),(21000,"0.0192")]],
             excluded_reason="Supplier labels all tiers reference-only with zero stock; purchasable package/multiple and firm price not verified. Exact MPN itself is documented in TI evaluation BOM."),
        dict(mpn="SMBJ33CA-E3/52",supplier="DigiKey",currency="USD",packaging="Full Reel",minimum=750,multiple=750,
             source_url="https://www.digikey.com/en/products/detail/vishay-general-semiconductor-diodes-division/SMBJ33CA-E3-52/1119279",
             price_breaks=[dict(minimum=750,unit_usd="0.14945"),dict(minimum=2250,unit_usd="0.12600")],
             excluded_reason="Retained cut-tape procurement scenario; a separately accepted full-reel purchase may reduce 100-board cost, but no reel-price credit is applied to cut-tape demand.")],
    observations_are_not_assembly_quotes=True, supplier_contact=False, orders=False)
path = HERE / "CATALOGUE_OBSERVATIONS.json"
if path.exists():
    raise SystemExit("Refusing to replace existing observation ledger; create a versioned receipt for later observations.")
path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
print(f"Recorded {len(offers)} exact-MPN offers and {len(data['excluded_reference_offers'])} excluded references")
