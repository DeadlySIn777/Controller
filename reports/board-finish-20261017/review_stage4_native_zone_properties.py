"""Bind native AFTER-input contour receipt properties to exact source tokens."""
import hashlib
import importlib.util
import json
from pathlib import Path
from fractions import Fraction
import sys
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
WORK=H/'combined-route-stage-r4'
OUT=WORK/'native-zone-property-review'


def sha(p):
    with Path(p).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()


def mod(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
    assert not OUT.exists()
    board=WORK/'native/board.kicad_pcb';receipt=WORK/'native-input-check/receipt.json'
    r=json.loads(receipt.read_bytes())
    assert sha(board)==r['board_SHA256']=='ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55'
    assert r['native_top_level_zones_and_rule_areas']==857 and not r['exact_integer_Cu_errors']
    assert all(sha(p)==v for p,v in r['input_SHA256'].items())
    helper=H.parent/'board-finish-20261011/parity-repair/root106/tools/pcbtext.py'
    C=mod('source_zone_properties',helper);Z=mod('zone_profile_tokens',H/'zone_profile_guard_r1.py')
    chunks={C.chunk_uuid(c):c for c in C.split(board.read_bytes())[1] if C.chunk_kind(c)=='zone'}
    checked=[]
    for row in r['all14_changed_or_new_zones_exact_native_contours_and_hole_ownership']:
        attrs={a[0]:a[1:] for a in Z.tree(chunks[row['UUID']])[1:] if isinstance(a,list)}
        text=lambda key:json.loads(attrs[key][0])
        native_iu=lambda token:int(Fraction(token.decode())*1000000)
        assert row['actual_raw_net']==text(b'net')
        assert row['layer']==text(b'layer')
        assert row['name']==text(b'name')
        assert row['minimum_thickness_IU']==native_iu(attrs[b'min_thickness'][0])
        clearance=next(a[1] for a in attrs[b'connect_pads'] if isinstance(a,list) and a[0]==b'clearance')
        assert row['local_clearance_IU']==native_iu(clearance)
        assert row['priority']==int(attrs.get(b'priority',[b'0'])[0])
        checked.append({'UUID':row['UUID'],'net_layer_name_clearance_minwidth_priority_native_source_exact':True,'native_holes':row['hole_count']})
    assert len(checked)==14
    record={'status':'ALL14_NATIVE_ZONE_SOURCE_PROPERTIES_AND_CONTOURS_BOUND_PASS_INPUT_SCOPE_ONLY',
        'board_SHA256':sha(board),'checked':checked,'input_SHA256':{str(p):sha(p) for p in [Path(__file__),helper,H/'zone_profile_guard_r1.py',board,receipt]},
        'full_fill_DRC_joins_current_source_reference_SI':'OPEN_UNEXECUTED_FOR_STAGE4','adopted':False,'manufacturing_ready':False}
    OUT.mkdir();(OUT/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'status':record['status'],'zones':len(checked)}))


if __name__=='__main__':main()
