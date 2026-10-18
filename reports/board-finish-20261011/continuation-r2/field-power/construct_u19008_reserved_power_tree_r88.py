"""Outside-reservation .8 mm power tree with exact retained branch obligations.

No original source is edited; accepted geometry remains a proposal until complete
reference, current, original relationship, native and final joint gates pass.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,sys,re,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import set_precision,STRtree
from inventory import sha
import contact_layout as C
import tri_route as T
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=HERE/'u19008-outside-reservation-power-tree-r88'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
 assert not OUT.exists();OUT.mkdir();mp=HERE/'c-u19008-actual-regulated-search-base-r84/model.pkl';assert sha(mp)=='61e7a9e2207c2a21ae850fc7c508db85a1fc49ec391b7d9397f3750424b94c36'
 g,h,binding,zones,after=pickle.loads(mp.read_bytes());np=HERE/'u19008-coupled-power-wall-nomination-r82/receipt.json';nr=json.loads(np.read_text());old=nr['owned_old_power_track'];net=old['net'];gn=next(q['net'] for q in h['pads'] if q['ref']=='U19008' and q['num']=='11');owned_removes={t['uuid'] for t in json.loads((mp.parent/'owned-track-removals.json').read_text())}
 ud=pickle.loads((HERE/'c-u19008-actual-regulated-search-base-r84/U19008-proposed-discrete.pkl').read_bytes());failed={t['uuid'] for t in ud['tracks'] if t['net']==net};h={**h,'tracks':[t for t in h['tracks'] if t['uuid'] not in failed]}
 # Incorporate current exact CORE changed pads/new barrels/tracks as hard
 # geometry; other R84 owned changes remain exact. This local search makes no
 # projection/source pass for this combined model.
 cp=ROOT/'sbc-power/r17031-translated-source-composition-r78/model.pkl';assert sha(cp)=='128a21a83ccc8e1029f4b97e27930f82de743e00ef45fb1fc2041f0967b8a821';cg,ch,cb,cz,ca=pickle.loads(cp.read_bytes());newcu={}
 for key in ('tracks','vias'):
  seen={x['uuid'] for x in h[key]};adds=[x for x in ch[key] if x['uuid'] not in seen and x['uuid'] not in owned_removes and x['uuid'] not in failed];h[key]=h[key]+adds;newcu[key]=[x['uuid'] for x in adds]
 changed=json.loads((cp.parent/'exact-host-footprint-translation-ledger.json').read_text());moved={q['uuid']:q for q in ch['pads'] if q['uuid'] in ('1aa9d7d6-1ea4-4c3d-91f0-de0b4ac416b4','fa1831f5-068d-433f-8653-c70d19ffbbaf')};h['pads']=[moved.get(q['uuid'],q) for q in h['pads']]
 known={q['uuid'] for q in zones};zones += [q for q in cz if q['uuid'] not in known]
 rp=ROOT/'protected-field-return-r4-snapshot-4/proposed-zones.pkl';assert sha(rp)=='213182e7ec8439cccb0087bf99b362e6e149a3f21843d103b7b50ddceb428239';peers=pickle.loads(rp.read_bytes());zones += peers
 win=box(57,105,70,116);rec={l:[] for l in LAYERS};holes=[]
 for q in h['pads']:
  for l,rs in q['layers'].items():
   if l in rec:
    for sh in C.poly(rs):
     if sh.intersects(win.buffer(.9)):rec[l].append({'kind':'pad','uuid':q['uuid'],'net':q['net'],'shape':sh})
  for sh in C.poly(q.get('hole') or []):
   if sh.intersects(win.buffer(.9)):holes.append((q['net'],sh))
 for t in h['tracks']:
  if t['layer'] in rec and min(t['a'][0],t['b'][0])-t['w']/2<70.9 and max(t['a'][0],t['b'][0])+t['w']/2>56.1 and min(t['a'][1],t['b'][1])-t['w']/2<116.9 and max(t['a'][1],t['b'][1])+t['w']/2>104.1:rec[t['layer']].append({'kind':'track',**t,'shape':C.body(t)})
 for v in h['vias']:
  if not (56.1<v['x']<70.9 and 104.1<v['y']<116.9):continue
  holes.append((v['net'],P.bounded_disk(v,v['drill']/2)))
  for l in v['flashed']:rec[l].append({'kind':'via',**v,'shape':P.bounded_disk(v,v['d']/2)})
 reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 def gap(a,b,local=.15):return max(.15 if h['domains_normalized'].get(C.norm(a))==h['domains_normalized'].get(C.norm(b)) else .6,local)+.025
 def free_for(net,layer,zone=False):
  walls=[P.bounded_buffer(q['shape'],gap(net,q['net'])) for q in rec[layer] if q['net']!=net]
  walls += [P.bounded_buffer(q['shape'].intersection(win.buffer(.627)),gap(net,q['net'],float(q.get('clearance_mm',.15)))) for q in zones if q['layer']==layer and q['net']!=net and q['shape'].intersects(win.buffer(.627))]
  walls += [P.bounded_buffer(sh,.275) for hn,sh in holes if hn!=net]
  for area in h['rule_areas']:
   if layer in area['layers'] and area.get('no_zones' if zone else 'no_tracks'):walls += [P.bounded_buffer(sh,.025) for sh in C.poly(area['outline']) if sh.intersects(win.buffer(.025))]
  if not zone:
   for area in reserved['keepouts']:
    if layer in area['layers'] and C.norm(net) not in exceptions.get(area['name'],set()):walls += [P.bounded_buffer(sh,.025) for sh in C.poly(area['outline']) if sh.intersects(win.buffer(.025))]
  return set_precision(win.difference(unary_union(walls)),1e-6)
 bfree=free_for(net,'B.Cu');gfree=free_for(gn,'In4.Cu',zone=True)
 contacts=json.loads((HERE/'u19008-coupled-power-wall-nomination-r82/outside-contact-ledger.json').read_text());contactsh={q['uuid']:q['shape'] for q in rec['B.Cu'] if q['uuid'] in {r['uuid'] for r in contacts}}
 answer=None;attempts=[]
 # Route a tree between available native branch portions, avoiding the old
 # endpoint disks inside the declared U19008 escape reservations.
 for reference_required in (True,False):
  usable=bfree.intersection(gfree) if reference_required else bfree
  cores=polys(usable.buffer(-.402))
  for part in cores:
   starts=part.intersection(contactsh['4b070be4-ead5-4ab1-908b-65f9fcd63eb3'].buffer(.398));ends=part.intersection(contactsh['6e675361-9509-4d5c-b9b4-ad0603306a5f'].buffer(.398))
   if starts.is_empty or ends.is_empty:continue
   sa,sb=nearest_points(starts.buffer(-.000002),ends.buffer(-.000002))
   if sa.is_empty or sb.is_empty:continue
   try:points,search=T.route(part,tuple(sa.coords[0]),tuple(sb.coords[0]))
   except (AssertionError,ValueError) as e:attempts.append({'ref_free_required':reference_required,'route_error':str(e)});continue
   points=[[round(x,6),round(y,6)] for x,y in points];body=P.bounded_buffer(LineString(points),.4);loss=[{'uuid':r['uuid'],'overlap_mm2':body.intersection(contactsh[r['uuid']]).area} for r in contacts if body.intersection(contactsh[r['uuid']]).area<.001]
   if not usable.covers(body) or loss:attempts.append({'ref_free_required':reference_required,'outside_losses':loss,'coverage_missing_mm2':body.difference(usable).area});continue
   answer={'points_mm':points,'length_mm':LineString(points).length,'width_mm':.8,'all_six_outside_contacts':[dict(r,replacement_overlap_mm2=body.intersection(contactsh[r['uuid']]).area) for r in contacts],'ground_reference_free_geometry_covers_full_body':reference_required,'search':search};break
  if answer:break
 print('R88 route',answer,flush=True)
 write(OUT/'route-attempts.json',attempts)
 if not answer:write(OUT/'receipt.json',{'verdict':'NO_OUTSIDE_RESERVATION_BRANCH_TREE_FOUND','attempts_sha256':sha(OUT/'route-attempts.json'),'board_written':False,'native_jobs':0});return
 tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-u19008-r88/power/{i}')),'net':net,'layer':'B.Cu','a':a,'b':b,'w':.8,'locked':True,'prospective_not_native':True} for i,(a,b) in enumerate(zip(answer['points_mm'],answer['points_mm'][1:]))]
 paired={'vias':ud['vias'],'tracks':[t for t in ud['tracks'] if t['net']!=net]};d={'vias':paired['vias'],'tracks':paired['tracks']+tracks};(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps(d,protocol=5));(OUT/'proposed-power-body.wkb').write_bytes(body.wkb);(OUT/'reference-zone-free.wkb').write_bytes(gfree.wkb);write(OUT/'outside-contact-ledger.json',answer['all_six_outside_contacts'])
 write(OUT/'receipt.json',{'verdict':'OUTSIDE_RESERVATION_TREE_NOMINATION_ALL_JOINT_REFERENCE_SOURCE_CURRENT_NATIVE_GATES_OPEN','input_R84_model_sha256':sha(mp),'current_CORE78_model_sha256':sha(cp),'current_root_four_spines_sha256':sha(rp),'new_CORE_hard_Cu':newcu,'translated_CORE_pad_UUIDs':sorted(moved),'withdraw_failed_R82_power_tracks':sorted(failed),'owned_original_delete':old,'answer':answer,'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'power_body_WKB_sha256':sha(OUT/'proposed-power-body.wkb'),'reference_zone_free_sha256':sha(OUT/'reference-zone-free.wkb'),'outside_contact_ledger_sha256':sha(OUT/'outside-contact-ledger.json'),'board_written':False,'native_jobs':0})
 print('R88 nomination',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
