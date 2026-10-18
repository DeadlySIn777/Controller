"""Actual DI15 endpoint transition/return nomination on checked R118.

No source, native, board or current model mutation. Full all-six physical
screen including every pad, flash layer, foreign positive power and hole.
"""
import sys,json,pickle,math,time,copy
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import construct_di6_direct_source_escape_r5 as K
import guarded_power_projection_r44 as Z
from shapely.geometry import Point,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
C=A.C;NET='/motherboard_di/DI15_LOGIC';GND='/LOGIC_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def main():
 started=time.monotonic();out=H/'DI15-actual-endpoint-return-nomination-r132.json';assert not out.exists();A.read(__file__);rp=H/'di15-safe-root-r42-DI6-bind-r118.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='bb171905c94a5795d7ae3e3ded2a367c4d02a4b463bf9c82b4c6c962126c69c6';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h=cur['h'];g=cur['after'];domains=h['domains_normalized'];rec,trees=F.build({**h,'zones':[]});source=A.read(cur['binding']['exact_native_discrete_board_file']);identity=A.N.SourceNets(source);reserve,exempt=A.reservations();smd=[(p['uuid'],p['ref'],p['num'],q) for p in h['pads'] if p['smd'] for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for q in L.poly(rs)];st=STRtree([q[3] for q in smd]);holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)) for v in h['vias']]+[(p['uuid'],q) for p in h['pads'] for q in L.poly(p.get('hole') or [])];ht=STRtree([q[1] for q in holes]);vt=STRtree([Point(v['x'],v['y']) for v in h['vias']]);cpraw=A.read(H/'fresh-partial-annular-return-r108-physical-checkpoint.pkl');assert C.sha(cpraw)=='0aa98f5c476d32127623ca1de144bdca4e595527dc90b17db6b075af8a5be803';cp=pickle.loads(cpraw);assert cp['current']['h']['tracks']==h['tracks'] and cp['current']['h']['vias']==h['vias'] and cp['current']['h']['pads']==h['pads'];roots={}
 for q in cur['root']:
  if q['kind']=='via' and q['layer'] in('In1.Cu','In4.Cu'):roots.setdefault(q['uuid'],{})[q['layer']]=q['shape']
 oldreturns=[]
 for v in h['vias']:
  if L.norm(v['net'])!=GND or v['uuid'] not in roots:continue
  areas={l:roots[v['uuid']][l].intersection(cur['source_planes'][l]).area if l in roots[v['uuid']] else 0 for l in('In1.Cu','In4.Cu')}
  if all(x>.004 for x in areas.values()):oldreturns.append({**v,'finite_actual_source_annular_contact_mm2':areas})
 result=[]
 for role,at,padname in [('source',[119.835668,89.798413],('U13001','25')),('target',[131.25,112.35],('U17005','9'))]:
  p=Point(at);pad=next(q for q in h['pads'] if(q['ref'],str(q['num']))==padname);assert L.norm(pad['net'])==NET;errors=[];mins=[]
  for layer in LAYERS:
   dd=[]
   for i in trees[layer].query(p.buffer(1),predicate='intersects'):
    q=rec[layer][int(i)];n=L.norm(q['net'])
    if n==NET:continue
    req=.25+(.15 if domains.get(n)==domains[NET] else .6)+.030;dist=p.distance(q['shape']);dd.append((dist,q['uuid'],q['net'],req))
    if dist<req:errors.append({'kind':'foreign_discrete_Cu','layer':layer,'uuid':q['uuid'],'raw_net':q['net'],'distance_center_to_Cu_mm':dist,'guarded_center_to_Cu_mm':req})
   for z in cur['zones']:
    n=L.norm(z['net'])
    if z['layer']!=layer or n==NET:continue
    req=.25+max(float(z.get('clearance_mm',.15)),.15 if domains.get(n)==domains[NET] else .6)+.030
    if p.distance(z['shape'])<req:errors.append({'kind':'positive_plane_hard','layer':layer,'uuid':z['uuid'],'raw_net':z['net'],'required_center_to_Cu_mm':req})
   for z in g['zones']:
    n=L.norm(z['net'])
    if n==NET or domains.get(n)==domains[NET]:continue
    req=.25+max(float(z.get('clearance_mm',.15)),.6)+.030
    if any(p.distance(sh)<req for sh in L.poly(z['fills'].get(layer,[]))):errors.append({'kind':'cross_domain_original_fill','uuid':z['uuid'],'layer':layer,'raw_net':z['net']})
   for q in h['rule_areas']:
    if layer in q['layers'] and q.get('no_vias') and any(p.distance(sh)<.275 for sh in L.poly(q['outline'])):errors.append({'kind':'native_no_vias','uuid':q['uuid'],'layer':layer})
   for q in reserve['keepouts']:
    if layer in q['layers'] and NET not in exempt.get(q['name'],set()) and any(p.distance(sh)<.275 for sh in L.poly(q['outline'])):errors.append({'kind':'frozen_reservation','name':q['name'],'layer':layer})
   mins.append({'layer':layer,'nearest_foreign_Cu':min(dd) if dd else None})
  ns=smd[int(st.nearest(p))];nh=holes[int(ht.nearest(p))];vi=h['vias'][int(vt.nearest(p))];smdgap=p.distance(ns[3])-.1-.005;drillgap=p.distance(nh[1])-.1-.005;pitch=p.distance(Point(vi['x'],vi['y']))
  if smdgap<.275 or drillgap<.275 or pitch<.815:errors.append({'kind':'ordinary_SMD_drill_pitch','SMD_gap_mm':smdgap,'drill_gap_mm':drillgap,'via_pitch_mm':pitch})
  pairs=[]
  for v in oldreturns:
   dist=math.dist(at,[v['x'],v['y']]);clear=.25+v['d']/2+.15+.030
   if max(.815,clear)<=dist<=1:pairs.append({'new_return':False,'return_UUID':v['uuid'],'return_at_mm':[v['x'],v['y']],'actual_diameter_drill_mm':[v['d'],v['drill']],'actual_flash_layers':v['flashed'],'distance_mm':dist,'finite_source_annular_contact_mm2':v['finite_actual_source_annular_contact_mm2']})
  reg=cp['physical_GND_return_region'].intersection(p.buffer(1,quad_segs=128)).difference(p.buffer(.825,quad_segs=128))
  for q in K.sites(reg,[at[0]+.9,at[1]],10):
   point=Point(q['at_mm']);ann=point.buffer(.25,quad_segs=128).difference(point.buffer(.1,quad_segs=128));areas={l:ann.intersection(cur['source_planes'][l].intersection(point.buffer(1))).area for l in('In1.Cu','In4.Cu')}
   if all(x>.004 for x in areas.values()):pairs.append({'new_return':True,'return_at_mm':q['at_mm'],'actual_diameter_drill_mm':[.5,.2],'conservative_flash_layers':LAYERS,'distance_mm':math.dist(at,q['at_mm']),'finite_source_annular_contact_mm2':areas})
  result.append({'role':role,'exact_native_pad_UUID':pad['uuid'],'source_ref_pin':list(padname),'native_F_pad_centre_mm':[pad['x'],pad['y']],'exact_raw_net':identity.raw(NET),'signal_at_mm':at,'signal_diameter_drill_mm':[.5,.2],'conservative_actual_layer_clearance_scope':LAYERS,'ordinary_signal_errors':errors,'per_layer_foreign_clearance':mins,'SMD_guarded_hole_edge_mm':smdgap,'nearest_SMD':[ns[0],ns[1],ns[2]],'every_hole_guarded_edge_mm':drillgap,'nearest_hole_UUID':nh[0],'ordinary_pitch_mm':pitch,'nearest_via_UUID':vi['uuid'],'finite_real_paired_returns':pairs,'new_return_region_area_mm2':reg.area})
 report={'verdict':'DI15_ACTUAL_ENDPOINT_ORDINARY_SIGNAL_AND_FINITE_RETURN_NOMINATIONS_READY' if all(not q['ordinary_signal_errors'] and q['finite_real_paired_returns'] for q in result) else'DI15_ACTUAL_ENDPOINT_TRANSITION_NOMINATION_INCOMPLETE','current_model_sha256':r['model_sha256'],'R118_receipt_sha256':C.sha(A.read(rp)),'source_parent_sha256':C.sha(source),'endpoints':result,'R108_ordinary_GND_region_exact_discrete_reuse':True,'all_pair_actual_source_after_new_signal_return_holes_reference_contacts_native_SI_current':'OPEN','native_jobs':0,'board_written':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'endpoint_summary':[{'role':q['role'],'errors':q['ordinary_signal_errors'],'returns':q['finite_real_paired_returns']} for q in result]}),flush=True)
if __name__=='__main__':main()
