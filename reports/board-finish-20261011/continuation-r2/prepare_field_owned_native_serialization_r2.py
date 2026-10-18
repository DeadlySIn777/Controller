"""Normalize only new local segments into the frozen native text grammar."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    original=HERE/'compose_field_owned_host_r1.py';derived=HERE/'compose_field_owned_host_r2.py'
    if derived.exists():raise ValueError('Fresh field serializer required')
    raw=original.read_text(encoding='utf-8').replace("OUT=HERE/'combined-owned-host-r1'","OUT=HERE/'combined-owned-host-r2'")
    helper='''
def native_new_segment(row):
    raw=chunk(row)
    number=rb'([-+0-9.eE]+)'
    expression=rb'\\s*\\(segment\\s+\\(start\\s+'+number+rb'\\s+'+number+rb'\\)\\s+\\(end\\s+'+number+rb'\\s+'+number+rb'\\)\\s+\\(width\\s+'+number+rb'\\)\\s+\\(layer\\s+"([^"\\n]+)"\\)\\s+\\(net\\s+"([^"\\n]+)"\\)\\s+\\(uuid\\s+"([^"\\n]+)"\\)\\)\\s*'
    match=re.fullmatch(expression,raw)
    if not match:raise ValueError('New segment has unknown or repeated native attributes')
    x1,y1,x2,y2,width,layer,net,uid=match.groups()
    if [float(x1),float(y1)]!=row['from_mm'] or [float(x2),float(y2)]!=row['to_mm'] or float(width)!=row['width_mm'] or net.decode()!=row['net_raw'] or uid.decode()!=row['uuid']:raise ValueError('Exact new segment metadata differs')
    canonical=(b'\\t(segment\\n\\t\\t(start '+x1+b' '+y1+b')\\n\\t\\t(end '+x2+b' '+y2+b')\\n\\t\\t(width '+width+b')\\n\\t\\t(layer "'+layer+b'")\\n\\t\\t(net "'+net+b'")\\n\\t\\t(uuid "'+uid+b'")\\n\\t)\\n')
    SERIALIZATION.append({'uuid':row['uuid'],'original_raw_sha256':sha(raw),'canonical_native_sha256':sha(canonical),'all_native_atoms_preserved':True})
    return canonical
'''
    raw=raw.replace("PINS={}","PINS={};SERIALIZATION=[]")
    mark="def write(name,data):"
    raw=raw.replace(mark,helper+'\n'+mark)
    old="for row in r['new_local_segment_additions']:\n        u=row['uuid'];ch=chunk(row)"
    if raw.count(old)!=1:raise ValueError('One exact new-only segment loop expected')
    raw=raw.replace(old,"for row in r['new_local_segment_additions']:\n        u=row['uuid'];ch=native_new_segment(row)")
    raw=raw.replace("'input_hashes':PINS,'adopted':False","'new_segment_native_serialization':SERIALIZATION,'input_hashes':PINS,'adopted':False")
    derived.write_text(raw,encoding='utf-8');(HERE/'field-owned-native-serialization-derivation-r2.json').write_text(json.dumps({'original':str(original),'original_sha256':sha(original),'derived':str(derived),'derived_sha256':sha(derived),'changes':['Render only37 new segment chunks into frozen native multiline grammar','Full-match six original attribute atoms and exact recipe metadata before canonicalization','All old footprint/retag/trim/delete operations and proof gates unchanged'],'old_board_bytes_changed':False,'adopted':False},indent=1)+'\n',encoding='utf-8');print(str(derived),flush=True)
if __name__=='__main__':main()
