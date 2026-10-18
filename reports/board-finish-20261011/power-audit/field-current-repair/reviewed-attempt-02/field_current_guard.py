"""Host-only field current accounting. No geometry, capacity or simultaneous-load assumptions are changed."""
import math

class CurrentModelError(ValueError):
 def __init__(self,report):
  self.report=report
  super().__init__('Unqualified field current model: '+', '.join(report.get('reasons',[])))

def current(value,name,positive=False):
 if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or value<0 or (positive and value<=0):
  raise ValueError('Invalid current: '+name)
 return value

def required_vias(amps,capacity):
 current(amps,'array amps');current(capacity,'amps_per_via',True)
 # Never round or cap current before ceil. A fractional positive excess needs another via.
 return max(1,math.ceil(amps/capacity))

def array_status(amps,n,capacity,declared_required=None):
 current(amps,'array amps');required=required_vias(amps,capacity)
 if not isinstance(n,int) or isinstance(n,bool) or n<0:raise ValueError('Invalid actual via count')
 declared_ok=isinstance(declared_required,int) and not isinstance(declared_required,bool) and declared_required==required
 return {'amps':amps,'n':n,'n_req':required,'planner_n_req':declared_required,
  'amps_per_via_policy':capacity,'actual_amps_per_via':amps/n if n else None,
  'qualified_for_modeled_current':n>=required and declared_ok,'full_rail_qualified':False,
  'reasons':([] if n>=required else ['undersized_or_incomplete_via_array'])+([] if declared_ok else ['required_count_missing_or_inconsistent'])}

def rail_status(rail):
 design=current(rail['design_a'],'design_a',True);limit=current(rail['limit_a'],'limit_a',True)
 clusters=rail['clusters']
 if not isinstance(clusters,list) or not clusters:raise ValueError('Explicit downstream clusters required')
 names=set();values=[]
 for cluster in clusters:
  name=cluster.get('name')
  if not isinstance(name,str) or not name or name in names or not cluster.get('pads'):raise ValueError('Invalid/duplicate cluster identity or empty pad roles')
  names.add(name);values.append(current(cluster['amps'],name))
 total=math.fsum(values);reasons=[]
 if total>design:reasons.append('documented_load_sum_exceeds_design_a')
 if total>limit:reasons.append('documented_load_sum_exceeds_source_limit_a')
 if design>limit:reasons.append('design_a_exceeds_source_limit_a')
 return {'id':rail['id'],'documented_cluster_sum_a':total,'design_a':design,'source_limit_a':limit,
  'cluster_count':len(clusters),'model_consistent':not reasons,'reasons':reasons,
  'scope':'Only this explicit documented cluster set; no inferred concurrency or current reduction',
  'full_rail_qualified':False,'source_rating_physical_qualification':False,
  'source_limit_basis':'Existing limit_a model assumption; not a new component/source-rating qualification'}

def validate_spec(spec,only=''):
 current(spec['via']['amps_per_via'],'amps_per_via',True)
 current(spec['drop_budget_v'],'drop_budget_v',True)
 rails=spec['rails'];ids=[r['id'] for r in rails]
 if len(ids)!=len(set(ids)) or not ids:raise ValueError('Missing or duplicate field rail identity')
 selected=only.split(',') if only else ids
 if len(selected)!=len(set(selected)) or any(not rid or rid not in ids for rid in selected):raise ValueError('Unknown/duplicate selected field rail')
 reports={r['id']:rail_status(r) for r in rails if r['id'] in selected}
 reasons=[rid+':'+reason for rid,r in reports.items() for reason in r['reasons']]
 report={'verdict':'MODEL_CURRENT_CONSISTENT' if not reasons else 'REJECT_LOAD_SOURCE_INCONSISTENCY',
  'rails':reports,'reasons':reasons,'full_rail_qualified':False,'geometry_modified':False,
  'capacity_modified':False,'loads_modified':False,'concurrency_assumptions_added':False}
 if reasons:raise CurrentModelError(report)
 return report

def modeled_route_status(rail,design,spec):
 model=rail_status(rail);reasons=list(model['reasons']);context=design.get('current_model',{})
 declared_scope=rail.get('qualification_scope',{})
 if not isinstance(declared_scope,dict) or declared_scope.get('kind') not in ('FULL_DOCUMENTED_CLUSTER_SET','PARTIAL_DOCUMENTED_CLUSTER_SET') or not isinstance(declared_scope.get('description'),str) or not declared_scope['description'].strip():reasons.append('explicit_full_or_partial_cluster_scope_missing')
 if not context.get('source_and_positive_load_pads_resolved'):reasons.append('unresolved_source_or_positive_load_pad')
 total=model['documented_cluster_sum_a']
 delivered=current(design.get('current_reaching_source_a',0),'current_reaching_source_a')
 source_local=current(context.get('source_local_load_a',0),'source_local_load_a')
 if not math.isclose(delivered+source_local,total,rel_tol=1e-12,abs_tol=1e-12):reasons.append('documented_current_source_accounting_mismatch')
 if any(current(u.get('amps',0),'unreached amps')>0 for u in design.get('unreached',[])):reasons.append('unreached_positive_current_load')
 arrays=design.get('via_groups',[])
 if delivered>0 and not arrays:reasons.append('current_path_has_no_accounted_via_arrays')
 for array in arrays:
  status=array_status(array['amps'],array['n'],spec['via']['amps_per_via'],array.get('n_req'))
  if not status['qualified_for_modeled_current']:reasons.append('undersized_or_incomplete_via_array')
 for segment in design.get('segments',[]):
  width=segment['width_mm'];required=segment.get('w_ipc10C_mm_raw')
  if not isinstance(width,(int,float)) or not math.isfinite(width) or width<=0 or required is None or not math.isfinite(required) or width<required:reasons.append('segment_below_existing_ipc_current_width')
 budget=spec['drop_budget_v'];drop=design.get('worst_drop_v_raw')
 if delivered>0 and (not isinstance(drop,(int,float)) or not math.isfinite(drop) or drop>budget):reasons.append('missing_or_exceeded_existing_drop_budget')
 reasons=list(dict.fromkeys(reasons))
 return {'qualified_for_explicit_modeled_route_current':not reasons,'full_rail_qualified':False,
  'declared_cluster_scope':declared_scope,
  'documented_cluster_sum_a':total,'current_reaching_source_a':delivered,'source_local_load_a':source_local,
  'reasons':reasons,'scope':'Only explicit resolved cluster set and unchanged array/IPC/drop policies; native/current-sharing/thermal/fault/transient/return proof remains open'}

def route_output(qualifications,ripup_proposal=False):
 if ripup_proposal:return 'routes_PROPOSAL_DO_NOT_APPLY.json'
 if not qualifications or any(not q['qualified_for_explicit_modeled_route_current'] for q in qualifications.values()):return 'routes_UNQUALIFIED_DO_NOT_APPLY.json'
 return 'routes.json'
