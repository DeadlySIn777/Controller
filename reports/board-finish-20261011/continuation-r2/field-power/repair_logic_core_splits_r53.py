"""Restore two six-contact LOGIC branches after CORE feeds, no new holes."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,sys,uuid,hashlib
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision,get_num_coordinates
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
from u11015_projection_r49 import correct_original_fills
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import zone_projection_r1 as N
OUT=HERE/'logic-core-split-repair-r53'
LAYERS=['In1.Cu','In4.Cu','In2.Cu','In3.Cu','F.Cu','B.Cu']

def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def polys(sh):return [sh] if sh.geom_type=='Polygon' else [x for x in getattr(sh,'geoms',[]) if x.geom_type=='Polygon']
def main():
 assert not OUT.exists();OUT.mkdir();rp=HERE.parent/'sbc-power/actual-core-cross-layer-source-bridge-r38';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'model.pkl')==rr['model_sha256'];g,h,binding,zones,_=pickle.loads((rp/'model.pkl').read_bytes());r44p=HERE/'u11015-reverse-companion-repair-r44';r44=json.loads((r44p/'receipt.json').read_text());assert sha(r44p/'proposed-discrete.pkl')==r44['proposed_discrete_sha256'];d=pickle.loads((r44p/'proposed-discrete.pkl').read_bytes());rem={q['uuid'] for q in r44['owned_original_track_removals']};h={**h,'tracks':[q for q in h['tracks'] if q['uuid'] not in rem]+d['tracks'],'vias':h['vias']+d['vias']}
 ids={z['uuid'] for z in zones if z.get('label')=='CORE-main-In2' or z.get('label','').startswith('IO3-r15-field-crossing-') or z.get('field_return_proposal') and z['layer']=='In2.Cu'};assert len(ids)==9;zones=[{**z,'shape':set_precision(z['shape'],1e-6)} if z['uuid'] in ids else z for z in zones]
 print('project R38+R44',len(zones),flush=True);after,cuts=N.projected(g,h,zones);after,rounded_cuts=correct_original_fills(after,d['vias']);(OUT/'projected-base.pkl').write_bytes(pickle.dumps((g,h,binding,zones,after),protocol=5));net='/LOGIC_GND';gg=F.graph(after,net);ri=next(i for i,xs in enumerate(gg) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));root=gg[ri];raw=next(q['net'] for q in root if q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2'));targets=['2cfe9b9e-41bf-43e3-9c0b-ad0b75fe6f4a','5e32b51b-fbc8-4441-8796-8d7a09753a2b'];wanted=[]
 for target in targets:
  gi=next(i for i,xs in enumerate(gg) if any(q['uuid']==target for q in xs))
  if gi!=ri and gi not in wanted:wanted.append(gi)
 source={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in LAYERS};rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526);obstacles={};ots={};adds=[];rows=[]
 domain=h['domains_normalized'][net]
 def gap(other):return .15 if h['domains_normalized'].get(C.norm(other))==domain else .6
 for l in LAYERS:
  sh=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in zones if q['layer']==l and C.norm(q['net'])!=net]
  for v in h['vias']:
   if v['net']!=raw:sh.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=64))
  for p0 in h['pads']:
   if p0['net']!=raw:sh.extend([s.buffer(.275) for s in C.poly(p0.get('hole') or [])])
  for area in h['rule_areas']:
   if area.get('no_zones') and l in area['layers']:sh.extend([s.buffer(.025) for s in C.poly(area['outline'])])
  obstacles[l]=sh;ots[l]=STRtree(sh)
 for gi in wanted:
  contacts=gg[gi];answer=None;options=[]
  for l in LAYERS:
   target=unary_union([q['shape'] for q in contacts if q['layer']==l and q['kind']!='fill']);goal=source[l]
   if target.is_empty or goal.is_empty:continue
   a,b=nearest_points(target,goal);options.append((a.distance(b),l,a,b,target))
  for distance,l,a,b,target in sorted(options,key=lambda x:x[0]):
   for margin in(5.,15.,35.):
    win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=ots[l].query(win,predicate='intersects');legal=win.difference(unary_union([obstacles[l][int(j)] for j in ii]));goal=source[l]
    for width in(1.,.75,.5,.35):
     parts=[]
     for part in polys(legal.buffer(-width/2-.005)):
      aa=part.buffer(-.00002).intersection(target);bb=part.buffer(-.00002).intersection(goal)
      if not aa.is_empty and not bb.is_empty:parts.append((aa.distance(bb),part,aa,bb))
     if not parts:continue
     _,part,aa,bb=min(parts,key=lambda x:x[0]);start,end=nearest_points(aa,bb)
     if get_num_coordinates(part)>160000:
      safe=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);poss=[x for x in polys(safe) if x.intersects(aa) and x.intersects(bb)]
      if not poss:continue
      part=max(poss,key=lambda x:x.area);start,end=nearest_points(part.buffer(-.00002).intersection(aa),part.buffer(-.00002).intersection(bb))
     try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
     except(AssertionError,ValueError):continue
     line=LineString(points);core=line.buffer(width/2,quad_segs=32)
     if not legal.buffer(.000001).covers(core):continue
     intended=set_precision(unary_union([x for x in polys(line.buffer(max(.75,width/2+.1),quad_segs=32).intersection(legal)) if x.intersects(core)]),1e-6)
     ownholes=unary_union([Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64) for v in h['vias'] if v['net']==raw]+[s for p0 in h['pads'] if p0['net']==raw for s in C.poly(p0.get('hole') or [])]);body=set_precision(intended.difference(ownholes),1e-6)
     if body.intersection(target).area<.001 or body.intersection(goal).area<.001:continue
     uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-logic-core-split-r53/{gi}/{l}'));z={'uuid':uid,'net':raw,'layer':l,'shape':body,'zone_outline_shape':intended,'physical_Cu_drill_subtracted':True,'label':f'LOGIC-retained-CORE-split-r53-{gi}','clearance_mm':.15};adds.append(z);source[l]=unary_union([goal,body]);answer={'group':gi,'verdict':'CONSTRUCTED','source_root':'J11001.2','zone_UUID':uid,'raw_net':raw,'layer':l,'physical_contacts':[C.identity(q) for q in contacts if q['kind']!='fill'],'minimum_core_width_mm':width,'length_mm':line.length,'points_mm':points,'source_overlap_mm2':body.intersection(goal).area,'retained_target_overlap_mm2':body.intersection(target).area,'sheet_only_R35um60C_ohm':.00057003672*line.length/width,'search':search};print(gi,'constructed',l,width,line.length,flush=True);break
    if answer:break
   if answer:break
  rows.append(answer or {'group':gi,'verdict':'NO_PATH','physical_contacts':[C.identity(q) for q in contacts if q['kind']!='fill']});write(OUT/'checkpoint.json',rows)
 (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5));(OUT/'base-model.pkl').write_bytes(pickle.dumps((g,h,binding,zones,after),protocol=5));write(OUT/'outward-round-cutter-ledger.json',rounded_cuts)
 receipt={'verdict':'CONSTRUCTED_RETAINED_LOGIC_SPLIT_REPAIRS_MUTUAL_NATIVE_CURRENT_PENDING' if all(x['verdict']=='CONSTRUCTED' for x in rows) else 'LOGIC_SPLIT_REPAIR_INCOMPLETE','rows':rows,'new_vias':0,'new_segments':0,'new_zones':len(adds),'input_R38_model_sha256':sha(rp/'model.pkl'),'input_R44_receipt_sha256':sha(r44p/'receipt.json'),'input_R46_receipt_sha256':sha(HERE/'u11015-r44-joint-contact-audit-r46/receipt.json'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'base_model_sha256':sha(OUT/'base-model.pkl'),'outward_round_cutter_ledger_sha256':sha(OUT/'outward-round-cutter-ledger.json'),'R49_helper_sha256':sha(HERE/'u11015_projection_r49.py'),'existing_native_zone_outlines_settings_UUIDs_unchanged':True,'all_field_return_proposal_shapes_unchanged':True,'protected24_R7_and_regulated_R41_not_composed':True,'native_jobs':0,'board_written':False,'complete_oldcontact_native_min_thickness_source_signedcurrent_mesh_fault_thermal_gates':'OPEN'};write(OUT/'receipt.json',receipt);print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
