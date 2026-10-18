"""Actual owned field-return body for the revised reserved-safe power tree."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys,copy,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely import set_precision,from_wkb
from shapely.ops import unary_union,nearest_points
import contact_layout as C
import fast_contacts as F
import tri_route as T
from inventory import sha
H=Path(__file__).resolve().parent;ROOT=H.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=H/'u19008-source-return-reference-r98'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'c-u19008-actual-regulated-search-base-r84/model.pkl';assert sha(mp)=='61e7a9e2207c2a21ae850fc7c508db85a1fc49ec391b7d9397f3750424b94c36';g,h,b,z,a=pickle.loads(mp.read_bytes());rp=H/'u19008-retained-logic-barrel-relocation-r95/owned-replacements.pkl';assert sha(rp)=='1d3052cb375c149f8243ea53b917ecdb0f014b9578446b9cf6a9396fc7a3fa81';repl=pickle.loads(rp.read_bytes());oldud=pickle.loads((mp.parent/'U19008-proposed-discrete.pkl').read_bytes());powerold={q['uuid'] for q in oldud['tracks'] if q['w']==.8};dp=H/'u19008-outside-reservation-branch-tree-r89/proposed-discrete.pkl';d=pickle.loads(dp.read_bytes());vid={q['uuid']:q for q in repl['vias']};tid={q['uuid']:q for q in repl['tracks']};h={**h,'tracks':[tid.get(t['uuid'],t) for t in h['tracks'] if t['uuid'] not in powerold]+[t for t in d['tracks'] if t['w']==.8],'vias':[vid.get(v['uuid'],v) for v in h['vias']]};gn=next(q['net'] for q in d['vias'] if C.norm(q['net'])=='/motherboard_do/FIELD_B_0V');body=from_wkb((dp.parent/'proposed-power-body.wkb').read_bytes());win=box(52,100,85,123)
 # This exact local corridor lies outside the later CORE/R17031 and four
 # root FAG spines. Keep all current peer bodies hard and verify that fact.
 cp=ROOT/'sbc-power/r17031-translated-source-composition-r78/model.pkl';cg,ch,cb,cz,ca=pickle.loads(cp.read_bytes());seen={q['uuid'] for q in z};peernew=[q for q in cz if q['uuid'] not in seen];pp=ROOT/'protected-field-return-r4-snapshot-4/proposed-zones.pkl';peers=pickle.loads(pp.read_bytes());z+=peernew+peers
 rec,trees=F.build({**h,'zones':[]});walls=[]
 def gap(net,local=.15):return max(.15 if h['domains_normalized'].get(C.norm(net))==h['domains_normalized'].get(C.norm(gn)) else .6,local)+.025
 for j in trees['In4.Cu'].query(win.buffer(.627),predicate='intersects'):
  q=rec['In4.Cu'][int(j)]
  if q['net']==gn:continue
  if q['kind']=='track':t=next(t for t in h['tracks'] if t['uuid']==q['uuid']);cut=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap(t['net']))
  elif q['kind']=='via':v=next(v for v in h['vias'] if v['uuid']==q['uuid']);cut=P.bounded_disk(v,v['d']/2+gap(v['net']))
  else:cut=P.bounded_buffer(q['shape'],gap(q['net']))
  walls.append(cut)
 for q in z:
  if q['layer']=='In4.Cu' and q['net']!=gn and q['shape'].intersects(win.buffer(.627)):walls.append(P.bounded_buffer(q['shape'].intersection(win.buffer(.627)),gap(q['net'],float(q.get('clearance_mm',.15)))))
 holes=[];ownholes=[]
 for pad in h['pads']:
  for sh in C.poly(pad.get('hole') or []):
   if sh.intersects(win):
    if pad['net']==gn:ownholes.append(sh)
    else:walls.append(P.bounded_buffer(sh,.275))
 for v in h['vias']:
  if not (51<v['x']<86 and 99<v['y']<124):continue
  sh=P.bounded_disk(v,v['drill']/2)
  if v['net']==gn:ownholes.append(sh)
  else:walls.append(P.bounded_buffer(sh,.275))
 for area in h['rule_areas']:
  if 'In4.Cu' in area['layers'] and area.get('no_zones'):walls += [P.bounded_buffer(sh,.025) for sh in C.poly(area['outline']) if sh.intersects(win.buffer(.025))]
 free=set_precision(win.difference(unary_union(walls)),1e-6);lost=body.difference(free);write(OUT/'power-body-reference-free-check.json',{'missing_area_mm2':lost.area,'new_LOGIC_location':[repl['vias'][0]['x'],repl['vias'][0]['y']]});print('R98 true reference legal missing',lost.area,flush=True)
 if not lost.is_empty and lost.area>1e-10:write(OUT/'receipt.json',{'verdict':'FAIL_POWER_BODY_REFERENCE_CORRIDOR','missing_mm2':lost.area,'board_written':False});return
 gs=F.graph(a,gn);ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and (q['ref'],q['pin'])==('J11005','2') for q in xs));rootref=unary_union([q['shape'] for q in gs[ri] if q['layer']=='In4.Cu' and q['kind']=='fill']);base=P.bounded_buffer(body,.12).intersection(free);initial=set_precision(unary_union([p for p in polys(base) if p.intersection(body).area>1e-8]),1e-6);assert body.difference(initial).area<1e-10;bridge=None
 if initial.intersection(rootref).area>=.001:bridge={'method':'positive_real_J11005_source_fill_overlap','length_mm':0.,'overlap_mm2':initial.intersection(rootref).area};native=initial
 else:
  for width in (.5,.35,.25):
   for part in polys(free.buffer(-width/2-.002)):
    start=part.intersection(initial);goal=part.intersection(rootref)
    if start.is_empty or goal.is_empty:continue
    aa,bb=nearest_points(start,goal)
    try:points,search=T.route(part,tuple(aa.coords[0]),tuple(bb.coords[0]))
    except (AssertionError,ValueError):continue
    line=LineString([[round(x,6),round(y,6)] for x,y in points]);core=P.bounded_buffer(line,width/2)
    if not free.covers(core):continue
    native=set_precision(unary_union([initial,P.bounded_buffer(line,max(.25,width)).intersection(free)]),1e-6)
    if native.intersection(rootref).area<.001:continue
    bridge={'method':'covered_real_same_layer_J11005_source_return_bridge','length_mm':line.length,'core_width_mm':width,'points_mm':list(line.coords),'source_fill_overlap_mm2':native.intersection(rootref).area,'search':search};break
   if bridge:break
 if not bridge:write(OUT/'receipt.json',{'verdict':'NO_J11005_SOURCE_RETURN_BRIDGE','board_written':False});return
 physical=set_precision(native.difference(unary_union(ownholes)),1e-6);q={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-u19008-r98/source-return-reference')),'net':gn,'layer':'In4.Cu','shape':physical,'zone_outline_shape':native,'clearance_mm':.15,'label':'U19008-reserved-safe-B-power-source-return','physical_Cu_drill_subtracted':True};(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps([q],protocol=5));(OUT/'prospective-reference-free.wkb').write_bytes(free.wkb);(OUT/'real-source-reference-contact.wkb').write_bytes(physical.intersection(rootref).wkb)
 write(OUT/'receipt.json',{'verdict':'PROPOSED_REAL_SOURCE_RETURN_REFERENCE_COMPLETE_FRESH_SOURCE_ALL_CONTACT_NATIVE_CURRENT_GATES_OPEN','R84_model_sha256':sha(mp),'CORE78_model_sha256':sha(cp),'root_four_spines_sha256':sha(pp),'R89_power_discrete_sha256':sha(dp),'R95_LOGIC_replacement_sha256':sha(rp),'power_body_physical_reference_missing_mm2':body.difference(physical).area,'bridge':bridge,'source_root':'J11005.2','actual_rooted_In4_fill_overlap_mm2':physical.intersection(rootref).area,'local_clearance_mm':.15,'priority':124,'min_thickness_mm':.15,'new_holes':0,'new_original_zone_definition_changes':0,'proposed_zone_pickle_sha256':sha(OUT/'proposed-zones.pkl'),'board_written':False,'native_jobs':0});print('R98',bridge,sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
