"""Read-only native/source check for the parent ASE oscillator assignment."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import shutil
import sys
import xml.etree.ElementTree as ET

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from hardware_build_assembly import parse, child, children, value

OUT = Path(__file__).resolve().parent
STOCK = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints/Oscillator.pretty/Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm.kicad_mod')
EXPECTED = {'1': [-1.05, 0.825], '2': [1.05, 0.825],
            '3': [1.05, -0.825], '4': [-1.05, -0.825]}
PINS = {'1':'IO_3V3', '2':'LOGIC_GND', '3':'FPGA_CLK_SOURCE', '4':'IO_3V3'}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def source_nodes(path, ref):
    result = {}
    for net in ET.parse(path).findall('.//nets/net'):
        for node in net.findall('node'):
            if node.attrib['ref'] == ref:
                result[node.attrib['pin']] = net.attrib['name']
    return result


def main():
    receipt_path = OUT/'review.json'
    if receipt_path.exists():
        raise RuntimeError('Preserve the existing independent receipt')
    protected = list((ROOT/'hardware/fpga_core').rglob('*'))
    protected = [p for p in protected if p.is_file() and '__pycache__' not in p.parts]
    protected += [ROOT/'reports/board-cad-20260930/SOURCE_REVIEW.md',
                  ROOT/'reports/board-completion-20260930/PACKAGE_GEOMETRY_CHECK.json']
    protected += list((ROOT/'hardware/board_review/revisions').glob('*/*.kicad_pcb'))
    before = {p.relative_to(ROOT).as_posix():sha(p) for p in protected}
    fp = pcbnew.FootprintLoad(str(STOCK.parent), STOCK.stem)
    pads = {}
    for pad in fp.Pads():
        pos, size = pad.GetPosition(), pad.GetSize()
        radius = pcbnew.ToMM(pad.GetRoundRectCornerRadius())
        width, height = pcbnew.ToMM(size.x), pcbnew.ToMM(size.y)
        pads[pad.GetNumber()] = {
            'x_mm':pcbnew.ToMM(pos.x), 'y_mm':pcbnew.ToMM(pos.y),
            'width_mm':width, 'height_mm':height,
            'shape':'roundrect' if pad.GetShape() == pcbnew.PAD_SHAPE_ROUNDRECT else str(pad.GetShape()),
            'roundrect_radius_mm':radius,
            'roundrect_area_mm2':width*height-(4-math.pi)*radius**2,
            'manufacturer_drawn_rectangular_area_mm2':width*height,
        }
    assert set(pads) == set(EXPECTED)
    for pin, xy in EXPECTED.items():
        assert [pads[pin]['x_mm'], pads[pin]['y_mm']] == xy
        assert [pads[pin]['width_mm'],pads[pin]['height_mm']] == [1.3,1.1]
        assert pads[pin]['shape'] == 'roundrect'
    tree = parse(STOCK.read_text(encoding='utf-8'))
    courtyard = next(p for p in children(tree,'fp_rect')
                     if value(child(p,'layer')[1]) == 'F.CrtYd')
    bounds = list(map(float,child(courtyard,'start')[1:3]+child(courtyard,'end')[1:3]))
    assert bounds == [-2.1,-1.75,2.1,1.75]
    assert bounds[0] <= -3.4/2 and bounds[1] <= -2.7/2
    assert bounds[2] >= 3.4/2 and bounds[3] >= 2.7/2
    model = json.loads((ROOT/'hardware/fpga_core/design.json').read_text())
    parent = json.loads((ROOT/'hardware/motion_card/design.json').read_text())
    assert model['components']['Y1']['mpn'] == 'ASE-50.000MHZ-L-C-T'
    assert model['components']['Y1']['pins'] == PINS
    assert model['components']['Y1']['footprint'] == ''
    assert parent['components']['Y1001']['pins'] == PINS
    child_nets = source_nodes(ROOT/'hardware/fpga_core/netlist.xml','Y1')
    parent_nets = source_nodes(ROOT/'hardware/motion_card/netlist.xml','Y1001')
    assert {k:v.split('/')[-1] for k,v in child_nets.items()} == PINS
    assert {k:v.split('/')[-1] for k,v in parent_nets.items()} == PINS
    symbol = parse((ROOT/'hardware/fpga_core/FPGA.kicad_sym').read_text())
    oscillator = next(s for s in children(symbol,'symbol') if value(s[1]) == 'ASE_50MHz')
    functions = {}
    for unit in children(oscillator,'symbol'):
        for pin in children(unit,'pin'):
            functions[value(child(pin,'number')[1])] = value(child(pin,'name')[1])
    assert functions == {'1':'STBY_N','2':'GND','3':'OUT','4':'VDD'}
    assert model['components']['C37']['placement_target'] == 'Y1'
    assert model['components']['C37']['capacitance_f'] == 1e-8
    assert set(model['components']['C37']['pins'].values()) == {'IO_3V3','LOGIC_GND'}
    snapshot = OUT/'sources'/STOCK.name
    shutil.copyfile(STOCK,snapshot)
    after = {p.relative_to(ROOT).as_posix():sha(p) for p in protected}
    assert before == after
    result = {
        'schema_version':1,'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'source_dimension_and_pin_mapping_candidate_not_process_qualified',
        'manufacturing_ready':False, 'physical_measurement':False,
        'native_pcb_drc_run':False, 'native_schematic_erc_run':False,
        'native_kicad_version':pcbnew.Version(),
        'stock_footprint_path':str(STOCK),'stock_footprint_sha256':sha(STOCK),
        'source_pdf_path':'research/fpga-core/ase.pdf',
        'source_pdf_sha256':sha(ROOT/'research/fpga-core/ase.pdf'),
        'source_image_visually_inspected':'research/fpga-core/ase-pins.png',
        'body_nominal_xy_mm':[3.2,2.5],'body_maximum_xy_mm':[3.4,2.7],
        'height_maximum_mm':1.2, 'pin1_top_view':'lower_left',
        'courtyard_bounds_mm':bounds,'max_body_inside_courtyard':True,
        'pads':pads,'source_native_symbol_pin_functions':functions,
        'source_native_nets':child_nets,'parent_native_nets_before_promotion':parent_nets,
        'bypass_source_ref':'C37','bypass_parent_ref':'C1037','bypass_nominal_f':1e-8,
        'source_recommended_rectangular_lands_stock_roundrect_difference':True,
        'stock_area_reduction_percent':100*(4-math.pi)*pads['1']['roundrect_radius_mm']**2/(1.3*1.1),
        'qualification_open':['Rounded copper/paste corner acceptance and final mask/stencil process',
            'Assembly placement/reflow/inspection qualification',
            'Clock route loading, bypass placement and physical timing',
            'Whole-board/cage collision and assembled fit'],
        'protected_inputs_before':before,'protected_inputs_after':after,
        'protected_inputs_unchanged':True,
    }
    receipt_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'checked_four_native_pads':True,'source_and_parent_pin_maps_match':True,
                      'protected_files_unchanged':len(before),
                      'roundrect_area_reduction_percent':result['stock_area_reduction_percent'],
                      'manufacturing_ready':False}))


if __name__ == '__main__':
    main()
