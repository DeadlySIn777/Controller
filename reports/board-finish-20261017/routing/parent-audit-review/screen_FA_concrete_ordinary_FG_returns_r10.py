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
H=Path(__file__).resolve().parent;ROOT=H.parents[3];P=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';STAGE=ROOT/'reports/board-finish-20261017/combined-route-stage-r4';OUT=H/'FA-concrete-ordinary-FG-return-pair-screen-r10'
T=runpy.run_path(str(H/'triage_reference_current_causal_geometry_r1.py'));norm=T['norm']
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
RETIRE={'f231adb1-b5c9-422a-82eb-c6a859d26a93','21702822-e41c-488c-a23a-db6e3e94614d'};NET='/motherboard_power_entry/FA_SHDN_CONTACT';GROUND='/motherboard_motors/FIELD_GND'
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
 def check(q,ownnet=NET):
  point=Point(q);bad=[];fills=[];near=[]
  for ly,rows in rec.items():
   for index in trees[ly].query(box(q[0]-2,q[1]-2,q[0]+2,q[1]+2)):
    r=rows[int(index)]
    if norm(r['raw_net'])==ownnet:continue
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
  return {'own_net':ownnet,'center_mm':list(q),'hard_discrete_drill_SMD_rule_and_provisional_power_errors':bad,'foreign_actual_fill_footprints_requiring_declared_coupled_cuts_not_accepted':fills,'near_guard_discrete':near,'nearest_SMD_drill_gap_mm':smdgap,'nearest_SMD':[s[0],s[1],s[2]],'nearest_via_center_distance_mm_UUID':list(nearest),'provisional_power_body_gap_mm':pgap}
 # Bind real same-domain named-source ground; no isolated annulus/zone is added.
 OLD=ROOT/'reports/board-finish-20261011/continuation-r2'
 for dd in(OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(dd))
 import R157_native_selected_actual_conversion_r673 as N
 K=N.K;gp=P/'actual-combined-full-after-all-net-groups.pkl';groups=pickle.loads(gp.read_bytes());root=K.root(groups[GROUND],'J11003','2');sourcefloors={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in K.LAYERS};del groups;gc.collect()
 sourcefloorpins={ly:hashlib.sha256(sh.wkb).hexdigest()for ly,sh in sourcefloors.items()}
 centers=[('existing_FA_all6_19ec',(292.95,159.05)),('new_FA_offset_29775',(297.75,155.45)),('new_FA_offset_29770',(297.7,155.5)),('new_FA_offset_29780',(297.8,155.4))]
 output=[]
 for label,q in centers:
  options=[];counts=collections.Counter();examples={}
  for degrees in range(0,360,2):
   ang=math.radians(degrees);r=.95;ret=(round(q[0]+r*math.cos(ang),6),round(q[1]+r*math.sin(ang),6));distance=math.dist(q,ret);assert .9<=distance<1.0
   row=check(ret,GROUND);annulus=Point(ret).buffer(.25,quad_segs=256).difference(Point(ret).buffer(.1,quad_segs=256));contacts={ly:annulus.intersection(floor).area for ly,floor in sourcefloors.items()};row['named_J11003_2_source_actual_fill_annular_positive_contact_mm2']=contacts;row['FA_center_mm']=list(q);row['pair_distance_mm']=distance
   bad=row['hard_discrete_drill_SMD_rule_and_provisional_power_errors'];source_ok=contacts['In1.Cu']>1e-8 and contacts['In4.Cu']>1e-8
   if not bad and source_ok:options.append(row)
   else:
    reason='hard_geometry'if bad else'NO_POSITIVE_ROOTED_FG_CONTACT_ON_BOTH_ADJACENT_PLANES';counts[reason]+=1;examples.setdefault(reason,[])
    if len(examples[reason])<3:examples[reason].append(row)
  options.sort(key=lambda row:(len(row['foreign_actual_fill_footprints_requiring_declared_coupled_cuts_not_accepted']),-min(row['named_J11003_2_source_actual_fill_annular_positive_contact_mm2']['In1.Cu'],row['named_J11003_2_source_actual_fill_annular_positive_contact_mm2']['In4.Cu'])))
  output.append({'label':label,'FA_center_mm':list(q),'FA_geometry_screen':check(q),'qualified_geometry_and_two_actual_rooted_plane_contacts_return_options':len(options),'options':options,'rejections':dict(counts),'representative_rejections':examples})
 put('all-concrete-ordinary-return-pair-options.json',output)
 put('receipt.json',{'status':'CONCRETE_ORDINARY_FG_RETURN_PAIR_GEOMETRY_SOURCE_CONTACT_SCREEN_ONLY','FA_domain':domain,'new_ordinary_via_diameter_mm':.5,'new_ordinary_drill_mm':.2,'same_domain_ground_net':GROUND,'paired_return_window_mm':[.9,1.0],'upper_window_exclusive':True,'screen_radius_mm':.95,'angular_step_degrees':2,'source_root':['J11003','2'],'actual_source_FG_keys':len(K.keys(root)),'source_floor_SHA256':sourcefloorpins,'centers':[{'label':r['label'],'FA_center_mm':r['FA_center_mm'],'return_options':r['qualified_geometry_and_two_actual_rooted_plane_contacts_return_options']}for r in output],'true_transition_scope_full_trace_reference_old_source_keys_partitions_all_oldrefs_all_bank_pours_current_IR_thermal_assembly_masks_native':'OPEN_REQUIRED','no_own_cap_or_zone_or_fabrication_change_added':True,'provisional_wide_power_FG_In1_deficit_mm2_held':3.726668,'foreign_fills_explicitly_held_for_exhaustive_coupled_aperture_and_reference_current_retention_proof':True,'native_jobs':0,'board_or_packet_written':False,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),mf,STAGE/'all-copper-expected.json',T['NPTH'],T['RULES'],POWER/'receipt.json',POWER/'candidate-nominal-track-body.wkb',gp)},'elapsed_seconds':time.monotonic()-t})
 print('RETURN_PAIR_COUNTS',[(r['label'],r['qualified_geometry_and_two_actual_rooted_plane_contacts_return_options'])for r in output],flush=True)
if __name__=='__main__':main()
