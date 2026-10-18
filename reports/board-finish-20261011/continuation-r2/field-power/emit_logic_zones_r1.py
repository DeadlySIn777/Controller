"""Exact canonical unfilled KiCad zone chunks; preserves explicit holes."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,uuid
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Polygon
from inventory import sha
from verify_source import parse,children,child,atom
import contact_layout as C
HERE=Path(__file__).resolve().parent;OUT=HERE/'logic-return-native-chunks-r1'
PRIMARY='https://raw.githubusercontent.com/KiCad/kicad-source-mirror/master/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp'
def ring(r):return '\t\t(polygon\n\t\t\t(pts\n'+''.join('\t\t\t\t(xy %.6f %.6f)\n'%(x,y) for x,y in list(r.coords)[:-1])+'\t\t\t)\n\t\t)\n'
def render(uid,net,layer,poly):
    return '\t(zone\n\t\t(net '+json.dumps(net)+')\n\t\t(layer '+json.dumps(layer)+')\n\t\t(uuid '+json.dumps(uid)+')\n\t\t(name '+json.dumps('Retained LOGIC_GND return repair '+uid)+')\n\t\t(hatch edge 0.5)\n\t\t(priority 20)\n\t\t(connect_pads yes\n\t\t\t(clearance 0.15)\n\t\t)\n\t\t(min_thickness 0.15)\n\t\t(fill\n\t\t\t(thermal_gap 0.15)\n\t\t\t(thermal_bridge_width 0.3)\n\t\t\t(island_removal_mode 1)\n\t\t)\n'+ring(poly.exterior)+''.join(ring(r) for r in poly.interiors)+'\t)\n'
def main():
    assert not OUT.exists();OUT.mkdir();rp=HERE/'logic-return-repair-r2/receipt.json';assert sha(rp)=='a8ea7e711121c83b3286a7965b26b4c5b1c1a92c939bd1c008e5ee2607f0b348';r=json.loads(rp.read_text());rows=[]
    for rr in r['rows']:
        q=rr['repair']
        if not q:continue
        p=Path(q['geometry_file']);assert sha(p)==q['sha256'];shape=from_wkb(p.read_bytes());assert set_precision(shape,1e-6).equals(shape);parts=[shape] if shape.geom_type=='Polygon' else list(shape.geoms)
        for i,part in enumerate(parts):
            uid=q['uuid'] if len(parts)==1 else str(uuid.uuid5(uuid.UUID(q['uuid']),'outer-part-'+str(i)));text=render(uid,q['net_raw'],q['layer'],part);file=OUT/(uid+'.zone-chunk');file.write_text(text,encoding='utf-8',newline='\n');ast=parse(text);assert ast[0]=='zone' and atom(ast,'uuid')==uid and atom(ast,'net')==q['net_raw'] and atom(ast,'layer')==q['layer'];rings=[[(float(x[1]),float(x[2])) for x in child(pp,'pts')[1:]] for pp in children(ast,'polygon')];rebuilt=Polygon(rings[0],rings[1:]);assert rebuilt.is_valid and rebuilt.symmetric_difference(part).area<1e-10;assert not children(ast,'filled_polygon') and not children(ast,'fill_segments');assert C.O.C.pcbtext.chunk_kind(text.encode())=='zone' and C.O.C.pcbtext.chunk_uuid(text.encode())==uid
            rows.append({'uuid':uid,'proposal_uuid':q['uuid'],'group':q['group'],'source_return_branch':q['source_external_return_repair'],'net_raw':q['net_raw'],'layer':q['layer'],'geometry_file':q['geometry_file'],'geometry_sha256':q['sha256'],'part_index':i,'outline_corners':len(rings[0]),'hole_count':len(rings)-1,'area_mm2':part.area,'chunk_file':str(file.resolve()),'chunk_sha256':sha(file),'exact_hole_semantics':'FIRST_POLYGON_OUTER; subsequent polygon records are holes, per primary KiCad parser','host_AST_roundtrip_exact':True,'native_load_and_refill_verified':False})
    receipt={'verdict':'EXACT_HOST_CHUNKS_READY_FOR_ROOT_REVIEW','proposal_receipt_sha256':sha(rp),'rows':rows,'native_parser_primary_source':PRIMARY,'native_parser_relevant_symbol':'PCB_IO_KICAD_SEXPR_PARSER::parseZONE, T_polygon, first outer/subsequent holes; T_connect_pads yes maps FULL','priority':20,'local_clearance_mm':.15,'cross_domain_frozen_rule_clearance_mm':.6,'pad_connection':'FULL_SOLID; footprint/pad overrides remain native validation obligations','min_thickness_mm':.15,'all_existing_zone_outlines_settings_and_UUIDs_preserved':True,'native_filled_cache_children_emitted':False,'raw_name_aliases_introduced':False,'native_jobs':0,'board_written':False,'current_thermal_and_all_old_contact_gates_open':True};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps({'chunks':len(rows),'holes':sum(q['hole_count'] for q in rows),'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
