"""Bounded source/host tests: no imports of numpy/cv2/scipy/shapely or raster/native planning."""
import argparse
import ast
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
sys.dont_write_bytecode=True
import field_current_guard as G
HERE=Path(__file__).resolve().parent
SPEC=HERE.parent/'constraint-snapshot/0-field_pdn_spec.json'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_spec():return json.loads(SPEC.read_bytes())
def partial():
 spec=load_spec();rail=next(r for r in spec['rails'] if r['id']=='FAG')
 rail['clusters']=[c for c in rail['clusters'] if c['name'].startswith('JD01 ')]
 rail['qualification_scope']={'kind':'PARTIAL_DOCUMENTED_CLUSTER_SET','description':'Original JD01 0.096 A cluster only; not whole FIELD_A rail'}
 spec['rails']=[rail];return spec,rail
def valid_partial_design():
 return {'current_model':{'source_and_positive_load_pads_resolved':True,'source_local_load_a':0.0},
  'current_reaching_source_a':.096,'unreached':[],
  'via_groups':[{'amps':.096,'n':1,'n_req':1},{'amps':.096,'n':1,'n_req':1}],
  'segments':[{'width_mm':.3,'w_ipc10C_mm_raw':.02}], 'worst_drop_v':.001,'worst_drop_v_raw':.001}
def parsed_classes(path):
 tree=ast.parse(Path(path).read_text());return tree,next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Designer')
