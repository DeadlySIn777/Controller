"""Find an exact single retained-track separator; no deletion or routing credit."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,re
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import regional_guarded_declared_projection_r140 as P
import complete_geometry_r2 as G
from inventory import sha
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
O=H/'U10009-exact-outer-single-track-separator-r259'
def polys(sh):return [] if sh.is_empty else [sh] if sh.geom_type=='Polygon' else [p for p in getattr(sh,'geoms',[]) if p.geom_type=='Polygon' and not p.is_empty]
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'U10009-continuous-centre-source-search-base-r255';g,h,b,z,a=pickle.loads((base/'model.pkl').read_bytes())
 # Pickle drops generated tags; this diagnostic restores the exact WKB only.
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb
 pad=next(p for p in h['pads'] if(p['ref'],p['num'])==('U10009','4'));net=C.norm(pad['net']);anchor=Point(pad['x'],pad['y']);win=box(anchor.x-12,anchor.y-12,anchor.x+12,anchor.y+12);outline=unary_union(C.poly(h['outline'])).buffer(-.526);win=win.intersection(outline);query=win.buffer(1.5)
 hard=b['field_regulated_search_hard_nominees']['planes'];qall=z+hard;rec,trees=F.build({**h,'zones':[]});tracks={t['uuid']:t for t in h['tracks']};vias={v['uuid']:v for v in h['vias']};walls=[];centrewalls=[]
 def gap(raw):return G.gap(h,pad['net'],raw)+.025
 def bodycut(q,radius):
  if q['kind']=='track':t=tracks[q['uuid']];return P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+radius)
  if q['kind']=='via':v=vias[q['uuid']];return P.bounded_disk(v,v['d']/2+radius)
  return P.bounded_buffer(q['shape'],radius)
 for layer,tree in trees.items():
  for j in tree.query(query,predicate='intersects'):
   q=rec[layer][int(j)]
   if C.norm(q['net'])==net:continue
   centrewalls.append(bodycut(q,.25+gap(q['net'])))
   if layer=='B.Cu':walls.append({'kind':q['kind'],'UUID':q['uuid'],'raw_net':q['net'],'cut':bodycut(q,gap(q['net']))})
 for q in qall:
  if C.norm(q['net'])==net or not q['shape'].intersects(query):continue
  req=max(gap(q['net']),float(q.get('clearance_mm',.15))+.025)
  if not(q['layer'] in ('In1.Cu','In2.Cu','In4.Cu') and C.norm(q['net'])=='/motherboard_motors/FIELD_GND' and q in z):centrewalls.append(P.bounded_buffer(q['shape'],.25+req))
  if q['layer']=='B.Cu':walls.append({'kind':'owned_plane','UUID':q['uuid'],'raw_net':q['net'],'cut':P.bounded_buffer(q['shape'],req)})
 for p in h['pads']:
  if p['smd']:
   for layer,records in p['layers'].items():
    if layer not in ('F.Cu','B.Cu'):continue
    sh=unary_union(C.poly(records))
    if sh.intersects(query):centrewalls.append(P.bounded_buffer(sh,.1+.275))
  for sh in C.poly(p.get('hole') or []):
   if not sh.intersects(query):continue
   centrewalls.append(P.bounded_buffer(sh,.1+.275))
   if not(bool(p['num']) and C.norm(p['net'])==net):walls.append({'kind':'pad_hole','UUID':p['uuid'],'raw_net':p['net'],'cut':P.bounded_buffer(sh,.275)})
 for v in h['vias']:
  pt=Point(v['x'],v['y'])
  if not pt.buffer(v['d']/2).intersects(query):continue
  centrewalls.append(P.bounded_disk(v,v['drill']/2+.1+.275))
  if C.norm(v['net'])!=net:walls.append({'kind':'via_hole','UUID':v['uuid'],'raw_net':v['net'],'cut':P.bounded_disk(v,v['drill']/2+.275)})
 reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text(encoding='utf-8');exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 for area in h['rule_areas']:
  for sh in C.poly(area['outline']):
   if not sh.intersects(query):continue
   if area.get('no_vias'):centrewalls.append(P.bounded_buffer(sh,.25+.025))
   if area.get('no_tracks') and 'B.Cu' in area['layers']:walls.append({'kind':'native_rule_area','UUID':area['uuid'],'raw_net':None,'cut':P.bounded_buffer(sh,.025)})
 for area in reserved['keepouts']:
  if net in exceptions.get(area['name'],set()):continue
  for sh in C.poly(area['outline']):
   if not sh.intersects(query):continue
   centrewalls.append(P.bounded_buffer(sh,.25+.025))
   if 'B.Cu' in area['layers']:walls.append({'kind':'reserved_area','UUID':area['name'],'raw_net':None,'cut':P.bounded_buffer(sh,.025)})
 centres=win.difference(unary_union(centrewalls)).buffer(-.000003);padshape=unary_union(C.poly(pad['layers']['B.Cu']));nominees=[];checks=[]
 def reachable(skip):
  free=win.difference(unary_union([r['cut'] for r in walls if r['UUID'] not in skip]));parts=[q for q in polys(free.buffer(-.105)) if q.intersects(padshape)]
  accessible=unary_union(parts);contacts=accessible.intersection(centres);return free,accessible,contacts
 originalfree,part,contacts=reachable(set());(O/'actual-B-route-free.wkb').write_bytes(originalfree.wkb);(O/'all6-layer-ordinary-legal-centres.wkb').write_bytes(centres.wkb);(O/'actual-target-B-0.2-centre-component.wkb').write_bytes(part.wkb)
 candidateids=sorted({r['UUID'] for r in walls if r['kind']=='track' and r['UUID'] in {t['uuid'] for t in g['tracks']} and r['cut'].intersects(part.buffer(1.5))})
 print('R259 candidate tracks',len(candidateids),'target accessible',part.area,'all6centre',centres.area,flush=True)
 for uid in candidateids:
  free,connected,sites=reachable({uid});row={'owned_candidate_original_track_UUID':uid,'raw_net':tracks[uid]['net'],'a':tracks[uid]['a'],'b':tracks[uid]['b'],'width_mm':tracks[uid]['w'],'opened_accessible_mm2':connected.area,'actual_still_legal_all6_via_centres_mm2':sites.area,'single_track_replacement_required_no_deletion_credit':True};checks.append(row)
  if not sites.is_empty:
   for pocket in polys(sites):
    pt=pocket.representative_point();row['nominee_xy_mm']=[round(pt.x,6),round(pt.y,6)];nominees.append(row.copy());break
  write(O/'separator-checkpoint.json',checks)
 write(O/'receipt.json',{'verdict':'SINGLE_TRACK_COUPLED_ESCAPE_NOMINATIONS_REQUIRE_REPLACEMENT' if nominees else 'NO_SINGLE_TRACK_ESCAPE_IN_DECLARED_12MM_WINDOW','input_model_sha256':sha(base/'model.pkl'),'target':'U10009.4','complete_existing_physical_and_ordinary_centre_guards':True,'source_and_outer_stub_reference_no_loss_current_native':'OPEN','single_track_tests':len(checks),'nominees':nominees,'zero_original_Cu_or_source_changes':True,'native_jobs':0,'board_written':False});print('R259 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
