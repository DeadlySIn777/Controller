"""Concrete small bypass placement after existing-cap local-loop screen."""
import json,copy,pickle,hashlib,math,time
from shapely.geometry import Point,LineString,box
from shapely import affinity
from shapely.ops import unary_union
from shapely.strtree import STRtree
from contact_layout import HERE,BASE,load,build,norm,poly,S,identity,footprint_shape
from inventory import sha,load as source_load
OUT=HERE/'new-local-bypass-r1.json'
B5='/motherboard_safety_sensor/FIELD_B_5V_PRE';GND='/motherboard_do/FIELD_B_0V'
def main():
 if OUT.exists():raise ValueError('Refuse prior bypass screen')
 g,b=load();binding=json.loads((HERE/'owned-pad-cuts-r1/geometry-binding.json').read_text(encoding='utf-8'));raw=(HERE/'owned-pad-cuts-r1/prospective-geometry.pkl').read_bytes();assert hashlib.sha256(raw).hexdigest()==binding['model_sha256'];h=pickle.loads(raw)
 oldf,court=footprint_shape(g,'C11053');oldps=[p for p in g['pads'] if p['ref']=='C11053'];assert oldf['side']=='F';rec,trees=build(h,layers={'F.Cu'});courts=[q for f in g['footprints'] for ps in f['courtyard'].values() for q in poly(ps) if f['side']=='F'];ct=STRtree(courts)
 parts,_,_=source_load();ab=json.loads((HERE/'ab-prereg-split-source/receipt-r3.json').read_text(encoding='utf-8'));refs=set(parts)|set(ab['new_components']);assert len(refs)==2721 and 'C11095' not in refs and 'C11094' not in refs
 outline=unary_union(poly(g['outline'])).buffer(-.5);hard=[]
 for a in g['rule_areas']:
  if (a.get('no_footprints') or a.get('no_pads')) and 'F.Cu' in a['layers']:hard.extend(poly(a['outline']))
 ut={p['num']:p for p in h['pads'] if p['ref']=='U11018'}
 def transform(sh,xy,rot):return affinity.translate(affinity.rotate(sh,-(rot-180),origin=(oldf['x'],oldf['y'])),xy[0]-oldf['x'],xy[1]-oldf['y'])
 def location(p,xy,rot):return tuple(transform(Point(p['x'],p['y']),xy,rot).coords[0])
 def score(v):
  xy,rot=v;pin={p['num']:location(p,xy,rot) for p in oldps};return math.dist(pin['1'],(ut['8']['x'],ut['8']['y']))+math.dist(pin['2'],(ut['9']['x'],ut['9']['y']))
 tried=[];win=box(120,130,141,151)
 for xy,rot in sorted([((129.44+ix*.25,139+iy*.25),rot) for ix in range(-24,25) for iy in range(-24,25) for rot in [0,90,180,270]],key=score):
  c=transform(court,xy,rot)
  if not outline.covers(c) or any(c.intersects(courts[i]) for i in ct.query(c,predicate='intersects')) or any(c.intersects(q) for q in hard):continue
  ps={};valid=True
  for p in oldps:
   sh=transform(unary_union(poly(p['layers']['F.Cu'])),xy,rot);n=B5 if p['num']=='1' else GND
   for i in trees['F.Cu'].query(sh.buffer(.625),predicate='intersects'):
    r=rec['F.Cu'][i]
    if r['kind']=='fill' or norm(r['net'])==n:continue
    if sh.distance(r['shape'])<(.15 if r['domain']=='DOM_FIELD_B' else .6)+.025:valid=False;break
   if not valid:break
   ps[p['num']]={'shape':sh,'net':n,'at':location(p,xy,rot),'uuid':'NEW-C11095.'+p['num'],'kind':'pad'}
  if not valid:continue
  rows=[];added=[]
  for pin,to,n,w in [('1','8',B5,.35),('1','5',B5,.25),('2','9',GND,.35)]:
   obs=[];voids=[]
   for i in trees['F.Cu'].query(win.buffer(2),predicate='intersects'):
    r=rec['F.Cu'][i]
    if norm(r['net'])==n:continue
    if r['kind']=='fill':voids.append(identity(r));continue
    obs.append(r['shape'].buffer((.15 if r['domain']=='DOM_FIELD_B' else .6)+w/2+.025))
   for p in ps.values():
    if p['net']!=n:obs.append(p['shape'].buffer(.15+w/2+.025))
   for r in added:
    if r['net']!=n:obs.append(r['shape'].buffer(.15+w/2+.025))
   for p in h['pads']:
    for q in poly(p.get('hole') or []):
     if q.intersects(win):obs.append(q.buffer(.25+w/2+.025))
   for a in h['rule_areas']:
    if a.get('no_tracks') and 'F.Cu' in a['layers']:obs.extend(q.buffer(w/2+.025) for q in poly(a['outline']))
   fr=win.difference(unary_union(obs));p=ps[pin];q=ut[to];path,search=S.astar(fr.buffer(-.00001),[(p['at'],p)],[((q['x'],q['y']),{'uuid':q['uuid'],'kind':'pad'})],time.monotonic()+1,node_cap=14000)
   if path and not fr.covers(LineString(path['points_mm'])):path=None
   row={'from':'C11095.'+pin,'to':'U11018.'+to,'net':n,'width_mm':w,'search':search,'verdict':'HOST_PATH' if path else 'NO_PATH'}
   if path:row.update(path=path,mandatory_fill_voids=voids,length_mm=LineString(path['points_mm']).length);added.append({'shape':LineString(path['points_mm']).buffer(w/2),'net':n})
   rows.append(row)
   if path is None:break
  result={'pose_mm':xy,'rotation_deg':rot,'geometric_loop_minimum_mm':score((xy,rot)),'paths':rows,'local_all_paths_found':len(rows)==3 and all(r['verdict']=='HOST_PATH' for r in rows),'new_pad_positions':{k:{kk:v for kk,v in p.items() if kk!='shape'} for k,p in ps.items()}}
  tried.append(result)
  if result['local_all_paths_found']:break
  if len(tried)>=40:break
 output={'board_sha256':g['sha256'],'all_original_AB_refs_census':{'original':len(parts),'existing_AB_added':4,'total_unique':len(refs),'C11094_reserved_by_root_SBC':True,'C11095_reserved_here':True},'new_component':{'ref':'C11095','clone':'C11053','mpn':'885012206052','value':'1uF 16V X7R','footprint':'Capacitor_SMD:C_0603_1608Metric','pins':{'1':'/motherboard_safety_sensor{slash}FIELD_B_5V_PRE','2':'/motherboard_do{slash}FIELD_B_0V'}},'existing_C11076_pose_preserved':True,'source_contract_next':'Separate AB-local-bypass source variant, exactly14 original pin-net moves plus5 new parts; frozen AB14+4 files/export remain untouched.','primary_part_reference':'https://www.we-online.com/components/products/datasheet/885012206052.pdf','capacitance_gate':'Nominal1uF +/-10%,16V,X7R +/-15% temperature. Manufacturer DC-bias/aging effective minimum at5.1V and relevant temperature must remain >=0.1uF; not proved by nominal data alone.','additional_DC_feed_reservation_a':.00001,'capacitor_startup':'Added1uF*dv/dt input charging is time-dependent and requires B5PRE transient budget; no zero-inrush assertion.','candidates':tried,'source_or_board_written':False,'native_jobs':0,'source_return_qualified':False}
 OUT.write_text(json.dumps(output,indent=1)+'\n',encoding='utf-8');print(json.dumps({'tried_legal_placements':len(tried),'complete':any(x['local_all_paths_found'] for x in tried),'chosen':tried[-1] if tried else None}))
if __name__=='__main__':main()
