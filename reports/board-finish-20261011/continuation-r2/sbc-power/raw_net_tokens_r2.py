"""Exact raw board net-token registry for isolated candidate serialization."""
import re,json,hashlib
from pathlib import Path
import layout_r1 as L

def registry():
    path=L.live.COMBINED
    data=path.read_bytes();text=data.decode('utf-8')
    names=set(json.loads('"'+m+'"') for m in re.findall(r'\(net\s+"((?:[^"\\]|\\.)*)"\)',text))
    by_normalized={}
    for raw in sorted(names):by_normalized.setdefault(L.p.norm(raw),[]).append(raw)
    collisions={key:value for key,value in by_normalized.items() if len(value)>1}
    if collisions:raise ValueError({'source_normalization_collision':collisions})
    return {key:values[0] for key,values in by_normalized.items()},hashlib.sha256(data).hexdigest()

def raw(normalized):
    names,_=registry()
    return names[L.p.norm(normalized)]

if __name__=='__main__':
    names,sha=registry()
    result={'source_board_sha256':sha,'raw_name_count':len(names),'normalization_collisions':[],
            'required_serialization_tokens':{n:names[L.p.norm(n)] for n in
            (L.stage.caps.CORE,'/IO_3V3','/LOGIC_GND',L.p.NET,
             L.stage.CT,'/motherboard_power_entry/SBC_SWITCH_PG')},
            'all_new_pads_tracks_vias_zones_must_use_exact_source_raw_tokens':True,
            'candidate_reparse_collision_and_exact_token_membership_gate_required':True}
    (L.OUT/'raw-net-token-binding-r2.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
