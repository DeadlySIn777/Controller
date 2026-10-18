"""Whole-board source/pad-group plan from existing native and actual R299 evidence."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict,Counter
import hashlib,importlib.util,json,pickle,re
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;OUT=HERE/'coordinated-power-reference-plane-plan-r1';CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACT=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';NATIVE=ROOT/'reports/board-finish-20261017/corrected-baseline-r1/native';PART=NATIVE.parent/'native-check/partitions.json';PADS=ROOT/'reports/board-finish-20261017/join-throughput-r1/native-pad-inventory.json';HELP=HERE/'field5-current-continuation/freeze_single_outer_power_packet_r11.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sp=importlib.util.spec_from_file_location('sexpr',HELP);P=importlib.util.module_from_spec(sp);sp.loader.exec_module(P);norm=lambda s:s.replace('{slash}','/')
REFS=[('LOGIC','/LOGIC_GND',[('J11001','2')]),('FIELD_A','/motherboard_motors/FIELD_GND',[('J11003','2')]),('FIELD_B','/motherboard_do/FIELD_B_0V',[('J11005','2')]),('AI','/motherboard_analog_input/AI_AGND',[('U14701','7'),('U14702','7'),('U14703','7')]),('AO0','/motherboard_analog_output/AO0_COM',[('U14601','7')]),('AO1','/motherboard_analog_output/AO1_COM',[('U14619','7')]),('CAN','/motherboard_comms/CAN_GND',[('U14813','15'),('U14813','16'),('U14813','17')]),('RS485','/motherboard_comms/RS485_COM',[('U14815','2'),('U14812','15')]),('CHASSIS','/CHASSIS',[])]
EXTRA={'/CORE_1V2':[('L2001','2')],'/IO_3V3':[('R18001','2')],'/mc_local_power/IO_3V3_REG_LOCAL':[('L2002','2')],'/mc_local_power/CORE_5V':[('R11022','2')],'/motherboard_power_entry/MOTION_5V_RAW':[('R11030','2')],'/motherboard_power_entry/FIELD_5V':[('L11003','2')],'/motherboard_compute/CM_AUX_3V3':[('J15001','78'),('J15001','84'),('J15001','86')]}
def v(n,k):
 q=next((x for x in n[1:]if isinstance(x,list)and x[0]==k),None);return q[1].decode().strip('"')if q and len(q)>1 else None
def box(pads):
 xy=[p['at_IU']for p in pads];return[min(x[0]for x in xy)/1e6,min(x[1]for x in xy)/1e6,max(x[0]for x in xy)/1e6,max(x[1]for x in xy)/1e6]if xy else[]
def groups(net,roots,part,pads):
 gs=part.get(net,[]);rows=[]
 for i,keys in enumerate(gs):
  pp=[pads[k]for k in keys];source=[k for k in keys if any(k.startswith(r+'.'+p+'#')for r,p in roots)];rows.append({'native_group':i,'physical_pad_keys':keys,'pad_count':len(keys),'source_port_keys':source,'bounds_mm':box(pp)})
 sourcegroups=[x['native_group']for x in rows if x['source_port_keys']];return{'net':net,'source_ports':[[r,p]for r,p in roots],'groups':len(gs),'required_native_pad_joins':max(0,len(gs)-1),'pad_count':sum(map(len,gs)),'source_port_groups':sourcegroups,'source_ports_span_more_than_one_unjoined_group':len(sourcegroups)>1,'group_rows':rows}
def main():
 assert not OUT.exists();OUT.mkdir();files=[PART,PADS,NATIVE/'fresh.net',ACT/'actual-combined-full-after-model.pkl',ACT/'actual-combined-full-after-all-net-groups.pkl',CONT/'field-power/normal-model-r3.json',ROOT/'reports/board-finish-20261011/power-audit/constraint-snapshot/2-rail_model.json',ROOT/'hardware/sbc_power/design-envelope.json',HELP,Path(__file__)];native=json.loads(PART.read_text());part={norm(k):x for k,x in native['nets'].items()};padinv=json.loads(PADS.read_text());pads=padinv['pads'];g=pickle.loads(files[3].read_bytes());actual=pickle.loads(files[4].read_bytes());field=json.loads(files[5].read_text());legacy=json.loads(files[6].read_text());tree=P.parsed(files[2].read_bytes());nn=next(x for x in tree[1:]if isinstance(x,list)and x[0]==b'nets');nodes={};roots=defaultdict(list)
 for n in nn[1:]:
  net=norm(v(n,b'name')or'');nodes[net]=[x for x in n[1:]if isinstance(x,list)and x[0]==b'node']
  for x in nodes[net]:
   if v(x,b'pintype')=='power_out'and not re.search(r'(_SW|_VCC|_VDDA|_RTN|_REF_DRIVE|_REF_LIMIT_OUT)$',net):roots[net].append((v(x,b'ref'),v(x,b'pin')))
 for net,row in legacy['rails'].items():
  net=norm(net)
  for q in row.get('sources',[]):
   for p in q.get('pins',[]):
    pair=(q['ref'],str(p))
    if any((v(x,b'ref'),v(x,b'pin'))==pair for x in nodes.get(net,[]))and pair not in roots[net]:roots[net].append(pair)
 for net,pp in EXTRA.items():roots[net]=pp
 refnets={x[1]for x in REFS};powers=[]
 for net,pp in roots.items():
  if net in part and net not in refnets and not re.search(r'(_SW|_VCC|_VDDA|_RTN|_REF_DRIVE|_REF_LIMIT_OUT)$',net):powers.append(groups(net,pp,part,pads))
 powers.sort(key=lambda x:(-x['required_native_pad_joins'],x['net']));references=[]
 for domain,net,pp in REFS:
  row=groups(net,pp,part,pads);row['domain']=domain;actual_groups=actual.get(net,[]);sourcegroups=[xs for xs in actual_groups if any(q['kind']=='pad'and(q['ref'],str(q['pin']))in pp for q in xs)];fills=[q for xs in sourcegroups for q in xs if q['kind']=='fill'and q['layer']in('In1.Cu','In4.Cu')];roles=defaultdict(lambda:{'area':0,'bounds':[]})
  for q in fills:
   k=(q['layer'],q['uuid']);roles[k]['area']+=q['shape'].area;roles[k]['bounds'].append(q['shape'].bounds)
  top=[]
  for ly in('In1.Cu','In4.Cu'):
   ranked=sorted([(k,z)for k,z in roles.items()if k[0]==ly],key=lambda kv:-kv[1]['area'])[:3]
   for k,z in ranked:
    zone=next(a for a in g['zones']if a['uuid']==k[1]);bb=z['bounds'];top.append({'layer':ly,'zone_UUID':k[1],'actual_source_connected_drilled_fill_area_sum_mm2':z['area'],'bounds_mm':[min(b[0]for b in bb),min(b[1]for b in bb),max(b[2]for b in bb),max(b[3]for b in bb)],'source_profile':{x:zone.get(x)for x in('priority','clearance_mm','min_thickness_mm','name')}})
  row['dominant_actual_R299_source_reference_roles']=top;row['source_connected_R299_pad_nodes']=len({(q['ref'],str(q['pin']))for xs in sourcegroups for q in xs if q['kind']=='pad'});references.append(row)
 contact=[]
 for net,gs in part.items():
  domain=g['domains_normalized'].get(net,'')
  if domain.startswith('DOM_CONTACT_')and len(gs)>1:contact.append({'domain':domain,'net':net,'groups':len(gs),'joins':len(gs)-1,'pad_groups':gs})
 r={'utc':datetime.now(timezone.utc).isoformat(),'status':'WHOLE_BOARD_COORDINATED_POWER_AND_REFERENCE_PLANE_COMPLETION_PLAN_NO_BOARD_EDITS','input_sha256':{str(p):sha(p)for p in files},'measurement_scope':'Corrected-baseline native stored-fill pad groups; actual R299 source-connected drilled plane roles. Current stage4 source edits are unqualified until a full native AFTER. Do not mix these counters.','native_total_required_pad_joins':native['pad_island_joins'],'references':references,'source_bound_power_rails':powers,'dry_contact_domain_missing_joins_separate_from_power_ground':contact,'reference_join_total':sum(x['required_native_pad_joins']for x in references),'power_rail_join_total':sum(x['required_native_pad_joins']for x in powers),'field_existing_normal_trunk_and_return_A':{'protected_positive':field['normal_protected24_trunk_envelopes_a'],'connector_signed_return':field['real_connector_input_return_envelopes_a'],'local_outputs':field['computed_local_output_envelopes_a'],'routing_targets':field['routing_local_targets_a']},'full_preserved_logic_stress_A':{'CORE1V2':.8,'IO3V3':2.,'CORE5V':7.882},'current_conflicts_to_resolve_before_width_signoff':['CORE7A source design has6.637A conditional normal screen/7A board envelope, while continuation retains7.882A CORE5 stress; do not use10A silicon label as board qualification or lower7.882A stress.','Legacy rail_model/power_widths/load_currents contain historical0.4A DO,0.5A TPS7A16/two-encoder/equal-parallel-pad assumptions; use it for verified source pin identities only, never new sizing.','Full twelve motors/four ABZ/all16DO0.5A remain fitted and simultaneously accounted. MOTION/compute/analog/isolated-communications branch corner current, transient and terminal-drop budgets need explicit source-correct completion, not generic defaults.'],'minimum_corridor_contract':'Use maximum signed downstream source/load cut current at each finite electrode and actual minimum Cu/plating/temperature/drop budget. FA/FB entry trunks reserve existing6.5A policy-equivalent space (historical7.189mm35um/10C screen, not qualification); no0.2mm signal-width ground shortcut. Local branch currents require a complete allocation; no automatic6.5A through every island, no zero unknowns and no equal pad/via sharing.','native_redesign_order':['Create an isolated whole-board PDN redesign: retain all galvanic boundaries and complete functional bank placements; all new source outlines one outer each with explicit holes and individual UUIDs.','Reconstruct domain reference regions jointly onIn1/In4 from source electrodes to every listed ground group, preserving cross-domain0.6mm gaps and converter/package keepouts; multiport AI/CAN/compute sources must all be physically joined.','RebuildIn2 power cells and finite source/barrel entries for IO3V3,CORE1V2,CORE5V,MOTION5V and field/analog rails before signal rerouting; move mutually blocking power/control crossings and bank placement together.','Replace redundant historical same-net local pour boundaries with coherent domain roles, but validate every formerly source-rooted component/direct contact and old receiving return. Don’t blindly union nominal outlines, erase antipads, join dissimilar ground domains, or reduce island-removal/minwidth policy.','After coordinated plane/placement changes, native full fill and DRC must show all reference/power source groups complete, no old key/contact/reference regression, and current-sized minimum necks; then export the global signal problem with actual source planes and correct per-domain rules.'],'native_jobs':0,'board_changed':False,'adopted':False,'manufacturing_ready':False};(OUT/'plan.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'reference_joins':r['reference_join_total'],'power_joins':r['power_rail_join_total'],'source_bound_power_rails':len(powers),'out':str(OUT)}),flush=True)
if __name__=='__main__':main()
