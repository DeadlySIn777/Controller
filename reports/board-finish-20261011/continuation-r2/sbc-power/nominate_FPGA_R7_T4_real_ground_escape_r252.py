"""Full-width F ground joins first, then literal ordinary BGA/outer sites.

The existing public U1001 pad-via .125 rule is separately ledgered. Any
candidate below its .025 added planning reserve stays a diagnostic failure.
"""
import hashlib,json,pickle,sys,math,uuid,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import tri_route as TR
O=H/'sbc-power/FPGA-R7-T4-full-width-real-ground-nominees-r252'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def parts(sh):return[sh]if sh.geom_type=='Polygon'else[p for p in getattr(sh,'geoms',[])if p.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';g,h,b,z,c=pickle.loads(mp.read_bytes());rootp=H/'sbc-power/CORE-R112-exact-ground-cross-layer-topology-r249';assert sha(rootp/'receipt.json')=='754100d0e83334eee6db787757903020ec4fe22058893f2ef4beaa82ebf0a72d';import shapely;refs={l:shapely.from_wkb((rootp/(l+'-exact-drilled-source-ground-union.wkb')).read_bytes())for l in('F.Cu','In1.Cu','In4.Cu')};rec,trees=F.build({**h,'zones':[]});holes=[(v['uuid'],v['net'],GP.bounded_disk(v,v['drill']/2+.00000002))for v in h['vias']]+[(p['uuid'],p['net'],sh.buffer(.00000002))for p in h['pads']for sh in C.poly(p.get('hole')or[])];ht=STRtree([sh for u,n,sh in holes]);smds=[(p,sh)for p in h['pads']if p['smd']for l,rs in p['layers'].items()if l in('F.Cu','B.Cu')for sh in C.poly(rs)];st=STRtree([sh for p,sh in smds]);vp=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vp);accepted=[];attempts=[];diagnostic=[]
 for pin in('T4','R7'):
  pad=next(p for p in h['pads']if(p['ref'],p['num'])==('U1001',pin));assert pad['net']=='/LOGIC_GND';start=[pad['x'],pad['y']];s=Point(start);put(O/(pin+'-source-pad.json'),pad);print('R252_START',pin,start,flush=True)
  for radius in(2.,5.,10.):
   clip=box(s.x-radius,s.y-radius,s.x+radius,s.y+radius);cuts=[]
   for j in trees['F.Cu'].query(clip.buffer(.8),predicate='intersects'):
    q=rec['F.Cu'][int(j)]
    if C.norm(q['net'])=='/LOGIC_GND':continue
    clear=GP.G.gap(h,'/LOGIC_GND',q['net'])+.025+.0000001
    if q['kind']=='track':tt=q['source'];cut=GP.bounded_buffer(LineString([tt['a'],tt['b']]),tt['w']/2+.1+clear)
    elif q['kind']=='via':v=q['source'];cut=GP.bounded_disk(v,v['d']/2+.1+clear)
    else:cut=GP.bounded_buffer(q['shape'],.1+clear)
    cuts.append(cut)
   for q in z:
    if q['layer']=='F.Cu'and C.norm(q['net'])!='/LOGIC_GND'and q['shape'].intersects(clip.buffer(.8)):cuts.append(GP.bounded_buffer(q['shape'],.1+max(q['clearance_mm'],GP.G.gap(h,'/LOGIC_GND',q['net']))+.025+.0000001))
   for j in ht.query(clip.buffer(.8),predicate='intersects'):
    uid,n,hh=holes[int(j)]
    if C.norm(n)!='/LOGIC_GND':cuts.append(GP.bounded_buffer(hh,.1+.275+.0000001))
   for q in h['rule_areas']:
    if q.get('no_tracks')and'F.Cu'in q['layers']:cuts.extend(GP.bounded_buffer(sh,.125)for sh in C.poly(q['outline'])if sh.intersects(clip))
   free=clip.difference(unary_union(cuts));eligible=[p for p in parts(free)if p.covers(s)];goals=[]
   for face in eligible:
    goalbody=face.buffer(-.00000002).intersection(refs['F.Cu'])
    if goalbody.is_empty:continue
    p=nearest_points(s,goalbody)[1];goal=[round(p.x,6),round(p.y,6)]
    if not face.covers(Point(goal)):continue
    try:path,method=TR.route(face,start,goal)
    except Exception as e:attempts.append({'pin':pin,'radius_mm':radius,'kind':'full_width_F_triangle_failure','error':str(e)});continue
    path=[[round(x,6),round(y,6)]for x,y in path];axis=LineString(path)
    if not face.covers(axis):continue
    tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'FPGA-R252:'+pin+':'+str(i))),'net':'/LOGIC_GND','layer':'F.Cu','w':.2,'a':a,'b':bb}for i,(a,bb)in enumerate(zip(path,path[1:]))];row={'pin':pin,'mode':'actual_J1_rooted_F_copper_full_width_join','path':path,'length_mm':axis.length,'tracks':tracks,'no_new_drill_or_native_rule_change':True,'method':method,'full_mutual_contact_actual_pour_native_required':True};accepted.append(row);print('R252_CONCRETE_FULL_WIDTH_GROUND',pin,len(tracks),axis.length,flush=True);break
   else:attempts.append({'pin':pin,'radius_mm':radius,'kind':'no_actual_rooted_F_copper_in_start_free_face','start_faces':len(eligible)});continue
   break
  if any(r['pin']==pin for r in accepted):continue
  # Direct .20 stub + conventional .5/.2 barrel. New barrels retain their
  # effective native and stronger planning verdicts as separate facts.
  for dx,dy in[(a,b)for a in(-.4,0.,.4)for b in(-.4,0.,.4)if a or b]+[(0,y)for y in(.8,1.,1.2,1.5,-.8,-1.,-1.2)]:
   x,y=round(s.x+dx,6),round(s.y+dy,6);p=Point(x,y);v={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'FPGA-R252-ordinary:'+pin+':'+repr((x,y)))),'net':'/LOGIC_GND','x':x,'y':y,'d':.5,'drill':.2,'flashed':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']};errs=[];plan=[];sj=int(st.nearest(p));smdd=p.distance(smds[sj][1])-.1-.005;hj=int(ht.nearest(p));hd=p.distance(holes[hj][2])-.1-.005;vi=int(vt.nearest(p));pitch=p.distance(vp[vi]);axis=LineString([start,[x,y]])
   if smdd<.275:errs.append({'kind':'every_SMD','guarded_mm':smdd,'UUID':smds[sj][0]['uuid']})
   if hd<.275:errs.append({'kind':'every_drill','guarded_mm':hd,'UUID':holes[hj][0]})
   if pitch<.815:errs.append({'kind':'ordinary_pitch','mm':pitch,'UUID':h['vias'][vi]['uuid']})
   for l in v['flashed']:
    for j in trees[l].query(p.buffer(1.0),predicate='intersects'):
     q=rec[l][int(j)]
     if C.norm(q['net'])=='/LOGIC_GND':continue
     bga=q['kind']=='pad'and q['source']['ref']=='U1001';baseclear=.125 if bga else GP.G.gap(h,'/LOGIC_GND',q['net']);req=baseclear+.025
     if q['kind']=='track':tt=q['source'];gap=p.distance(LineString([tt['a'],tt['b']]))-.25-tt['w']/2
     elif q['kind']=='via':vv=q['source'];gap=p.distance(Point(vv['x'],vv['y']))-.25-vv['d']/2
     else:gap=p.distance(q['shape'])-.25
     if gap<baseclear:errs.append({'kind':'new_via_native_effective_Cu','layer':l,'UUID':q['uuid'],'gap_mm':gap,'required_native_mm':baseclear,'existing_U1001_public_pad_via_predicate':bga})
     if gap<req:plan.append({'kind':'new_via_added_planning_reserve','layer':l,'UUID':q['uuid'],'gap_mm':gap,'required_planning_mm':req,'existing_native_rule_min_mm':baseclear})
    if l=='F.Cu':
     for j in trees[l].query(axis.buffer(.8),predicate='intersects'):
      q=rec[l][int(j)]
      if C.norm(q['net'])=='/LOGIC_GND':continue
      if q['kind']=='track':tt=q['source'];gap=axis.distance(LineString([tt['a'],tt['b']]))-.1-tt['w']/2
      elif q['kind']=='via':vv=q['source'];gap=axis.distance(Point(vv['x'],vv['y']))-.1-vv['d']/2
      else:gap=axis.distance(q['shape'])-.1
      if gap<GP.G.gap(h,'/LOGIC_GND',q['net'])+.025:errs.append({'kind':'full_width_F_stub_Cu','UUID':q['uuid'],'gap_mm':gap})
   ann=p.buffer(.25,quad_segs=128).difference(GP.bounded_disk(v,.1));areas={l:ann.intersection(refs[l].buffer(-.075)).area for l in('In1.Cu','In4.Cu')};row={'pin':pin,'via':v,'native_errors':errs,'planning_errors':plan,'guarded_SMD_mm':smdd,'guarded_drill_mm':hd,'via_pitch_mm':pitch,'literal_J1_rooted_inner_finite_annular_interior_mm2':areas,'full_width_stub_points':[start,[x,y]],'native_new_all6_original_foreign_fill_antipads_full_contacts_and_current':'OPEN'};attempts.append(row)
   if not errs:diagnostic.append(row)
 put(O/'attempts.json',attempts);put(O/'diagnostic-only-literal-native-BGA-sites.json',diagnostic);(O/'proposed-discrete.pkl').write_bytes(pickle.dumps({'tracks':[t for r in accepted for t in r['tracks']],'vias':[]},protocol=5));put(O/'receipt.json',{'verdict':'CONCRETE_FULL_WIDTH_REAL_GROUND_JOINS_PENDING_FULL_CONTACT_NATIVE'if accepted else'NO_FULL_WIDTH_GROUND_JOIN_IN_DECLARED_WINDOWS_LITERAL_SITE_DIAGNOSTICS_PRESERVED','exact_R112_model_sha256':sha(mp),'exact_R249_ground_scope_sha256':sha(rootp/'receipt.json'),'ordinary_native_U1001_pad_via_rule_original_DRU_sha256':sha(H/'sbc-native-contract-r1/copy/board.kicad_dru'),'accepted_geometry_nominees':accepted,'literal_native_effective_sites_not_adopted':len(diagnostic),'all_planning_reserve_failures_visible_and_unwaived':True,'no_pad_source_oldtrack_via_zone_or_rule_mutation':True,'full_CORE0p8_IO3_2A_retained':True,'all_mutual_oldcontact_source_sharedreturn_native_and_current_gates':'OPEN','board_written':False,'native_jobs':0,'script_sha256':sha(__file__)});print('R252_COMPLETE',len(accepted),len(diagnostic),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
