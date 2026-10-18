"""Actual full-state source-gain guards and independent native pad partitions.

Runs only after R763. No native jobs, current solve, geometry or mask mutation.
Native and +.025 planning gaps are separate, and nominal curved-pad certainty
is not invented from the exported ERROR_INSIDE polygon.
"""
import os, psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import collections, json, pickle, sys, time
from pathlib import Path
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path('C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261011/continuation-r2/field-power');ROOT=H.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import R157_native_selected_actual_conversion_r673 as N
import audit_R667_actual_three_ground_landing_native_source_contacts_r669 as R
K=N.K;L=N.L;sha=N.sha
P=Path('C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'); BEFORE=Path('C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261011/continuation-r2/field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763')
NF=ROOT/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full'
OUT=Path('C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261017/actual-full-audit-repaired-r1/r767')

def put(name,obj):(OUT/name).write_text(json.dumps(obj,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def save(label,s):
 row=info(s)
 if not s.is_empty:
  path=OUT/(label+'.wkb');path.write_bytes(s.wkb);row['file']=str(path)
 return row

def main():
 assert not OUT.exists();OUT.mkdir();started=time.monotonic()
 pr=json.loads((P/'receipt.json').read_bytes())
 assert sha(P/'actual-combined-full-after-model.pkl')==pr['after_actual_model_SHA256']
 assert sha(P/'actual-combined-full-after-all-net-groups.pkl')==pr['after_actual_groups_SHA256']
 before=pickle.loads((BEFORE/'actual-full-R157-before-model.pkl').read_bytes());after=pickle.loads((P/'actual-combined-full-after-model.pkl').read_bytes())
 og=pickle.loads((BEFORE/'actual-full-R157-before-all-net-groups.pkl').read_bytes());ag=pickle.loads((P/'actual-combined-full-after-all-net-groups.pkl').read_bytes())
 nr=json.loads((NF/'receipt.json').read_bytes());assert sha(NF/'partitions.json')==nr['partitions_SHA256']
 cpp=json.loads((NF/'partitions.json').read_bytes());assert cpp['sha256']==nr['candidate_SHA256'] and cpp['refilled']
 # Labels retain original physical-pad enumeration, including duplicated pins.
 counts=collections.Counter();labels={};label_to_UUID={}
 for pad in after['pads']:
  base=pad['ref']+'.'+str(pad['num']);idx=counts[base];counts[base]+=1;label=base+'#'+str(idx)
  assert label not in label_to_UUID;labels[pad['uuid']]=label;label_to_UUID[label]=pad['uuid']
 cpprows=[];cpperrors=[]
 for net,ref,pin in K.ROOTS:
  rawset={p['net']for p in after['pads']if L.norm(p['net'])==net};assert len(rawset)==1;raw=next(iter(rawset))
  anchor={labels[p['uuid']]for p in after['pads']if(p['ref'],str(p['num']))==(ref,pin)}
  hit=[set(xs)for xs in cpp['nets'][raw]if set(xs)&anchor]
  physical=K.root(ag[net],ref,pin);physical_labels={labels[r['uuid']]for r in physical if r['kind']=='pad'}
  # Do not union different CPP source groups into a fictitious shared source.
  selected=[xs for xs in hit if physical_labels&anchor&xs]
  assert len(selected)==1,('Source anchor ambiguous across actual CPP components',net,anchor)
  native=selected[0];row={'net':net,'source':ref+'.'+pin,'all_actual_anchor_pad_labels':sorted(anchor),
   'CPP_source_group_count_at_all_physical_anchor_sites':len(hit),'CPP_selected_source_pad_count':len(native),
   'drilled_polygon_source_pad_count':len(physical_labels),'CPP_source_pads_absent_drilled_polygon_source':[label for label in sorted(native-physical_labels)],
   'drilled_polygon_source_pads_absent_CPP_source':[label for label in sorted(physical_labels-native)]}
  cpprows.append(row)
  if row['CPP_source_pads_absent_drilled_polygon_source']or row['drilled_polygon_source_pads_absent_CPP_source']:cpperrors.append(row)
 put('nine-source-actual-CPP-versus-drilled-native-pad-partitions.json',cpprows)
 # Every physical source fill is already all-drill-subtracted by R763.
 allfills={ly:[]for ly in K.LAYERS}
 zmeta={z['uuid']:z for z in after['zones']}
 for net,groups in ag.items():
  for xs in groups:
   for row in xs:
    if row['kind']=='fill':allfills[row['layer']].append(row)
 trees={ly:STRtree([r['shape']for r in xs])for ly,xs in allfills.items()}
 discrete,dtrees=K.F.build({**after,'zones':[]})
 domains=after['domains_normalized'];native_errors=[];planner_errors=[];pad_near=[];checks=[];gains=[]
 maxlocal={ly:max([float(zmeta[r['uuid']]['clearance_mm'])for r in xs]+[.6])for ly,xs in allfills.items()}
 for net,ref,pin in K.ROOTS:
  old=K.root(og[net],ref,pin);now=K.root(ag[net],ref,pin)
  oldbody={ly:unary_union([r['shape']for r in old if r['kind']=='fill'and r['layer']==ly])for ly in K.LAYERS}
  for index,row in enumerate(r for r in now if r['kind']=='fill'):
   ly=row['layer'];gain=row['shape'].difference(oldbody[ly]);local=float(zmeta[row['uuid']]['clearance_mm'])
   if gain.is_empty:continue
   gainrow={'net':net,'source':ref+'.'+pin,'zone_UUID':row['uuid'],'layer':ly,'gain':save(net.rsplit('/',1)[-1]+'-'+row['uuid']+'-'+str(index)+'-gain',gain)};gains.append(gainrow)
   query=max(maxlocal[ly],local,.6)+.025+.005+.000001
   for i in trees[ly].query(gain.buffer(query),predicate='intersects'):
    foreign=allfills[ly][int(i)];fn=L.norm(foreign['net'])
    if fn==net:continue
    gap=.15 if domains.get(fn)==domains.get(net)else .6
    required=max(local,float(zmeta[foreign['uuid']]['clearance_mm']),gap);assert required+.025<=query
    distance=gain.distance(foreign['shape']);check={'kind':'ACTUAL_FILLED_CU','source_net':net,'source_zone':row['uuid'],'foreign_net':foreign['net'],'foreign_UUID':foreign['uuid'],'layer':ly,'gap_mm':distance,'native_required_mm':required,'planner_required_mm':required+.025}
    checks.append(check)
    if distance<required:native_errors.append(check)
    if distance<required+.025:planner_errors.append(check)
   for i in dtrees.get(ly,STRtree([])).query(gain.buffer(query),predicate='intersects'):
    foreign=discrete[ly][int(i)];fn=L.norm(foreign['net'])
    if fn==net:continue
    required=max(local,.15 if domains.get(fn)==domains.get(net)else .6)
    if foreign['kind']=='via':
     v=foreign['source'];distance=gain.distance(Point(v['x'],v['y']))-v['d']/2;mode='true actual flashed nominal via circle'
    elif foreign['kind']=='track'and not foreign['source'].get('m'):
     t=foreign['source'];distance=gain.distance(LineString([t['a'],t['b']]))-t['w']/2;mode='true round segment cap and body'
    else:distance=gain.distance(foreign['shape']);mode='actual ERROR_INSIDE pad polygon or exact unchanged graphic'
    check={'kind':'ACTUAL_DISCRETE_'+foreign['kind'],'source_net':net,'source_zone':row['uuid'],'foreign_net':foreign['net'],'foreign_UUID':foreign['uuid'],'layer':ly,'gap_mm':distance,'native_required_mm':required,'planner_required_mm':required+.025,'measurement_mode':mode}
    checks.append(check)
    if distance<required:native_errors.append(check)
    if distance<required+.025:planner_errors.append(check)
    if foreign['kind']=='pad'and distance<required+.005:pad_near.append({**check,'true_nominal_curved_pad_clearance':'OPEN; ERROR_INSIDE polygon does not prove nominal outer boundary'})
  put('checkpoint-source-gain-guard-counts.json',{'finished_source':net,'checks':len(checks),'native_errors':len(native_errors),'planner_errors':len(planner_errors)})
  print('R767',net,len(checks),len(native_errors),len(planner_errors),flush=True)
 put('all-actual-source-gains.json',gains);put('all-actual-source-gain-guard-checks.json',checks)
 put('source-gain-native-clearance-errors.json',native_errors);put('source-gain-extra025-planning-margin-deficits.json',planner_errors)
 put('source-gain-foreign-pad-nominal-boundary-uncertainty.json',pad_near)
 counts={'CPP_vs_drilled_source_partition_mismatches':len(cpperrors),'actual_source_gain_native_guard_errors':len(native_errors),
  'actual_source_gain_extra025_planner_deficits':len(planner_errors),'source_gain_nominal_curved_pad_boundary_open_cases':len(pad_near)}
 files=[Path(__file__),P/'receipt.json',P/'prepare-receipt.json',NF/'receipt.json',NF/'partitions.json',P/'actual-combined-full-after-model.pkl',P/'actual-combined-full-after-all-net-groups.pkl']
 receipt={'status':'ACTUAL_FULL_SOURCE_GAIN_AND_CPP_SCOPED_PASS_OTHER_GATES_OPEN'if not any(counts.values())else'ACTUAL_FULL_SOURCE_GAIN_CPP_RAW_FAILURE_OR_NOMINAL_PAD_UNCERTAINTY_RETAINED',
  'counts':counts,'parent_R763_status':pr['status'],'parent_R763_counts':pr['counts'],'parent_failure_not_promoted':True,
  'actual_before_and_after_are_both_FULL_CPP_fill_states':True,'zero_threshold_Cu_or_line_witnesses_not_waived':True,
  'true_analytic_actual_flashed_via_and_straight_track_caps':True,'nominal_curved_pad_certainty_not_invented':True,
  'native_vs_extra025_planning_requirement_separate':True,'max_local_foreign_own_domain_query_guard_coverage_asserted':True,
  'source_current_barrel_voltage_full_loop_thermal_SI_full_DRC_manufacturing':'OPEN_OR_FAIL_RETAINED',
  'input_SHA256':{str(p):sha(p)for p in files},'native_jobs':0,'source_or_geometry_or_masks_modified':False,'adopted':False,'elapsed_seconds':time.monotonic()-started}
 put('receipt.json',receipt);print('R767_COMPLETE',sha(OUT/'receipt.json'),counts,flush=True)

if __name__=='__main__':main()
