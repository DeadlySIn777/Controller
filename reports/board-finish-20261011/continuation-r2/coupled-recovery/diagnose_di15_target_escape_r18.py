"""Identify actual local target copper/reference blockers without rip-up."""
import sys,pickle,json,time,math
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import tri_route as T
import construct_di6_direct_source_escape_r5 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
NET='/motherboard_di/DI15_LOGIC';GND='/LOGIC_GND'
def main():
 started=time.monotonic();out=HERE/'di15-target-exact-blocker-diagnostic-r18.json';assert not out.exists();A.read(__file__);raw=A.read(HERE/'di15-current-r78-projection-r13.pkl');assert C.sha(raw)=='2b272430cc2d0e2368a23c3d7aad25c3142010fdbec4ef6f2f78ff3239cd82c2';cp=pickle.loads(raw);h=cp['h'];zones=cp['zones'];refs=cp['refs'];win=box(127,109,137,120);domain=h['domains_normalized'];target=next(p for p in h['pads'] if(p['ref'],str(p['num']))==('U17005','9'));pad=unary_union(L.poly(target['layers']['F.Cu']));rec,trees=F.build({**h,'zones':[]});reserve,exempt=A.reservations();hard=[];holes=[]
 for r in h['rule_areas']:
  for sh in L.poly(r['outline']):
   if sh.distance(win)<2:hard.append({'uuid':r['uuid'],'shape':sh,'layers':r['layers'],'no_vias':r.get('no_vias'),'no_tracks':r.get('no_tracks'),'exempt':set()})
 for r in reserve['keepouts']:
  for sh in L.poly(r['outline']):
   if sh.distance(win)<2:hard.append({'uuid':r['name'],'shape':sh,'layers':r['layers'],'no_vias':True,'no_tracks':True,'exempt':exempt.get(r['name'],set())})
 for v in h['vias']:
  if Point(v['x'],v['y']).distance(win)<2:holes.append((v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)))
 for p in h['pads']:
  for sh in L.poly(p.get('hole') or []):
   if sh.distance(win)<2:holes.append((p['uuid'],L.norm(p['net']),sh))
 smd=[sh for p in h['pads'] if p['smd'] for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for sh in L.poly(rs) if sh.distance(win)<2];physical={};via=[];nearest=[]
 for l in K.LAYERS:
  obs=[];vobs=[]
  for i in trees[l].query(win.buffer(2),predicate='intersects'):
   r=rec[l][int(i)];n=L.norm(r['net'])
   if n==NET:continue
   gap=.15 if domain.get(n)==domain.get(NET) else .6;obs.append(r['shape'].buffer(gap+.030,quad_segs=128));vobs.append(r['shape'].buffer(.25+gap+.030,quad_segs=128))
   if l=='F.Cu':nearest.append({'UUID':r['uuid'],'kind':r['kind'],'raw_net':r['net'],'gap_to_actual_target_pad_mm':r['shape'].distance(pad),'required_native_domain_mm':gap,'bounds_mm':r['shape'].bounds})
  for z in zones:
   n=L.norm(z['net'])
   if z['layer']!=l or n==NET or z['shape'].distance(win)>2:continue
   gap=.15 if domain.get(n)==domain.get(NET) else .6;required=max(gap,float(z.get('clearance_mm',.15)));obs.append(z['shape'].buffer(required+.030,quad_segs=128));vobs.append(z['shape'].buffer(.25+required+.030,quad_segs=128))
  for z in cp['after']['zones']:
   n=L.norm(z['net']);gap=.15 if domain.get(n)==domain.get(NET) else .6
   if n==NET or gap==.15:continue
   for sh in L.poly(z['fills'].get(l,[])):
    if sh.distance(win)<2:
     required=max(gap,float(z.get('clearance_mm',.15)));obs.append(sh.buffer(required+.030,quad_segs=128));vobs.append(sh.buffer(.25+required+.030,quad_segs=128))
  obs += [sh.buffer(.280,quad_segs=128) for u,n,sh in holes if n!=NET];obs += [r['shape'].buffer(.025,quad_segs=128) for r in hard if r['no_tracks'] and l in r['layers'] and NET not in r['exempt']];physical[l]=win.difference(unary_union(obs)).buffer(-.105);vobs += [r['shape'].buffer(.275,quad_segs=128) for r in hard if r['no_vias'] and l in r['layers'] and NET not in r['exempt']];via.append(win.difference(unary_union(vobs)))
 vr=via[0]
 for p in via[1:]:vr=vr.intersection(p)
 ordinary=[Point(v['x'],v['y']).buffer(.81,quad_segs=128) for v in h['vias'] if Point(v['x'],v['y']).distance(win)<2]+[sh.buffer(.380,quad_segs=128) for u,n,sh in holes]+[sh.buffer(.380,quad_segs=128) for sh in smd];vr=vr.difference(unary_union(ordinary));attachment=pad.buffer(-.075).intersection(physical['F.Cu']);starts=K.sites(attachment,list(pad.centroid.coords)[0],12);rootfree=physical['F.Cu'].intersection(refs['F.Cu'].intersection(win.buffer(2)).buffer(-.105));diag=[];attempts=[]
 for s in starts:
  comp=unary_union([p for p in K.pieces(physical['F.Cu']) if p.covers(Point(s['at_mm']))]);rcomp=unary_union([p for p in K.pieces(rootfree) if p.covers(Point(s['at_mm']))]);legal=vr.intersection(comp);diag.append({'attachment_mm':s['at_mm'],'physical_F_component_area_mm2':comp.area,'physical_F_component_reaches_window_edge':comp.distance(win.boundary)<.02,'ordinary_all6_sites_in_physical_F_component_mm2':legal.area,'ordinary_all6_sites_in_rooted_reference_F_component_mm2':vr.intersection(rcomp).area})
  for v in K.sites(legal,[131.25,112.35],5):
   pp=[p for p in K.pieces(comp) if p.covers(Point(s['at_mm'])) and p.covers(Point(v['at_mm']))]
   if not pp:continue
   pts,search=T.route(pp[0],tuple(s['at_mm']),tuple(v['at_mm']));pts=[[round(x,6),round(y,6)] for x,y in pts];body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(pts,pts[1:])]);missing=body.difference(refs['F.Cu']);fn=HERE/('di15-target-r18-'+str(len(attempts))+'.wkb');fn.write_bytes(missing.wkb);zoneblocks=[{'UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'local_clearance_mm':z.get('clearance_mm',.15),'body_overlap_mm2':z['shape'].intersection(missing).area,'gap_to_reference_gap_mm':z['shape'].distance(missing)} for z in zones if z['layer']=='In1.Cu' and z['shape'].distance(missing)<.65];barrelblocks=[{'UUID':q['uuid'],'raw_net':q['net'],'at_mm':[q['x'],q['y']],'diameter_mm':q['d'],'actual_flashed_layers':q['flashed'],'distance_to_reference_gap_mm':Point(q['x'],q['y']).distance(missing)} for q in h['vias'] if Point(q['x'],q['y']).distance(missing)<.9];attempts.append({'source_attachment_mm':s['at_mm'],'ordinary_signal_via_mm':v['at_mm'],'F_points_mm':pts,'length_mm':LineString(pts).length,'actual_source_pad_contact_mm2':body.intersection(pad).area,'full_body_current_source_root_reference_gap_mm2':missing.area,'gap_bounds_mm':missing.bounds,'gap_WKB_path':str(fn),'gap_WKB_sha256':C.sha(missing.wkb),'prospective_In1_zone_reference_blockers':zoneblocks,'native_existing_nearby_annuli':barrelblocks,'search':search})
  if attempts:break
 result={'verdict':'DI15_TARGET_PHYSICAL_ESCAPE_DIAGNOSED_REFERENCE_REPAIR_OPEN' if attempts else'DI15_TARGET_LOCAL_PHYSICAL_COMPONENT_OR_ORDINARY_SITE_BLOCKED','exact_current_checkpoint_sha256':C.sha(raw),'current_R78_model_sha256':cp['R78_model_sha256'],'target_actual_physical_pad_UUID':target['uuid'],'target_actual_pad_bounds_mm':pad.bounds,'nearest_F_discrete_blockers':sorted(nearest,key=lambda q:q['gap_to_actual_target_pad_mm'])[:20],'ordinary_all6_legal_area_mm2_before_reference_protection':vr.area,'actual_target_attachment_area_mm2':attachment.area,'physical_vs_root_reference_components':diag,'attempts':attempts,'all_current_copper_preserved':True,'all_final_contact_source_reference_paired_return_native_gates':'OPEN','native_jobs':0,'board_written':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({'verdict':result['verdict'],'diagnosis':diag,'attempts':attempts,'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
