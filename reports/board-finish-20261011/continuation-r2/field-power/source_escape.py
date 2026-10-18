"""Global continuous source-escape width screen with immutable barrier rules."""
import json,pickle,hashlib,re,time
from collections import defaultdict
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.prepared import prep
from contact_layout import HERE,BASE,load,build,norm,poly
from power_groups import N,ROOTS
from inventory import sha
OUT=HERE/'source-escape-r1.json'
def main():
 if OUT.exists():raise ValueError('Refuse prior continuous screen')
 g,b=load();bd=json.loads((HERE/'power-groups-r1-binding.json').read_text(encoding='utf-8'));raw=(HERE/'power-groups-r1.pkl').read_bytes();assert hashlib.sha256(raw).hexdigest()==bd['cache_sha256'];groups=pickle.loads(raw);gr=json.loads((HERE/'power-groups-r1.json').read_text(encoding='utf-8'));rec,trees=build(g);reserv=json.loads((BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));dru=(BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text(encoding='utf-8');ex={}
 for ln in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',ln.strip())
  if m:ex[m[1]]={norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 outline=unary_union(poly(g['outline']));out={'board_sha256':g['sha256'],'native_jobs':0,'board_written':False,'fixed_static_copper_preserved':True,'original_native_barriers_preserved':True,'rows':[],'scope':'Global continuous free-space connectivity at given copper width, with fill retreat pending. This does not itself qualify old-source necks or silicon/copper transient limits.'};caches={}
 for bank in ['FBG','FAG']:
  net=N[bank];domain=g['domains_normalized'][net];ri=gr['nets'][bank]['source_root_group'];root=groups[bank][ri];goals={i:xs for i,xs in enumerate(groups[bank]) if i!=ri and any(r['kind']=='pad' for r in xs)}
  for layer in ['In1.Cu','In4.Cu','In2.Cu','In3.Cu','F.Cu','B.Cu']:
   obs=[]
   for r in rec[layer]:
    if norm(r['net'])==net or r['kind']=='fill':continue
    obs.append(r['shape'].buffer((.15 if r['domain']==domain else .6)+.03))
   for p in g['pads']:
    if norm(p['net'])!=net:obs.extend(q.buffer(.25+.025) for q in poly(p.get('hole') or []))
   for v in g['vias']:
    if norm(v['net'])!=net:obs.append(Point(v['x'],v['y']).buffer(v['drill']/2+.25+.025))
   for a in g['rule_areas']:
    if (a.get('no_tracks') or a.get('no_zones')) and layer in a['layers']:obs.extend(q.buffer(.025) for q in poly(a['outline']))
   for a in reserv['keepouts']:
    if net not in ex.get(a['name'],set()) and layer in a['layers']:obs.extend(q.buffer(.025) for q in poly(a['outline']))
   blocked=unary_union(obs);rootshape=unary_union([r['shape'] for r in root if r['layer']==layer]);goalshapes={i:unary_union([r['shape'] for r in xs if r['layer']==layer]) for i,xs in goals.items()};rows=[]
   for w in [7.2,5.5,4.4,3.2,2.,1.,.5,.35]:
    fr=outline.buffer(-.5-w/2-.025).difference(blocked.buffer(w/2));pieces=[fr] if fr.geom_type=='Polygon' else list(fr.geoms);rootpieces=[p for p in pieces if p.intersection(rootshape).area>1e-8];reach=unary_union(rootpieces);joined=[i for i,sh in goalshapes.items() if not sh.is_empty and reach.intersection(sh).area>1e-8]
    rows.append({'width_mm':w,'root_reachable_center_area_mm2':reach.area,'root_piece_count':len(rootpieces),'root_piece_bounds_mm':[p.bounds for p in rootpieces],'globally_reachable_original_pad_groups':joined})
    if w in [.35,2.,4.4,7.2]:caches[(bank,layer,w)]=fr
   out['rows'].append({'bank':bank,'layer':layer,'source_root':list(ROOTS[bank]),'source_group':ri,'screens':rows});print(bank,layer,[(r['width_mm'],len(r['globally_reachable_original_pad_groups'])) for r in rows],flush=True);(HERE/'source-escape-checkpoint.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8')
 OUT.write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8');data=pickle.dumps(caches,protocol=5);(HERE/'source-escape-r1.pkl').write_bytes(data);(HERE/'source-escape-r1-binding.json').write_text(json.dumps({'cache_sha256':hashlib.sha256(data).hexdigest(),'receipt_sha256':sha(OUT),'board_sha256':g['sha256']},indent=1)+'\n',encoding='utf-8')
if __name__=='__main__':main()
