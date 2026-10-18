"""R44 exact six-track topology repair on pinned SBC R32: full contact precheck.

R32 remains prospective; this checks existing relationships and R44 source
attachment without promoting its five nominated CORE feeders to rooted evidence.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,math
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point
from inventory import sha
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import zone_projection_r1 as N
OUT=HERE/'u11015-r44-joint-contact-audit-r46'

def write(path,x):path.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def filtered(groups,remove):return [[q for q in xs if not(q['kind']=='track' and q['uuid'] in remove)] for xs in groups]

def main():
 assert not OUT.exists();OUT.mkdir()
 rp=HERE.parent/'sbc-power/five-core-and-b5-checkpoint-r32';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'model.pkl')==rr['model_sha256'];g,h,binding,zones,before=pickle.loads((rp/'model.pkl').read_bytes())
 bp=HERE/'local-and-b5-return-audit-r25';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'groups.pkl')==br['groups_sha256'];prior=pickle.loads((bp/'groups.pkl').read_bytes());base25=pickle.loads((bp/'geometry.pkl').read_bytes())
 q=HERE/'u11015-reverse-companion-repair-r44';r=json.loads((q/'receipt.json').read_text());assert sha(q/'proposed-discrete.pkl')==r['proposed_discrete_sha256'];d=pickle.loads((q/'proposed-discrete.pkl').read_bytes());remove={t['uuid'] for t in r['owned_original_track_removals']};assert len(remove)==6
 original={t['uuid']:t for t in h['tracks']}
 for t in r['owned_original_track_removals']:assert original[t['uuid']]==t
 hh={**h,'tracks':[t for t in h['tracks'] if t['uuid'] not in remove]+d['tracks'],'vias':h['vias']+d['vias']}
 assert not({v['uuid'] for v in d['vias']}&{v['uuid'] for v in h['vias']})
 rec,trees=F.build({**hh,'zones':[]});cu=[];holes=[]
 smd=[(p0,sh) for p0 in hh['pads'] if p0['smd'] for l,rs in p0['layers'].items() if l in ('F.Cu','B.Cu') for sh in C.poly(rs)]
 padholes=[(p0,sh) for p0 in hh['pads'] for sh in C.poly(p0.get('hole') or [])]
 for v in d['vias']:
  pp=Point(v['x'],v['y']);disk=pp.buffer(v['d']/2,quad_segs=32)
  for p0,sh in smd:
   distance=pp.distance(sh)-v['drill']/2
   if distance<.275-1e-9:holes.append({'kind':'SMD','via':v['uuid'],'other':p0['uuid'],'gap_mm':distance})
  for p0,sh in padholes:
   distance=pp.distance(sh)-v['drill']/2
   if distance<.275-1e-9:holes.append({'kind':'PAD_DRILL','via':v['uuid'],'other':p0['uuid'],'gap_mm':distance})
  for w in hh['vias']:
   if w['uuid']==v['uuid']:continue
   distance=math.hypot(v['x']-w['x'],v['y']-w['y'])-(v['drill']+w['drill'])/2
   if distance<.275-1e-9:holes.append({'kind':'VIA_DRILL','via':v['uuid'],'other':w['uuid'],'gap_mm':distance})
  for l in v['flashed']:
   for j in trees[l].query(disk.buffer(.626),predicate='intersects'):
    w=rec[l][int(j)]
    if w['net']==v['net']:continue
    required=(.15 if w['domain']==hh['domains_normalized'][C.norm(v['net'])] else .6)+.025;distance=disk.distance(w['shape'])
    if distance<required-1e-7:cu.append({'kind':'VIA','uuid':v['uuid'],'other':w['uuid'],'layer':l,'gap_mm':distance,'required_mm':required})
 for t in d['tracks']:
  sh=C.body(t);l=t['layer']
  assert t['w']>=.2
  for j in trees[l].query(sh.buffer(.626),predicate='intersects'):
   w=rec[l][int(j)]
   if w['net']==t['net']:continue
   required=(.15 if w['domain']==hh['domains_normalized'][C.norm(t['net'])] else .6)+.025;distance=sh.distance(w['shape'])
   if distance<required-1e-7:cu.append({'kind':'TRACK','uuid':t['uuid'],'other':w['uuid'],'layer':l,'gap_mm':distance,'required_mm':required})
 write(OUT/'ordinary-aperture-receipt.json',{'verdict':'PASS' if not cu and not holes else 'REJECT','Cu_failures':cu,'hole_failures':holes,'pinned_R32_model_SHA256':sha(rp/'model.pkl'),'new_vias':3,'new_segments':12});print('R32 ordinary',len(cu),len(holes),flush=True)
 # Restore known transient GEOS precision state before any buffer replay.
 pids={z['uuid'] for z in zones if z.get('label')=='CORE-main-In2' or z.get('label','').startswith('IO3-r15-field-crossing-') or z.get('field_return_proposal') and z['layer']=='In2.Cu'}
 assert len(pids)==9;zones=[{**z,'shape':set_precision(z['shape'],1e-6)} if z['uuid'] in pids else z for z in zones]
 print('projecting',len(zones),flush=True);after,cuts=N.projected(g,hh,zones)
 nets=sorted(set(prior)|{C.norm(t['net']) for t in d['tracks']});rows=[];groups={}
 for net in nets:
  a=filtered(prior.get(net) or F.graph(base25,net),remove);b=F.graph(after,net);old32=filtered(F.graph(before,net),remove);groups[net]=b
  lost25=losses(a,b);lost32=losses(old32,b);row={'net':net,'R25_retained_relationship_losses':lost25,'R32_local_delta_relationship_losses':lost32,'verdict':'PASS' if not lost25 and not lost32 else 'REPAIR_REQUIRED'};rows.append(row);print(net,row['verdict'],len(lost25),len(lost32),flush=True);write(OUT/'checkpoint.json',rows)
 roots=[]
 for net,root in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/motherboard_safety_sensor/FIELD_B_5V_PRE','L19001')]:
  ri=next(i for i,xs in enumerate(groups[net]) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(root,'2') for q in xs));rootkeys=F.discrete_keys(groups[net][ri]);oldri=next(i for i,xs in enumerate(prior[net]) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(root,'2') for q in xs));missing=F.discrete_keys(prior[net][oldri])-rootkeys
  roots.append({'net':net,'root':root+'.2','root_group':ri,'prior_source_contacts_not_rooted':[list(k) for k in sorted(missing)],'unrooted_named_groups':[i for i,xs in enumerate(groups[net]) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)],'new_U11015_GND6_rooted':any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','6') for q in groups[net][ri]) if root=='J11003' else None})
 ownoutside={x['uuid'] for a in r['exact_outside_contact_ledger'] for x in a['retained_same_raw_net_outside_contacts']};outrows=[]
 for net in ('/motherboard_power_entry/AUX24_A_ILIM','/motherboard_power_entry/AUX24_A_DVDT'):
  matches=[{'group':i,'outside_UUIDs':sorted({x['uuid'] for x in xs}&ownoutside)} for i,xs in enumerate(groups[net]) if {x['uuid'] for x in xs}&ownoutside];outrows.append({'net':net,'retained_contact_partitions':matches,'restored_all_outside_pad_pair_contacts':len(matches)==1 and len(matches[0]['outside_UUIDs'])==2})
 (OUT/'geometry.pkl').write_bytes(pickle.dumps(after,protocol=5));(OUT/'discrete.pkl').write_bytes(pickle.dumps(hh,protocol=5));(OUT/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(zones,protocol=5))
 passed=not cu and not holes and all(x['verdict']=='PASS' for x in rows) and all(not x['prior_source_contacts_not_rooted'] for x in roots) and next(x for x in roots if x['root']=='J11003.2')['new_U11015_GND6_rooted'] and all(x['restored_all_outside_pad_pair_contacts'] for x in outrows)
 receipt={'verdict':'PASS_CONTACTS_AND_ORDINARY_APERTURES_NATIVE_CURRENT_PENDING' if passed else 'JOINT_REPAIR_REQUIRED','rows':rows,'source_root_status':roots,'exact_six_owned_removals':sorted(remove),'outside_contact_pair_status':outrows,'new_vias':3,'new_segments':12,'new_zones':0,'input_R44_receipt_SHA256':sha(q/'receipt.json'),'input_R32_receipt_SHA256':sha(rp/'receipt.json'),'input_R32_model_SHA256':sha(rp/'model.pkl'),'input_R25_receipt_SHA256':sha(bp/'receipt.json'),'ordinary_receipt_SHA256':sha(OUT/'ordinary-aperture-receipt.json'),'geometry_sha256':sha(OUT/'geometry.pkl'),'discrete_sha256':sha(OUT/'discrete.pkl'),'groups_sha256':sha(OUT/'groups.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'precision_state_restored_UUIDs':sorted(pids),'original_fill_retreat_ledger':cuts,'source_node_BOM_pose_limits_unchanged':True,'RTN_ports_not_merged_with_GND':True,'comparison_scope':'exact R25 retained physical relationships and R32 local delta; original198b/r06/r07 and corrected CORE source proof separate','protected24_R7_not_composed':True,'native_jobs':0,'board_written':False,'signed_mesh_drop_thermal_native_flash_refill_and_reference_gates':'OPEN'};write(OUT/'receipt.json',receipt);print(receipt['verdict'],sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
