"""Construct the main A return on exact source-connected continuous free space."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,hashlib
import shapely
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from contact_layout import HERE,BASE,load,build,poly,norm,identity,O,contacts
from power_groups import N,ROOTS
from inventory import sha
from tri_route import route
OUT=HERE/'triangulated-return-r1'

def main():
 if OUT.exists():raise ValueError('Frozen return proposal exists')
 OUT.mkdir();g,b=load();rec,trees=build(g,layers={'In1.Cu','In2.Cu','In4.Cu'})
 prior=pickle.loads((HERE/'variable-return-r2/prospective-copper.pkl').read_bytes())
 for q in prior:rec[q['layer']].append(q)
 trees={l:O.STRtree([r['shape'] for r in rs]) for l,rs in rec.items()}
 groups=pickle.loads((HERE/'power-groups-r1.pkl').read_bytes());net=N['FAG'];dom=g['domains_normalized'][net];pad=next(p for p in g['pads'] if (p['ref'],p['num'])==ROOTS['FAG']);goal=groups['FAG'][38];outline=unary_union(poly(g['outline']));res=json.loads((BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));rows=[];adds=[]
 for layer in ['In1.Cu','In4.Cu','In2.Cu']:
  fp=HERE/'return-obstruction-r1'/(layer+'-2.0.free.wkb')
  if not fp.exists():raise ValueError('Continuous source-component proof missing '+str(fp))
  free=shapely.from_wkb(fp.read_bytes());source=unary_union(poly(pad['layers'][layer])).intersection(free).buffer(-.01);target=unary_union([r['shape'] for r in goal if r['layer']==layer]).intersection(free).buffer(-.01);assert not source.is_empty and not target.is_empty
  a,bb=nearest_points(source,target);pts,search=route(free,tuple(a.coords[0]),tuple(bb.coords[0]));line=LineString(pts);win=line.envelope.buffer(4.5).envelope;obs=[]
  for i in trees[layer].query(win,predicate='intersects'):
   r=rec[layer][i]
   if norm(r['net'])==net or r['kind']=='fill':continue
   obs.append(r['shape'].buffer((.15 if r['domain']==dom else .6)+.03))
  for p in g['pads']:
   if norm(p['net'])!=net:obs.extend(q.buffer(.275) for q in poly(p.get('hole') or []) if q.intersects(win))
  for v in g['vias']:
   if norm(v['net'])!=net and win.covers(Point(v['x'],v['y'])):obs.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275))
  for a in g['rule_areas']:
   if a.get('no_zones') and layer in a['layers']:obs.extend(q.buffer(.025) for q in poly(a['outline']) if q.intersects(win))
  legal=win.intersection(outline.buffer(-.526)).difference(unary_union(obs));core=line.buffer(1.,quad_segs=32);cu=line.buffer(3.6,quad_segs=32).intersection(legal);parts=[cu] if cu.geom_type=='Polygon' else list(cu.geoms);cu=unary_union([q for q in parts if q.intersection(core).area>1e-8]);assert cu.buffer(.000003).covers(core)
  hits=contacts(rec,trees,cu,layer);assert not [x for x in hits if norm(x['net'])!=net and x['kind']!='fill'];retreats=[]
  for i in trees[layer].query(cu.buffer(.65),predicate='intersects'):
   r=rec[layer][i]
   if r['kind']=='fill' and norm(r['net'])!=net:
    gap=.15 if r['domain']==dom else .6;area=cu.buffer(gap+.025).intersection(r['shape']).area
    if area>1e-8:retreats.append(identity(r)|{'required_retreat_area_mm2':area,'clearance_mm':gap})
  crossings=[]
  for a in res['keepouts']:
   if layer not in a['layers']:continue
   area=cu.intersection(unary_union(poly(a['outline']))).area
   if area<=1e-8:continue
   actual=next((q for q in g['rule_areas'] if q['name']==a['name']),None);assert not a.get('no_zones') and not (actual and actual.get('no_zones'))
   crossings.append({'name':a['name'],'intersection_area_mm2':area,'native_no_zones':actual.get('no_zones') if actual else None,'frozen_reservation_disallows':'track via only','new_type':'copper zone','rule_not_modified':True})
  p=OUT/('FAG-'+layer+'.wkb');p.write_bytes(cu.wkb);row={'bank':'FAG','raw_native_net':pad['net'],'source_PTH':list(ROOTS['FAG']),'target_original_group':38,'target4A_terminal_group':['JD09.A9','JD09.A10','JD09.A11','JD09.A12'],'layer':layer,'verdict':'HOST_EXACT_CONSTRUCTIVE_MAIN_A_RETURN','path_points_mm':pts,'length_mm':line.length,'path_method':search,'core_width_mm':2.,'maximum_expansion_width_mm':7.2,'core_polygon_exactly_covered':True,'area_mm2':cu.area,'holes':sum(len(q.interiors) for q in ([cu] if cu.geom_type=='Polygon' else list(cu.geoms))),'own_contacts':[x for x in hits if norm(x['net'])==net],'mandatory_foreign_fill_retreat':retreats,'reserved_area_crossings':crossings,'continuous_free_component':{'path':str(fp.resolve()),'sha256':sha(fp)},'copper_file':str(p.resolve()),'copper_sha256':sha(p),'uniform_2mm_core60C_path_resistance_mohm_bound':.57003672*line.length/2,'no_barrel_source_plane_or_thermal_rating_inferred':True}
  rows.append(row);adds.append({'shape':cu,'net':pad['net'],'domain':dom,'layer':layer,'kind':'prospective_copper','uuid':'NEW_RETURN_FAG_MAIN_'+layer});print(layer,row['length_mm'],len(pts),len(crossings),flush=True);(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
 data=pickle.dumps(adds,protocol=5);(OUT/'prospective-copper.pkl').write_bytes(data);receipt={'original_board_sha256':g['sha256'],'prior_bridge_receipt_sha256':sha(HERE/'variable-return-r2/receipt.json'),'rows':rows,'cache_sha256':hashlib.sha256(data).hexdigest(),'source_rooted_actual_4A_A_output_return_3layers':True,'new_holes':0,'native_jobs':0,'board_written':False,'full_current_sharing_and_foreign_reference_and_native_refill_pending':True};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()