class Controls(unittest.TestCase):
 def test_real_four_documented_totals_rejected_without_reductions(self):
  spec=load_spec();before=copy.deepcopy(spec)
  with self.assertRaises(G.CurrentModelError) as raised:G.validate_spec(spec)
  self.assertEqual(spec,before)
  totals={rid:r['documented_cluster_sum_a'] for rid,r in raised.exception.report['rails'].items()}
  for rid,want in {'FA':5.036,'FAG':5.268,'FB':6.55,'FBG':6.61}.items():self.assertAlmostEqual(totals[rid],want,places=12)
  self.assertTrue(all(not r['model_consistent'] and not r['full_rail_qualified'] for r in raised.exception.report['rails'].values()))
  self.assertFalse(raised.exception.report['loads_modified']);self.assertFalse(raised.exception.report['concurrency_assumptions_added'])
 def test_source_limit_inconsistency_is_independent_of_design_limit(self):
  spec,r=partial();r['design_a']=.2;r['limit_a']=.05
  with self.assertRaises(G.CurrentModelError) as raised:G.validate_spec(spec)
  self.assertIn('FAG:design_a_exceeds_source_limit_a',raised.exception.report['reasons'])
  self.assertIn('FAG:documented_load_sum_exceeds_source_limit_a',raised.exception.report['reasons'])
 def test_real_3_05A_five_arrays_fail_and_seven_pass(self):
  p=Path('Z:/pcb-runs/claude-finish/agent-work/field-pdn/testA3/w/design/design.json')
  document=json.loads(p.read_bytes());rows=[v for r in document['nets'].values() for v in r['via_groups'] if abs((v.get('amps') or 0)-3.05)<.001]
  self.assertEqual(len(rows),2)
  for row in rows:
   self.assertEqual((row['amps'],row['n'],row['n_req'],row['ok']),(3.05,5,7,False))
   five=G.array_status(row['amps'],row['n'],.5,row['n_req']);seven=G.array_status(row['amps'],7,.5,7)
   self.assertFalse(five['qualified_for_modeled_current']);self.assertEqual(five['actual_amps_per_via'],.61)
   self.assertTrue(seven['qualified_for_modeled_current']);self.assertFalse(seven['full_rail_qualified'])
 def test_no_current_rounding_or_epsilon_can_hide_extra_via(self):
  self.assertEqual(G.required_vias(.5,.5),1);self.assertEqual(G.required_vias(.5000000001,.5),2)
  self.assertEqual(G.required_vias(3.05,.5),7);self.assertEqual(G.required_vias(.096,.5),1)
 def test_array_claimed_count_cannot_lie_or_be_missing(self):
  for req in (5,None,True,7.0):
   with self.subTest(required=req):self.assertFalse(G.array_status(3.05,7,.5,req)['qualified_for_modeled_current'])
 def test_partial_0096A_is_model_valid_but_never_full_rail_qualified(self):
  spec,rail=partial();report=G.validate_spec(spec);q=G.modeled_route_status(rail,valid_partial_design(),spec)
  self.assertAlmostEqual(report['rails']['FAG']['documented_cluster_sum_a'],.096)
  self.assertTrue(q['qualified_for_explicit_modeled_route_current']);self.assertFalse(q['full_rail_qualified'])
  self.assertEqual(G.route_output({'FAG':q}),'routes.json')
 def test_missing_positive_pad_and_source_current_are_not_zeroed_away(self):
  spec,r=partial()
  for case in ('pad','source','overcount','unreached'):
   with self.subTest(case=case):
    d=valid_partial_design()
    if case=='pad':d['current_model']['source_and_positive_load_pads_resolved']=False
    if case=='source':d['current_reaching_source_a']=0
    if case=='overcount':d['current_reaching_source_a']=.192
    if case=='unreached':d['unreached']=[{'amps':.096}]
    q=G.modeled_route_status(r,d,spec);self.assertFalse(q['qualified_for_explicit_modeled_route_current'])
    self.assertEqual(G.route_output({'FAG':q}),'routes_UNQUALIFIED_DO_NOT_APPLY.json')
 def test_undersized_arrays_ipc_neck_and_drop_fail_routes(self):
  spec,r=partial()
  for case in ('arrays','count','width','drop','missingdrop'):
   with self.subTest(case=case):
    d=valid_partial_design()
    if case=='arrays':d['via_groups']=[]
    if case=='count':d['via_groups'][0]['n']=0
    if case=='width':d['segments'][0]['w_ipc10C_mm_raw']=.301
    if case=='drop':d['worst_drop_v_raw']=spec['drop_budget_v']+.001
    if case=='missingdrop':d['worst_drop_v_raw']=None
    q=G.modeled_route_status(r,d,spec);self.assertFalse(q['qualified_for_explicit_modeled_route_current'])
    self.assertEqual(G.route_output({'FAG':q}),'routes_UNQUALIFIED_DO_NOT_APPLY.json')
 def test_whatif_never_emits_applicable_routes(self):
  spec,r=partial();q=G.modeled_route_status(r,valid_partial_design(),spec)
  self.assertEqual(G.route_output({'FAG':q},True),'routes_PROPOSAL_DO_NOT_APPLY.json')
  self.assertEqual(G.route_output({}),'routes_UNQUALIFIED_DO_NOT_APPLY.json')
 def test_partial_scope_must_be_explicit_before_applicable_filename(self):
  spec,r=partial();r.pop('qualification_scope')
  q=G.modeled_route_status(r,valid_partial_design(),spec)
  self.assertFalse(q['qualified_for_explicit_modeled_route_current']);self.assertFalse(q['full_rail_qualified'])
  self.assertEqual(G.route_output({'FAG':q}),'routes_UNQUALIFIED_DO_NOT_APPLY.json')
 def test_invalid_current_identity_capacity_inputs(self):
  for value in (-1,float('nan'),float('inf'),True,'3.05'):
   with self.subTest(value=str(value)):
    with self.assertRaises(ValueError):G.required_vias(value,.5)
  for capacity in (0,-1,True,float('nan')):
   with self.subTest(capacity=str(capacity)):
    with self.assertRaises(ValueError):G.required_vias(.096,capacity)
  for only in ('NOT_A_RAIL','FAG,FAG','FAG,'):
   with self.subTest(only=only):
    with self.assertRaises(ValueError):G.validate_spec(partial()[0],only)
 def test_actual_patched_main_rejects_before_geom_build_or_route_emit(self):
  tree,_=parsed_classes(HERE/'field_pdn_design.py');main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  ns={'argparse':argparse,'os':os,'json':json,'ZERO_BRANCH_MM':60.,'CurrentModelError':G.CurrentModelError,
      'validate_spec':G.validate_spec,'log':Mock(),'Designer':Mock(),'text_fallbacks':Mock()}
  exec(compile(ast.Module(body=[main],type_ignores=[]),'isolated-main','exec'),ns)
  with tempfile.TemporaryDirectory() as temp,patch.object(sys,'argv',['field','--geom','NEVER_READ','--partitions','NEVER_READ','--work',temp,'--spec',str(SPEC)]):
   with self.assertRaises(SystemExit) as raised:ns['main']()
   self.assertEqual(raised.exception.code,3);ns['Designer'].assert_not_called();ns['text_fallbacks'].assert_not_called()
   files=list(Path(temp).iterdir());self.assertEqual([p.name for p in files],['field-current-preflight.json'])
   self.assertEqual(json.loads(files[0].read_bytes())['verdict'],'REJECT_LOAD_SOURCE_INCONSISTENCY')
 def test_constructor_also_rejects_before_any_geometry_access(self):
  _,cls=parsed_classes(HERE/'field_pdn_design.py');init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
  ns={'validate_spec':G.validate_spec};exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='D',bases=[],keywords=[],body=[init],decorator_list=[])],type_ignores=[])),'isolated-constructor','exec'),ns)
  with self.assertRaises(G.CurrentModelError):ns['D']({}, {},load_spec(),type('A',(),{'only':''})())
 def test_actual_write_never_names_failed_array_applicable_routes(self):
  tree,cls=parsed_classes(HERE/'field_pdn_design.py');write=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='write')
  constants=[n for n in tree.body if isinstance(n,ast.Assign)]
  ns={'math':math,'os':os,'json':json,'time':time,'via_r':lambda dz:.001,'log':Mock(),
      'modeled_route_status':G.modeled_route_status,'route_output':G.route_output}
  # The unchanged scalar assignments are safe; no geometry/scipy/cv2 module is imported.
  exec(compile(ast.Module(body=constants+[write],type_ignores=[]),'isolated-write','exec'),ns)
  spec,r=partial();d=valid_partial_design()
  d['segments'][0].update({'len_mm':1.,'rise_C':1.});d['via_groups'][0].update({'ok':False,'n':0})
  d['via_groups'][1]['ok']=True
  with tempfile.TemporaryDirectory() as temp:
   obj=type('D',(),{})();obj.a=type('A',(),{'work':temp})();obj.design={'nets':{'FAG':d}}
   obj.analysis={};obj.spec=spec;obj.rail={'FAG':r};obj.pool=[];obj.out_tracks=[];obj.out_vias=[]
   obj.via_d=.6;obj.via_drill=.3;obj.amps_per_via=.5;obj.res_ok=True;obj.n_barrier=0;obj.dz_to_in3=lambda:.001
   ns['write'](obj)
   self.assertFalse((Path(temp)/'routes.json').exists())
   routes=json.loads((Path(temp)/'routes_UNQUALIFIED_DO_NOT_APPLY.json').read_bytes())
   self.assertTrue(routes['failures']);self.assertFalse(routes['full_rail_qualified'])
   self.assertFalse(routes['current_qualification']['FAG']['qualified_for_explicit_modeled_route_current'])
 def test_main_refuses_stale_applicable_routes_without_overwrite(self):
  tree,_=parsed_classes(HERE/'field_pdn_design.py');main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  ns={'argparse':argparse,'os':os,'json':json,'ZERO_BRANCH_MM':60.}
  exec(compile(ast.Module(body=[main],type_ignores=[]),'isolated-main','exec'),ns)
  with tempfile.TemporaryDirectory() as temp,patch.object(sys,'argv',['field','--geom','NEVER_READ','--partitions','NEVER_READ','--work',temp]):
   p=Path(temp)/'routes.json';p.write_bytes(b'{"host_control_sentinel":true}');before=digest(p)
   with self.assertRaisesRegex(SystemExit,'fresh work'):ns['main']()
   self.assertEqual(digest(p),before);self.assertEqual([x.name for x in Path(temp).iterdir()],['routes.json'])
 def test_main_refuses_any_nonempty_work_before_reading_inputs(self):
  tree,_=parsed_classes(HERE/'field_pdn_design.py');main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  ns={'argparse':argparse,'os':os,'json':json,'ZERO_BRANCH_MM':60.}
  exec(compile(ast.Module(body=[main],type_ignores=[]),'isolated-main','exec'),ns)
  with tempfile.TemporaryDirectory() as temp,patch.object(sys,'argv',['field','--geom','NEVER_READ','--partitions','NEVER_READ','--work',temp]):
   p=Path(temp)/'old-report.json';p.write_bytes(b'{"host_control_sentinel":true}');before=digest(p)
   with self.assertRaisesRegex(SystemExit,'Nonempty'):ns['main']()
   self.assertEqual(digest(p),before);self.assertEqual([x.name for x in Path(temp).iterdir()],['old-report.json'])
 def test_each_actual_requested_source_and_positive_cluster_selector_must_resolve(self):
  _,cls=parsed_classes(HERE/'field_pdn_design.py')
  resolve=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='resolve')
  design=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='design_net')
  model=next(n.value for n in ast.walk(design) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=="des['current_model']")
  ns={};exec(compile(ast.Module(body=[resolve],type_ignores=[]),'original-resolve-semantics','exec'),ns)
  obj=type('D',(),{})();obj.isl={'FAG':{'pad_group':{'SRC.1':0,'LOAD.1':1}}};obj.resolve=lambda r,s:ns['resolve'](obj,r,s)
  obj.current_preflight={'rails':{'FAG':{}}}
  for kind in ('complete','missing_source','missing_cluster','wildcard'):
   with self.subTest(kind=kind):
    r={'id':'FAG','source':{'pads':[['SRC','1']]}}
    c={'amps':.096,'pads':[['LOAD','1']],'pad_names':['LOAD.1']}
    if kind=='missing_source':r['source']['pads'].append(['SRC','2'])
    if kind=='missing_cluster':c['pads'].append(['LOAD','2'])
    if kind=='wildcard':c['pads']=[['LOAD','*']]
    evaluated=eval(compile(ast.Expression(model),'actual-selector-contract','eval'),{'self':obj,'r':r,'rid':'FAG','src_pads':['SRC.1'],'clusters':[c]})
    self.assertEqual(evaluated['source_and_positive_load_pads_resolved'],kind in ('complete','wildcard'))
 def test_raw_drop_rejects_rounding_hidden_over_actual_budget(self):
  spec,r=partial();budget=spec['drop_budget_v'];actual=budget+.00004
  d=valid_partial_design();d.update({'worst_drop_v':budget,'worst_drop_v_raw':actual})
  q=G.modeled_route_status(r,d,spec);self.assertFalse(q['qualified_for_explicit_modeled_route_current'])
  self.assertIn('missing_or_exceeded_existing_drop_budget',q['reasons'])
  _,cls=parsed_classes(HERE/'field_pdn_design.py');drops=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='drops')
  ns={'via_r':lambda dz:0.,'RST':1.};exec(compile(ast.Module(body=[drops],type_ignores=[]),'actual-drop-record','exec'),ns)
  obj=type('D',(),{'dz_to_in3':lambda self:.001})();segs=[{'amps':actual,'len':1.,'w':1.}]
  ct={'entry':0,'root':{'vias':[[0,0]],'amps':actual},'paths':[{'amps':actual,'island':1}],
      'join':[(-1,None)],'seg_by_path':{0:[0]},'vgroups':[{}, {'vias':[[1,0]],'name':'load'}],'C':1}
  record=ns['drops'](obj,segs,[ct],{}, {},0)[0]
  self.assertEqual(record['drop_v'],budget);self.assertEqual(record['drop_v_raw'],actual)
 def test_actual_raw_downstream_assignments_preserve_over_design_current(self):
  _,cls=parsed_classes(HERE/'field_pdn_design.py');design=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='design_net')
  assignments=[n for n in ast.walk(design) if isinstance(n,ast.Assign)]
  wanted=['I_C','vg[\'amps\']','ct[\'root\'][\'amps\']','des[\'current_reaching_source_a\']']
  selected={ast.unparse(n.targets[0]):n.value for n in assignments if ast.unparse(n.targets[0]) in wanted}
  self.assertEqual(set(selected),set(wanted))
  ns={'math':math,'down':{1:3.05,2:2.218},'tg':[1,2],'down_eff':{0:5.268,1:5.268},'vg':{'island':1},'ct':{'paths':[{'amps':3.05},{'amps':2.218}]},'src_gi':0,'g_amps':{0:0},'r':{'design_a':4.58}}
  for name,expr in selected.items():self.assertAlmostEqual(eval(compile(ast.Expression(expr),'actual-unclipped-expression','eval'),ns),5.268)
 def test_geometry_capacity_constants_and_unmodified_masks_are_exact(self):
  old,oldcls=parsed_classes(HERE/'original-field_pdn_design.py');new,newcls=parsed_classes(HERE/'field_pdn_design.py')
  constants=lambda t:{ast.unparse(n.targets[0]):ast.dump(n.value,include_attributes=False) for n in t.body if isinstance(n,ast.Assign)}
  self.assertEqual(constants(old),constants(new))
  allowed={'__init__','design_net','finalize','vg_record','write','drops'}
  original={n.name:ast.dump(n,include_attributes=False) for n in oldcls.body if isinstance(n,ast.FunctionDef) and n.name not in allowed}
  patched={n.name:ast.dump(n,include_attributes=False) for n in newcls.body if isinstance(n,ast.FunctionDef) and n.name not in allowed}
  self.assertEqual(original,patched)
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='min' and any('design_a' in ast.unparse(a) for a in n.args) for n in ast.walk(new)))
 def test_inputs_and_active_combined_closure_unchanged(self):
  packet=json.loads((HERE/'construction.json').read_bytes())
  self.assertTrue(all(digest(p)==h for p,h in packet['input_sha256'].items()))
  self.assertEqual(packet['active_combined_source_binding'],[]);self.assertFalse(packet['installed'])
if __name__=='__main__':
 started=time.time();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
 with (HERE/'host-tests.log').open('w',encoding='utf-8') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 receipt={'verdict':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'elapsed_seconds':round(time.time()-started,3),
  'source_sha256':{p.name:digest(p) for p in [HERE/'field_pdn_design.py',HERE/'field_current_guard.py',HERE/'prepare_patch.py',HERE/'host_controls.py']},
  'log_sha256':digest(HERE/'host-tests.log'),'scope':'Host-only source AST/current checks; no raster/GPU/heavy/native execution'}
 (HERE/'host-receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
 print(json.dumps(receipt));sys.exit(0 if result.wasSuccessful() else 1)
