"""Read-only layout/net census for the frozen field candidate."""
import json,re
from collections import defaultdict
from contact_layout import load,build,norm,poly,O,S,BOARD,HERE,identity
from shapely.geometry import box
from shapely.ops import unary_union

g,b=load();r,t=build(g);raw=defaultdict(set)
for n in re.findall(r'\(net "([^"]*)"\)',BOARD.read_text(encoding='utf-8')):raw[norm(n)].add(n)
collisions={n:sorted(v) for n,v in raw.items() if len(v)>1}
audit=[]
for p in (HERE/'board-delta-r2').glob('*.footprint-chunk'):
 for n in re.findall(r'\(net "([^"]*)"\)',p.read_text(encoding='utf-8')):
  k=norm(n);audit.append({'chunk':p.name,'raw':n,'canonical':k,'exact_existing_raw':n in raw.get(k,set()),'new_allowed':k=='DOB_DO_FIELD_3V3' or k.startswith('unconnected-(U11038-')})
wrong=[x for x in audit if not x['exact_existing_raw'] and not x['new_allowed']]
nets=['/motherboard_safety_sensor/FIELD_B_5V_PRE','/motherboard_do/FIELD_B_0V','/motherboard_power_entry/FB_PGOOD','/motherboard_do/DOB_FIELD_3V3']
out={'raw_name_collisions':collisions,'wrong_serialized_raw':wrong,'audited_pad_count':len(audit),'nets':{}}
for net in nets:
 out['nets'][net]={'raw':sorted(raw[net]),'pads':[{k:p[k] for k in ['ref','num','uuid','x','y']}|{'layers':list(p['layers'])} for p in g['pads'] if norm(p['net'])==net],
  'fills':{l:sum(x['shape'].area for x in rows if norm(x['net'])==net and x['kind']=='fill') for l,rows in r.items()},
  'zones':[{k:z[k] for k in ['uuid','net','layers']} for z in g['zones'] if norm(z['net'])==net]}
win=box(121,130,137,149);out['U11018_window']={l:[identity(x) for x in rows if x['shape'].intersects(win) and x['kind']!='fill'] for l,rows in r.items()};out['U11018_courts']=[{'ref':f['ref'],'pose':[f['x'],f['y']],'side':f['side']} for f in g['footprints'] if any(q.intersects(win) for ps in f['courtyard'].values() for q in poly(ps))]
(HERE/'layout-diag-r1.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8')
print(json.dumps({'collisions':len(collisions),'bad_raw_names':wrong,'pads_audited':len(audit),'net_pads':{n:len(v['pads']) for n,v in out['nets'].items()},'fill_area':{n:v['fills'] for n,v in out['nets'].items()},'U18_courts':out['U11018_courts']}))
