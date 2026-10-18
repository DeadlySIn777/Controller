"""Create the bounded oscillator assignment proposal; no CAD generation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TARGET = ROOT/'hardware/motion_card/oscillator-footprint-promotion.json'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    if TARGET.exists():
        raise RuntimeError('Preserve existing promotion ledger')
    current = OUT/'sources/ase-current-20260930.pdf'
    request = urllib.request.Request('https://abracon.com/Oscillators/ASEseries.pdf',
                                     headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
    assert payload.startswith(b'%PDF')
    current.write_bytes(payload)
    assert sha(current) == sha(ROOT/'research/fpga-core/ase.pdf')
    review = json.loads((OUT/'review.json').read_text())
    source_paths = [ROOT/'research/fpga-core/ase.pdf',current,OUT/'review.json',
                    OUT/'sources/Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm.kicad_mod']
    ledger = {
        'schema_version':1,'promotion_id':'MC-OSC-001-prototype-candidate',
        'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Parent motion card source assignment only; historical fpga_core retained',
        'source_block':'fpga_core','source_reference':'Y1','parent_reference':'Y1001',
        'mpn':'ASE-50.000MHZ-L-C-T',
        'inherited_footprint':'',
        'footprint':'Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',
        'footprint_status':'manufacturer_land_dimensions_and_pin_mapping_candidate_not_process_qualified',
        'expected_source_pins':{'1':'IO_3V3','2':'LOGIC_GND','3':'FPGA_CLK_SOURCE','4':'IO_3V3'},
        'manufacturer_pin_functions':{'1':'Tri-State STBY','2':'GND/Case','3':'Output','4':'VDD'},
        'manufacturer_source_url':'https://abracon.com/Oscillators/ASEseries.pdf',
        'manufacturer_revision':'2022-02-18',
        'mechanical_source_page_1_based':5,'ordering_options_source_page_1_based':3,
        'exact_ordering_options':{'frequency_hz':50000000,'temperature_code':'L',
            'temperature_celsius':[-40,85],'stability_code':'C',
            'frequency_stability_ppm':50,'packaging_code':'T','reel_pieces':1000},
        'body_nominal_xy_mm':[3.2,2.5],'body_maximum_xy_mm':[3.4,2.7],
        'height_maximum_mm':1.2,'pin1_top_view':'lower_left',
        'land_dimensions_mm':[1.3,1.1],'land_center_spacing_xy_mm':[2.1,1.65],
        'native_pad_geometry':review['pads'],
        'native_courtyard_bounds_mm':review['courtyard_bounds_mm'],
        'native_stock_footprint_sha256':review['stock_footprint_sha256'],
        'land_shape_difference':{
            'manufacturer_recommended_drawing':'rectangular copper lands',
            'native_stock_shape':'roundrect',
            'native_radius_mm':review['pads']['1']['roundrect_radius_mm'],
            'stock_area_reduction_percent':review['stock_area_reduction_percent'],
            'disposition':'Dimensional/pin assignment candidate; corner, mask and paste acceptance remains unqualified'},
        'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in source_paths},
        'historical_child_sources_unchanged':True,
        'electrical_pin_or_net_changes':False,'pcb_pad_or_copper_changes':False,
        'manufacturing_ready':False,'physical_qualification':False,'assembly_process_qualified':False,
        'qualification_open':review['qualification_open'],
    }
    TARGET.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ledger':TARGET.relative_to(ROOT).as_posix(),
                      'download_matches_retained_pdf':True,'manufacturing_ready':False}))


if __name__ == '__main__':main()
