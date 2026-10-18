"""Finite actual-Cu legal axis faces beside both retained signal barrels."""
import hashlib,json,math,pickle,re,sys
from pathlib import Path
from shapely.geometry import Point,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'U10003-exact-actual-paired-return-legal-faces-r164';NET='/motherboard_motors/FIELD_GND'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']
def main():
 assert not OUT.exists();OUT.mkdir()
 mp=H/'U10003-sparse-current-ground-fault-construction-r153/model.pkl';assert sha(mp)=='2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8'
 g,h,b,z,full=pickle.loads(mp.read_bytes());ports=json.loads((H/'U10003-unqualified-physical-fault-detour-r130/receipt.json').read_bytes())['repair']['existing_native_barrels']
 print('R164_BUILD_ACTUAL_HARD_CU',flush=True);records,trees=F.build({**h,'zones':[]})
 _,groups=K.physical(full,NET,K.hole_context(full));root=K.root(groups,'J11003','2')
 refs={l:unary_union([r['shape']for r in root if r['layer']==l and r['kind']=='fill'])for l in ('In1.Cu','In4.Cu')}
 footprints=next(f for f in h['footprints']if f['ref']=='U10003');court=unary_union([s for rs in footprints['courtyard'].values()for s in C.poly(rs)])
 reserved=C.BASE/'recovery-composite/c06/alternate-r07';areas=json.loads((reserved/'reserved-r07.json').read_bytes())['keepouts'];dru=(reserved/'reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n)for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 rows=[];allcandidates=[]
 for port in ports:
  pt=Point(port['x'],port['y']);window=pt.buffer(1.35,quad_segs=256);cuts=[];ledger=[]
  def add(sh,radius,kind,uid,**details):
   if sh.distance(window)>radius:return
   cut=N.bounded_buffer(sh.intersection(window.buffer(radius+1)),radius)
   if not cut.intersects(window):return
   cuts.append(cut);ledger.append({'kind':kind,'UUID':uid,'axis_guard_radius_mm':radius,'WKB_sha256':hashlib.sha256(cut.wkb).hexdigest(),**details})
  for layer in h['copper_layers']:
   for j in trees[layer].query(window.buffer(.9),predicate='intersects'):
    q=records[layer][int(j)];other=C.norm(q['net'])
    if other==NET:continue
    gap=(.15 if h['domains_normalized'][other]==h['domains_normalized'][NET]else.6)+.025+.000020
    add(q['shape'],.25+gap,q['kind'],q['uuid'],layer=layer,raw_net=q['net'])
  for q in z:
   other=C.norm(q['net'])
   if other==NET:continue
   gap=max(.15 if h['domains_normalized'][other]==h['domains_normalized'][NET]else.6,float(q.get('clearance_mm',.15)))+.025+.000020
   add(q['shape'],.25+gap,'CURRENT_OWNED_POSITIVE',q['uuid'],layer=q['layer'],raw_net=q['net'])
  for p in h['pads']:
   for sh in C.poly(p.get('hole')or[]):add(sh,.1+.275+.000020,'ACTUAL_PAD_HOLE',p['uuid'])
   if p['smd']:
    for l,rs in p['layers'].items():
     for sh in C.poly(rs):add(sh,.1+.275+.000020,'ACTUAL_SMD_HOLE_GUARD',p['uuid'],ref=p['ref'],pin=p['num'],layer=l)
  for v in h['vias']:add(Point(v['x'],v['y']),(.2+v['drill'])/2+.275+.000020,'ACTUAL_EVERY_DRILL_PITCH',v['uuid'])
  for a in h['rule_areas']:
   if a['no_vias']:
    for sh in C.poly(a['outline']):add(sh,.25+.025,'ACTUAL_NATIVE_NO_VIAS',a['uuid'])
  for a in areas:
   if NET not in exceptions.get(a['name'],set()):
    for sh in C.poly(a['outline']):add(sh,.25+.025,'ROUTER_RESERVATION',a['name'])
  add(court,.25+.025,'LITERAL_U10003_COURTYARD','U10003')
  # Same-domain original fills may retreat through normal priority filling;
  # other-domain actual planes remain hard on every Cu layer.
  for q in full['zones']:
   other=C.norm(q['net'])
   if other==NET or h['domains_normalized'][other]==h['domains_normalized'][NET]:continue
   for layer,rr in q['fills'].items():
    for sh in C.poly(rr):add(sh,.25+max(.6,float(q['clearance_mm']))+.025+.000020,'OTHER_DOMAIN_ACTUAL_NATIVE_FILL',q['uuid'],layer=layer,raw_net=q['net'])
  legal=window.difference(unary_union(cuts));near=legal.intersection(pt.buffer(.95,quad_segs=256));candidates=[]
  for poly in polys(near):
   core=poly.buffer(-.0001);site=(core if not core.is_empty else poly).representative_point();xy=[round(site.x,6),round(site.y,6)];site=Point(xy)
   if not legal.covers(site):continue
   ann=site.buffer(.25,quad_segs=256).difference(site.buffer(.1,quad_segs=256))
   row={'signal_UUID':port['uuid'],'site_mm':xy,'signal_distance_mm':site.distance(pt),'literal_axis_clearance_to_all_obstacle_union_mm':site.distance(unary_union(cuts)),'current_drilled_J11003_source_fill_annuli_mm2':{l:ann.intersection(sh).area for l,sh in refs.items()},'new_source_plane_extension_and_negative_same_domain_original_fill_gates':'OPEN'};candidates.append(row);allcandidates.append(row)
  (OUT/(port['uuid']+'-legal.wkb')).write_bytes(legal.wkb);put(OUT/(port['uuid']+'-actual-obstacle-ledger.json'),ledger)
  rows.append({'signal_UUID':port['uuid'],'signal_at_mm':[port['x'],port['y']],'finite_window_radius_mm':1.35,'paired_candidate_max_radius_mm':.95,'exact_legal_axis_area_mm2':legal.area,'near_axis_area_mm2':near.area,'minimum_finite_legal_axis_distance_mm':legal.distance(pt)if not legal.is_empty else None,'near_nominees':candidates,'actual_obstacle_count':len(ledger)})
  print('R164_PORT',json.dumps(rows[-1]),flush=True)
 result={'verdict':'FINITE_EXACT_TRUE_CU_PAIRED_RETURN_FACE_NOMINATION_ONLY','model_sha256':sha(mp),'rows':rows,'nominees':allcandidates,'original_or_new_Cu_deleted':False,'physical_geometry_changed':False,'source_reference_current_native_all6_full_DRC_gates':'OPEN','native_jobs':0,'adopted':False,'manufacturing_ready':False}
 put(OUT/'receipt.json',result);print('R164_RECEIPT',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
