"""Cheap input-contract and exact final-hook controls; never import/run the GPU planner."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
import stitch_exact_guard as G
HERE=Path(__file__).resolve().parent
def fixtures():
 pad={'ref':'C1','num':'1','net':'N','cls':'DOM_LOGIC','x':8.0,'y':10.0,'layers':['F.Cu'],
      'poly':[[[[7.8,9.8],[8.2,9.8],[8.2,10.2],[7.8,10.2]],[]]],'smd':True,'drill':0}
 geometry={'bbox':G.ROOT106_BBOX.copy(),'pads':[pad],'tracks':[],'vias':[],
  'zones':[{'net':'N','fills':{'In1.Cu':[[[[1,1],[20,1],[20,20],[1,20]],[]]]}}]}
 proposal={'ref':'C1','pad':'1','net':'N','layer':'F.Cu','d':.5,'drill':.2,'stub_w':.25,
           'via':[10.0,10.0],'pad_xy':[8.0,10.0],'dist':2.0}
 return geometry,[proposal]
class Controls(unittest.TestCase):
 def test_valid_explicit_domain_and_accounting(self):
  g,p=fixtures();G.validate_inputs(g,p,[],1)
 def test_classless_rejected_before_any_output(self):
  g,p=fixtures();g['pads'][0]['cls']='Default'
  with tempfile.TemporaryDirectory() as temp:
   d=Path(temp);f=d/'geom.json';f.write_text(json.dumps(g));before={x.name for x in d.iterdir()}
   with self.assertRaisesRegex(ValueError,'Classless'):G.validate_plan(f,p,d/'out',existing_failed=[],target_count=1)
   self.assertEqual(before,{x.name for x in d.iterdir()})
 def test_unknown_planned_domain_rejected(self):
  for domain in ('','Default','DOM_FAKE','UNKNOWN','DP100'):
   with self.subTest(domain=domain):
    g,p=fixtures();g['pads'].append({**g['pads'][0],'ref':'C2','num':'2','net':'KNOWN','cls':'DOM_FIELD_A'})
    g['pads'][0]['cls']=domain
    with self.assertRaisesRegex(ValueError,'known explicit'):G.validate_inputs(g,p,[],1)
 def test_contradictory_net_domains_rejected(self):
  g,p=fixtures();g['pads'].append({**g['pads'][0],'ref':'C2','cls':'DOM_FIELD_A'})
  with self.assertRaisesRegex(ValueError,'Contradictory'):G.validate_inputs(g,p,[],1)
 def test_invalid_dimensions(self):
  for key,value in [('d',.49),('drill',.19),('drill',.25),('stub_w',0),('stub_w',-1),
                    ('d',float('nan')),('drill',float('inf')),('d',True),('dist',-1),
                    ('via',[10]),('via',[10,float('nan')]),('pad_xy',[8,10,0])]:
   with self.subTest(key=key,value=str(value)):
    g,p=fixtures();p[0][key]=value
    with self.assertRaisesRegex(ValueError,'dimension'):G.validate_inputs(g,p,[],1)
 def test_duplicate_planned_roles(self):
  g,p=fixtures();p.append(copy.deepcopy(p[0]))
  with self.assertRaisesRegex(ValueError,'Duplicate planned'):G.validate_inputs(g,p,[],2)
 def test_duplicate_failed_and_planned_roles(self):
  g,p=fixtures();f=[{'pad':'C1.1','net':'N','why':'no-path'}]
  with self.assertRaisesRegex(ValueError,'Duplicate'):G.validate_inputs(g,p,f,2)
 def test_duplicate_failed_roles(self):
  g,p=fixtures();g['pads'].append({**g['pads'][0],'ref':'C2'});f=[{'pad':'C2.1','net':'N','why':'no-path'}]*2
  with self.assertRaisesRegex(ValueError,'Duplicate'):G.validate_inputs(g,p,f,3)
 def test_failed_identity_rejects_fabricated_empty_or_wrong_net(self):
  for pad,net in [('C9999.1','N'),('C2.','N'),('.1','N'),('C2.1','OTHER')]:
   with self.subTest(pad=pad,net=net):
    g,p=fixtures();g['pads'].append({**g['pads'][0],'ref':'C2'})
    with self.assertRaisesRegex(ValueError,'Failed row'):G.validate_inputs(g,p,[{'pad':pad,'net':net,'why':'no-path'}],2)
 def test_target_accounting_rejects_bad_counts(self):
  for count in (0,2,True,1.0,None):
   with self.subTest(count=count):
    g,p=fixtures()
    with self.assertRaisesRegex(ValueError,'Targets'):G.validate_inputs(g,p,[],count)
 def test_exact_pad_identity_not_ambiguous_ref_pad(self):
  for mutation in ('net','pose','layer','duplicate'):
   with self.subTest(mutation=mutation):
    g,p=fixtures()
    if mutation=='net':g['pads'][0]['net']='OTHER';g['pads'].append({**g['pads'][0],'ref':'C2','net':'N'})
    if mutation=='pose':p[0]['pad_xy']=[8.001,10.0]
    if mutation=='layer':p[0]['layer']='B.Cu'
    if mutation=='duplicate':g['pads'].append(copy.deepcopy(g['pads'][0]))
    with self.assertRaisesRegex(ValueError,'exact physical'):G.validate_inputs(g,p,[],1)
 def test_unknown_foreign_domain_uses_actual_cross_domain_06(self):
  g,p=fixtures();g['tracks']=[{'net':'UNCLASSIFIED','layer':'F.Cu','a':[10.65,9.0],'b':[10.65,11.0],'w':.2}]
  with tempfile.TemporaryDirectory() as temp:
   d=Path(temp);f=d/'geom.json';f.write_text(json.dumps(g))
   accepted,rejected=G.validate_plan(f,p,d/'check',existing_failed=[],target_count=1)
   self.assertFalse(accepted);self.assertEqual(len(rejected),1)
   violations=rejected[0]['vector_violations']
   self.assertTrue(any(v[0]=='via_clearance' and 'req 0.6' in v[1] and abs(v[2]-.3)<1e-8 for v in violations))
   receipt=json.loads((d/'check.vector-guard.json').read_bytes())
   self.assertEqual(receipt['failed_after'],1);self.assertTrue(receipt['helper_dependency_provenance']['unchanged'])
 def test_output_alias_refused(self):
  g,p=fixtures()
  with tempfile.TemporaryDirectory() as temp:
   d=Path(temp);prefix=d/'x';f=d/'x.vector-proposal.json';f.write_text(json.dumps(g));h=G.digest(f)
   with self.assertRaisesRegex(ValueError,'aliases'):G.validate_plan(f,p,prefix,existing_failed=[],target_count=1)
   self.assertEqual(h,G.digest(f))
 def test_actual_planner_output_alias_refused(self):
  g,p=fixtures()
  with tempfile.TemporaryDirectory() as temp:
   d=Path(temp);f=d/'geom.json';f.write_text(json.dumps(g));h=G.digest(f)
   with self.assertRaisesRegex(ValueError,'Planner output aliases'):G.validate_plan(f,p,f,existing_failed=[],target_count=1)
   self.assertEqual(h,G.digest(f));self.assertEqual([f.name],[x.name for x in d.iterdir()])
 def test_real_planner_final_hook_appends_failures_before_json_save(self):
  # Execute only the newly inserted source statements and the original final json.dump AST.
  source=(HERE/'stitch_plan3.py').read_text();tree=ast.parse(source)
  start=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.ImportFrom) and n.module=='stitch_exact_guard')
  chunk=ast.Module(body=tree.body[start:start+4],type_ignores=[])
  self.assertTrue(isinstance(chunk.body[-1],ast.Expr) and isinstance(chunk.body[-1].value,ast.Call) and chunk.body[-1].value.func.attr=='dump')
  plans=[{'role':i} for i in range(188)];old=[{'old':i} for i in range(248)];new=[{'rejected':i} for i in range(4)]
  stream=io.StringIO();namespace={'sys':type('S',(),{'argv':['planner','geom']})(),'plan':plans,'failed':old,
   'OUT':'out','PADMASK':'mask','targets':{'N':list(range(436))},'__file__':'planner','DRU':'rules',
   'json':json,'math':__import__('math'),'VD':.5,'VDR':.2,'STUB':.25,'GAP':.1,'MASKEXP':0,
   'smd_wide_n':{},'dru_masks':[],'STUB_ANG':0,'n_angle_rej':0,'pad_dirs':[]}
  with patch.object(G,'validate_plan',return_value=(plans[:184],new)) as checker,patch('builtins.open',return_value=stream):
   exec(compile(chunk,'isolated-final-hook','exec'),namespace)
  kwargs=checker.call_args.kwargs
  self.assertEqual(kwargs['target_count'],436);self.assertEqual(kwargs['dependency_paths'],('planner','rules'))
  saved=json.loads(stream.getvalue());self.assertEqual((saved['targets'],len(saved['plan']),len(saved['failed'])),(436,184,252))
  self.assertEqual(saved['failed'][-4:],new)
 def test_saved_actual_replay_and_recheck_complete(self):
  r=json.loads((HERE/'final2-replay-receipt.json').read_bytes())
  d=json.loads((HERE/'final2-filtered-plan.json').read_bytes())
  self.assertEqual((d['targets'],len(d['plan']),len(d['failed'])),(436,184,252))
  self.assertEqual(r['accepted_recheck_violations'],0);self.assertEqual(len(r['new_failed']),4)
  self.assertEqual(r['historical_input_sha256_before'],r['historical_input_sha256_after'])
  self.assertEqual(r['preserved_v1_sha256_before'],r['preserved_v1_sha256_after'])
  self.assertEqual(r['guard_sha256'],G.digest(HERE/'stitch_exact_guard.py'))
  self.assertEqual([v[2] for f in r['new_failed'] for v in f['vector_violations'] if v[0]=='via_clearance'],[.145,.11,.145,.145])
if __name__=='__main__':
 started=time.time();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
 with (HERE/'host-tests.log').open('w',encoding='utf-8') as stream:
  result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 receipt={'verdict':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,
  'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
  'elapsed_seconds':round(time.time()-started,3),'script_sha256':G.digest(__file__),
  'tested_source_sha256':{p.name:G.digest(p) for p in [HERE/'stitch_exact_guard.py',HERE/'stitch_vector_audit.py',HERE/'stitch_plan3.py']},
  'log_sha256':G.digest(HERE/'host-tests.log'),'scope':'Host-only input controls, small independent vector check and final-hook AST; no GPU/native planner execution'}
 (HERE/'host-receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
 print(json.dumps(receipt));sys.exit(0 if result.wasSuccessful() else 1)
