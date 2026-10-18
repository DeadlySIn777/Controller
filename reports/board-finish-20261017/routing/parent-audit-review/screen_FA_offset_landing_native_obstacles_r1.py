"""Bounded all-layer ordinary FA landing triage; no board/native fill produced."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time,runpy,math,collections,gc
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon,box
from shapely import from_wkb
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent;ROOT=H.parents[3];P=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';STAGE=ROOT/'reports/board-finish-20261017/combined-route-stage-r4';OUT=H/'FA-offset-landing-native-obstacle-screen-r1'
T=runpy.run_path(str(H/'triage_reference_current_causal_geometry_r1.py'));norm=T['norm']
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
RETIRE={'f231adb1-b5c9-422a-82eb-c6a859d26a93','21702822-e41c-488c-a23a-db6e3e94614d'};NET='/motherboard_power_entry/FA_SHDN_CONTACT'
CENTERS=[(297.25,155.65),(297.65,155.35),(297.8,155.3),(298.0,155.0),(297.55,155.2)]
POWER=ROOT/'reports/board-finish-20261017/power-review/field5-current-continuation/F-parallel-offset-FA-landing-refined-r10'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 t=time.monotonic();assert not OUT.exists();OUT.mkdir();mf=P/'actual-combined-full-after-model.pkl';h=pickle.loads(mf.read_bytes());expected=json.loads((STAGE/'all-copper-expected.json').read_bytes());ex=expected['copper'];dom=h['domains_normalized'];domain=dom[NET]
 # Bind current sparse ordinary primitives, preserve cached genuine native pads,
 # fills and flash masks; new primitive all6 flash assumptions are conservative.
 tracks=[r for r in h['tracks']if r['uuid']in ex and r['uuid']not in RETIRE];vias=[r for r in h['vias']if r['uuid']in ex];oldids={r['uuid']for r in tracks+vias}|RETIRE
 for uid,row in ex.items():
  if uid in oldids:continue
  if row['kind']=='segment':tracks.append({'uuid':uid,'net':row['raw_net'],'layer':row['layer'],'w':row['width_IU']/1e6,'a':[v/1e6 for v in row['start_IU']],'b':[v/1e6 for v in row['end_IU']]})
  elif row['kind']=='via':
   ds=set(row['diameters_IU'].values());assert len(ds)==1;vias.append({'uuid':uid,'net':row['raw_net'],'x':row['at_IU'][0]/1e6,'y':row['at_IU'][1]/1e6,'d':next(iter(ds))/1e6,'drill':row['drill_IU']/1e6,'flashed':list(row['diameters_IU'])})
  else:raise AssertionError(('Unhandled new primitive',uid,row['kind']))
 h={**h,'tracks':tracks,'vias':vias};npth=json.loads(T['NPTH'].read_bytes());nocu={r['UUID']for r in npth if r['IsNPTHWithNoCopper']and not any(l['CanFlashLayer']or l['FlashLayer']for l in r['layer_observations'])};rec,trees=T['build'](h,nocu)
 groundoptions=[n for n in('/LOGIC_GND','/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V')if dom[n]==domain]
 rules=json.loads(T['RULES'].read_bytes());rulepolys=[(r,Polygon([(x/1e6,y/1e6)for x,y in p['outer_IU']], [[(x/1e6,y/1e6)for x,y in ring]for ring in p['holes_IU']]))for r in rules for p in r['outlines']]
 smd=[(p['uuid'],p['ref'],str(p['num']),sh)for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for sh in T['polys'](rs)];smdtree=STRtree([r[3]for r in smd])
 holes=[(v['uuid'],'via',Point(v['x'],v['y']),v['drill']/2)for v in vias]+[(p['uuid'],'pad_hole',sh,0)for p in h['pads']for sh in T['polys'](p.get('hole')or[])];holetree=STRtree([r[2]for r in holes]);body=from_wkb((POWER/'candidate-nominal-track-body.wkb').read_bytes());powernet=norm(next(v['net']for v in vias if v['uuid'].startswith('0901cf4a')))
 def required(other):return .175 if dom.get(norm(other))==domain else .625
 def check(q):
  point=Point(q);bad=[];fills=[];near=[]
  for ly,rows in rec.items():
   for index in trees[ly].query(box(q[0]-2,q[1]-2,q[0]+2,q[1]+2)):
    r=rows[int(index)]
    if norm(r['raw_net'])==NET:continue
    gap=point.distance(r['shape'])-r['radius']-.25-(.005 if r['kind']=='pad'else 0);req=max(required(r['raw_net']),float(r['data'].get('clearance_mm',0))+.025)
    row={'layer':ly,'kind':r['kind'],'UUID':r['UUID'],'raw_net':r['raw_net'],'gap_mm':gap,'guarded_requirement_mm':req}
    if gap<req:(fills if r['kind']=='fill'else bad).append(row)
    elif gap<req+.1:near.append(row)
  s=smd[int(smdtree.nearest(point))];smdgap=point.distance(s[3])-.1-.005
  if smdgap<.275:bad.append({'kind':'ordinary_new_drill_to_SMD','UUID':s[0],'ref':s[1],'pin':s[2],'gap_mm':smdgap,'requirement_mm':.275})
  ds=[]
  for index in holetree.query(point.buffer(.8)):
   u,k,sh,r=holes[int(index)];gap=point.distance(sh)-r-.1-.005
   if gap<.275:bad.append({'kind':'ordinary_new_drill_to_every_hole','UUID':u,'hole_kind':k,'gap_mm':gap,'requirement_mm':.275})
  nearest=min((math.hypot(q[0]-v['x'],q[1]-v['y']),v['uuid'])for v in vias)
  if nearest[0]<.815:bad.append({'kind':'ordinary_new_via_pitch','nearest_UUID':nearest[1],'center_distance_mm':nearest[0],'requirement_mm':.815})
  for r,sh in rulepolys:
   if r['GetDoNotAllowVias']and point.distance(sh)<.275:bad.append({'kind':'actual109_native_no_via_rule','UUID':r['UUID'],'name':r['name'],'all_rule_layers':r['layers'],'gap_mm':point.distance(sh)-.25,'required_guard_mm':.025})
  pgap=point.distance(body)-.25;preq=required(powernet)
  if pgap<preq:bad.append({'kind':'provisional_wide_FIELD5_F_power_body','raw_net':powernet,'gap_mm':pgap,'requirement_mm':preq})
  return {'center_mm':list(q),'hard_discrete_drill_SMD_rule_and_provisional_power_errors':bad,'foreign_actual_fill_footprints_requiring_declared_coupled_cuts_not_accepted':fills,'near_guard_discrete':near,'nearest_SMD_drill_gap_mm':smdgap,'nearest_SMD':[s[0],s[1],s[2]],'nearest_via_center_distance_mm_UUID':list(nearest),'provisional_power_body_gap_mm':pgap}
 observations=[check(q)for q in CENTERS];put('five-named-centers.json',observations)
 # The route screen is strict to immutable current foreign Cu. A later qualified
 # route may need bounded owned plane cuts with every reference/current gate held.
 port=next(v for v in vias if v['uuid'].startswith('19ec6624'));routes=[]
 for q in CENTERS:
  axis=LineString([(port['x'],port['y']),q]);bad=[]
  for index in trees['In3.Cu'].query(axis.buffer(.9)):
   r=rec['In3.Cu'][int(index)]
   if norm(r['raw_net'])==NET:continue
   gap=axis.distance(r['shape'])-r['radius']-.1-(.005 if r['kind']=='pad'else 0);req=max(required(r['raw_net']),float(r['data'].get('clearance_mm',0))+.025)
   if gap<req:bad.append({'kind':r['kind'],'UUID':r['UUID'],'raw_net':r['raw_net'],'gap_mm':gap,'guarded_requirement_mm':req})
  routes.append({'center_mm':list(q),'old_FA_port_UUID':port['uuid'],'straight_In3_foreign_Cu_conflicts':bad,'ordinary_pair_window_existing_same_domain_candidates':[{'UUID':v['uuid'],'raw_net':v['net'],'at_mm':[v['x'],v['y']],'distance_mm':math.hypot(q[0]-v['x'],q[1]-v['y']),'d_mm':v['d'],'drill_mm':v['drill'],'flashed':v['flashed'],'source_root_and_transition_floor_not_yet_credited':True}for v in vias if norm(v['net'])in groundoptions and .9<=math.hypot(q[0]-v['x'],q[1]-v['y'])<1.]})
 put('five-named-In3-axis-and-existing-paired-return-screen.json',routes)
 good=[]
 for ix in range(21):
  for iy in range(17):
   q=(round(297.25+ix*.05,6),round(154.8+iy*.05,6));row=check(q)
   if not row['hard_discrete_drill_SMD_rule_and_provisional_power_errors']:good.append(row)
 put('all-hard-geometry-clear-grid-landings-50um.json',good)
 put('receipt.json',{'status':'BOUNDED_ORDINARY_FA_LANDING_DISCRETE_DRILL_RULE_POWER_SCREEN_NO_REFERENCE_OR_NATIVE_PASS','FA_domain':domain,'same_domain_ground_options':groundoptions,'wide_power_raw_net':powernet,'named_center_count':len(observations),'grid_pitch_mm':.05,'grid_points':357,'hard_geometry_clear_grid_landings':len(good),'all_actual_foreign_fill_cuts_current_source_keys_partitions_oldrefs_and_old_FA_In3_floor':'OPEN_NOT_CREDITED','same_domain_existing_return_vias_0_9_inclusive_1_0_exclusive':'Candidates only; old rooted source contacts/layer entries and each true transition scope must be independently bound','no_rule_or_clearance_or_reference_scope_weakened':True,'native_jobs':0,'candidate_or_board_written':False,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),mf,STAGE/'all-copper-expected.json',T['NPTH'],T['RULES'],POWER/'receipt.json',POWER/'candidate-nominal-track-body.wkb')},'elapsed_seconds':time.monotonic()-t})
 print('FA_LANDING_SCREEN_DONE',len(good),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
