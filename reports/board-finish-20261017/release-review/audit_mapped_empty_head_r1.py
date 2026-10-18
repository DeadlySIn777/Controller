"""Evaluate the mapped LUT cone conservatively; does not modify native output."""
from pathlib import Path
import re,json,hashlib,itertools
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/board-finish-20261017'
mapped=BASE/'event-producer-fifo-r1/native-events-map/outflow/cnc3_runtime_events.map.v'
s=mapped.read_text()
norm=lambda v:re.sub(r'\s+','',v)
cells={}
params={norm(name):int(mask,16) for name,mask in re.findall(r'defparam\s+([^\r\n]+?)\.LUTMASK\s*=\s*16\x27h([0-9a-fA-F]+);',s)}
for match in re.finditer(r'EFX_LUT4\s+([^\r\n(]+?)\s*\((.*?)\)\s*(?:/\*.*?\*/)?\s*;',s,re.S):
    name,ports=match.groups()
    ports={p:norm(v) for p,v in re.findall(r'\.(\w+)\(([^()]*)\)',ports)}
    assert ports['O'] not in cells
    assert norm(name) in params,name
    cells[ports['O']]={'name':name.strip(),'inputs':[ports.get('I'+str(i),"1'b0") for i in range(4)],'mask':params[norm(name)]}
assert len(cells)>5000,len(cells)
known={f'count[{i}]':0 for i in range(9)}
known.update({"1'b0":0,"1'b1":1})
visiting=set()
def evaluate(net):
    if net in known:return known[net]
    if net not in cells:return None
    assert net not in visiting,net
    visiting.add(net)
    c=cells[net];v=[evaluate(x) for x in c['inputs']]
    visiting.remove(net)
    results={((c['mask']>>sum(b<<i for i,b in enumerate(bits)))&1)
             for bits in itertools.product(*[(0,1) if x is None else (x,) for x in v])}
    result=next(iter(results)) if len(results)==1 else None
    known[net]=result
    return result
bits={i:evaluate(f'event_head[{i}]') for i in range(160)}
selected={n:{**cells[n],'input_values':[evaluate(x) for x in cells[n]['inputs']],
    'value':evaluate(n)} for n in ['n5834','n5768','n5805','n5657','n5658','n5837','n6477','n6476','n5705','event_head[0]']}
out=BASE/'release-review/mapped-empty-head-r1';out.mkdir(exist_ok=False)
receipt={'status':'MAPPED_EMPTY_HEAD_CONSERVATIVE_LUT_CONE_ZERO' if all(v==0 for v in bits.values()) else 'MAPPED_EMPTY_HEAD_CONE_NOT_PROVED',
    'source':str(mapped),'SHA256':hashlib.sha256(mapped.read_bytes()).hexdigest(),
    'method':'Set only global count[8:0]=0; treat every other unmapped source, RAM bit, FF output, primary input as independent arbitrary binary. Evaluate each LUT over all possibilities per unknown input. No correlation assumptions; cannot falsely prove constant from lost correlation.',
    'parsed_LUTs':len(cells),'head_bits_zero':sum(v==0 for v in bits.values()),'head_bits_one':sum(v==1 for v in bits.values()),'head_bits_unknown':sum(v is None for v in bits.values()),
    'selected_cone':selected,'vendor_models_changed':False,'RTL_or_native_outputs_changed':False,
    'scope':'Combinational truth-table cone proof only; not mapped sequential equivalence, unknown/X initialization or timing qualification.'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='selected_cone'}))
