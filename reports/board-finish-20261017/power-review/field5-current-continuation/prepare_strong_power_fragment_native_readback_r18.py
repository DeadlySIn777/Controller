"""Native parser fixture for34 exact power tracks,2 FG source parts,original net."""
from pathlib import Path
import hashlib,importlib.util,json,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];FR=HERE/'strong-power-stage3-sparse-fragments-r17';OUT=HERE/'strong-power-native-readback-r18';hp=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sp=importlib.util.spec_from_file_location('pcbtext',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
def main():
    assert not OUT.exists();OUT.mkdir();m=json.loads((FR/'fragments-manifest.json').read_text());base=Path(m['parent_board']);assert sha(base)==m['parent_board_SHA256'];head,cc,tail=H.split(base.read_bytes());original_field=next(c for c in cc if H.chunk_kind(c)=='zone'and b'FIELD_5V"'in c and b'(layer "F.Cu")'in c);uid=H.chunk_uuid(original_field);chunks=[]
    for op in m['operations']:
        p=Path(op['after_file']);assert sha(p)==op['after_SHA256'];chunks.append(p.read_bytes())
    q=OUT/'minimal-power-fragment-readback.kicad_pcb';q.write_bytes(head+b''.join(c for c in cc if H.chunk_uuid(c)is None)+original_field+b''.join(chunks)+tail);d={'fixture':str(q),'fixture_SHA256':sha(q),'original_FIELD5_F_source_zone_UUID':uid,'original_FIELD5_zone_chunk_SHA256':hashlib.sha256(original_field).hexdigest(),'fragment_manifest':str(FR/'fragments-manifest.json'),'fragment_manifest_SHA256':sha(FR/'fragments-manifest.json'),'source_stage3':str(base),'source_stage3_SHA256':sha(base),'operations':m['operations'],'input_sha256':{str(hp):sha(hp),str(Path(__file__)):sha(Path(__file__))},'full_coupled_board':False,'native_fill_called':False,'adopted':False};(OUT/'input.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'fixture':str(q),'operations':len(chunks)}))
if __name__=='__main__':main()
