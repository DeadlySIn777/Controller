"""ROOT106 vector proposal filter with honest accepted/failed target accounting.

Host geometry only. No raster rebuild/GPU/native/current/rooted-return proof.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT106_BBOX=[-.05,-.05,450.05,235.05]
KNOWN_DOMAINS={"DOM_AI","DOM_AO0","DOM_AO1","DOM_CAN","DOM_CHASSIS","DOM_FIELD_A","DOM_FIELD_B",
               "DOM_LOGIC","DOM_RS485","DOM_CONTACT_PEN0_1","DOM_CONTACT_PEN1_1","DOM_CONTACT_PERMIT_OUT_1",
               "NC_ISOLATE"}|{f"DOM_CONTACT_EN{i}_COM" for i in range(12)}

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def finite(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def validate_inputs(geometry,plan,existing_failed,target_count):
 if geometry.get('bbox')!=ROOT106_BBOX:raise ValueError('Exact guard supports explicit ROOT106450x235 geometry only')
 domains={};pads={}
 for p in geometry['pads']:
  if p.get('net'):
   domain=p.get('cls','').split(',')[0]
   if p['net'] in domains and domains[p['net']]!=domain:raise ValueError('Contradictory net domain classes')
   domains[p['net']]=domain
  pads.setdefault((p['ref'],p['num']),[]).append(p)
 if not any(d in KNOWN_DOMAINS for d in domains.values()):raise ValueError('Classless geometry cannot establish isolated-domain clearances')
 roles=set()
 for item in plan:
  if not isinstance(item,dict) or any(k not in item for k in('ref','pad','net','layer','d','drill','stub_w','via','pad_xy','dist')):raise ValueError('Incomplete stitch proposal')
  if not all(isinstance(item[k],str) and item[k] for k in('ref','pad','net')):raise ValueError('Invalid physical pad identity')
  role=(item['ref'],item['pad'])
  if role in roles:raise ValueError('Duplicate planned physical pad role')
  roles.add(role)
  if domains.get(item['net']) not in KNOWN_DOMAINS:raise ValueError('Planned net has no known explicit isolated-domain class')
  if item['layer'] not in('F.Cu','B.Cu'):raise ValueError('Stitch stub must use an actual outer pad layer')
  if not all(isinstance(item[k],(tuple,list)) and len(item[k])==2 for k in('via','pad_xy')):raise ValueError('Invalid coordinate dimensions')
  values=[item['d'],item['drill'],item['stub_w'],item['dist'],*item['via'],*item['pad_xy']]
  if not all(finite(v) for v in values) or item['d']<.5 or item['drill']<.2 or (item['d']-item['drill'])/2<.15-1e-9 or item['stub_w']<=0 or item['dist']<0:raise ValueError('Unsupported or invalid stitch dimensions')
  matches=pads.get(role,[])
  if len(matches)!=1 or matches[0]['net']!=item['net'] or item['layer'] not in matches[0]['layers'] or item['pad_xy']!=[matches[0]['x'],matches[0]['y']]:raise ValueError('Proposal does not name one exact physical pad/net/pose/layer')
 if existing_failed is not None:
  for failure in existing_failed:
   if not isinstance(failure,dict) or any(not isinstance(failure.get(k),str) or not failure[k] for k in('pad','net','why')):raise ValueError('Invalid existing failed pad accounting')
   role=tuple(failure['pad'].rsplit('.',1))
   if len(role)!=2 or role in roles:raise ValueError('Duplicate planned/failed physical pad role')
   roles.add(role)
   matches=pads.get(role,[])
   if not all(role) or len(matches)!=1 or matches[0]['net']!=failure['net']:raise ValueError('Failed row does not name one exact physical pad/net')
  if not isinstance(target_count,int) or isinstance(target_count,bool) or target_count<0 or target_count!=len(plan)+len(existing_failed):raise ValueError('Targets must equal planned plus existing failed')
 elif target_count is not None:raise ValueError('Target accounting requires existing failed rows')

def validate_plan(geometry_path,plan,output,pad_mask='',existing_failed=None,target_count=None,dependency_paths=()):
 geometry_path,output=Path(geometry_path),Path(output)
 helper=Path(__file__).with_name('stitch_vector_audit.py')
 context=[geometry_path,helper,Path(__file__),Path(sys.executable)]+[Path(p) for p in dependency_paths if p]
 if pad_mask:context.append(Path(pad_mask))
 paths=[Path(str(output)+suffix) for suffix in('.vector-proposal.json','.vector-report.json','.vector.log','.vector-guard.json')]
 protected={p.resolve() for p in context}
 if output.resolve() in protected or (output.exists() and any(output.samefile(p) for p in context)):raise ValueError('Planner output aliases input dependency')
 if len({p.resolve() for p in paths})!=4 or any(p.resolve() in protected for p in paths):raise ValueError('Vector output aliases input dependency')
 proposal,report,log,receipt_path=paths
 frozen={str(p.resolve()):digest(p) for p in context}
 geometry=json.loads(geometry_path.read_bytes())
 validate_inputs(geometry,plan,existing_failed,target_count)
 # Invalid inputs refuse before any proposal/report/receipt file is written.
 if any(p.exists() for p in paths):raise ValueError('Fresh vector guard artifact paths required')
 proposal.write_text(json.dumps({'plan':plan},indent=1)+'\n',encoding='utf-8')
 frozen[str(proposal.resolve())]=digest(proposal)
 command=[sys.executable,str(helper),str(geometry_path),str(proposal),str(report),'--classes',str(geometry_path)]
 if pad_mask:command+=['--pad-mask',str(pad_mask)]
 with log.open('w',encoding='utf-8') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
 if result.returncode or not report.is_file():raise ValueError('Independent vector stitch check did not complete')
 if any(digest(path)!=expected for path,expected in frozen.items()):raise ValueError('Vector input/helper changed during execution')
 check=json.loads(report.read_bytes())
 if check['planned']!=len(plan) or len(check['rows'])!=len(plan):raise ValueError('Vector report does not cover every proposal')
 provenance=check.get('runtime_provenance',{})
 if not provenance.get('unchanged') or provenance.get('before')!=provenance.get('after') or not provenance.get('before'):raise ValueError('Vector dependency before/after provenance incomplete')
 if provenance['before'].get(str(helper.resolve()))!=frozen[str(helper.resolve())]:raise ValueError('Vector executed helper identity differs')
 expected_inputs={str(p.resolve()):digest(p) for p in (geometry_path,proposal)}
 if pad_mask:expected_inputs[str(Path(pad_mask).resolve())]=digest(pad_mask)
 if provenance.get('inputs_before')!=expected_inputs or provenance.get('inputs_after')!=expected_inputs:raise ValueError('Vector measured input identities differ')
 accepted,rejected=[],[]
 for item,row in zip(plan,check['rows']):
  if any(item[k]!=row[k] for k in('ref','pad','net','layer','via')):raise ValueError('Vector report has wrong physical proposal identity')
  if row['viol']:
   rejected.append({'pad':item['ref']+'.'+item['pad'],'net':item['net'],
                    'why':'independent vector stitch rejection','vector_violations':row['viol'],'proposal':item})
  else:accepted.append(item)
 if len(rejected)!=check['stitches_with_violations'] or len(plan)!=len(accepted)+len(rejected):raise ValueError('Vector rejection accounting differs')
 if existing_failed is not None and target_count!=len(accepted)+len(existing_failed)+len(rejected):raise ValueError('Filtered target accounting differs')
 receipt={'verdict':'VECTOR_PROPOSAL_FILTER_COMPLETE','planned_input':len(plan),'accepted':len(accepted),
          'rejected':rejected,'rejected_count':len(rejected),'targets':target_count,
          'failed_before':len(existing_failed) if existing_failed is not None else None,
          'failed_after':len(existing_failed)+len(rejected) if existing_failed is not None else None,
          'target_accounting_complete':existing_failed is not None,
          'input_sha256_before':frozen,'input_sha256_after':{p:digest(p) for p in frozen},
          'vector_report_sha256':digest(report),'helper_dependency_provenance':provenance,
          'scope':'ROOT106450x235 host vector proposal filtering; no raster/GPU/native execution',
          'limits':['Original vector geometry exporter/checker coverage and rounding limits remain',
                    'Stored fill landing is not rooted-return/current or fresh native connectivity proof',
                    'Current matching project/reservations/DRC/uncapped pad-partition/API/electrical gates remain required']}
 receipt_path.write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'tool':'stitch_exact_guard','input':len(plan),'accepted':len(accepted),'rejected':len(rejected),
                   'targets':target_count,'failed_after':receipt['failed_after'],'receipt':str(receipt_path)}),flush=True)
 return accepted,rejected

def filter_document(geometry_path,document,output,pad_mask='',dependency_paths=()):
 accepted,rejected=validate_plan(geometry_path,document['plan'],output,pad_mask,
                              existing_failed=document['failed'],target_count=document['targets'],dependency_paths=dependency_paths)
 result={**document,'plan':accepted,'failed':document['failed']+rejected,
         'vector_guard':{'planned_input':len(document['plan']),'accepted':len(accepted),'rejected':len(rejected),
                         'receipt':str(output)+'.vector-guard.json'}}
 if result['targets']!=len(result['plan'])+len(result['failed']):raise ValueError('Document target accounting incomplete')
 return result
