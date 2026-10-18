"""Rebuild only the failed FIELD5 bridge on the accepted current physical context."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import regional_guarded_declared_projection_r140 as P
import contact_layout as C
import fast_contacts as F
import physical_reference_losses_r1 as REF
import owned_analytic_track_guards_r75 as TG
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from inventory import sha
BASE=H/'FIELD5-current-IO3-and-reference-preservation-search-base-r223'
assert not BASE.exists();BASE.mkdir()
bp=H/'R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(bp/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
g,h,b,z,a=pickle.loads((bp/'model.pkl').read_bytes());restore_bound_generated_precision_states(b,z);h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z)
rp=H/'REG-rebuilt-B3-on-wider-IO3-full-audit-r212';d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());removed=json.loads((H/'u11017-dead-spur-native-owned-recipe-r138/receipt.json').read_text(encoding='utf-8'))['delete_rows'];deleteids={r['uuid'] for r in removed};assert deleteids<={r['uuid'] for r in h['tracks']};h['tracks']=[t for t in h['tracks'] if t['uuid'] not in deleteids]+d['tracks'];h['vias']+=d['vias']
newq=[q for q in pickle.loads((rp/'new-owned-zones.pkl').read_bytes()) if q['uuid']!='938b9038-0f65-5de2-99ed-d6781afcb116']
for q in newq:
 for role in ('shape','zone_outline_shape'):q[role]=set_precision(q[role],1e-6,mode='pointwise')
# The current projection is only a search state. Do not import the failed R212 model.
from complete_geometry_r2 import gap
for q in z:
 if q['layer'] not in ('In1.Cu','In2.Cu','In4.Cu') or C.norm(q['net']) not in ('/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V'):continue
 own=[n['zone_outline_shape'] for n in newq if n['layer']==q['layer'] and gap(h,n['net'],q['net'])==.15 and C.norm(n['net'])!=C.norm(q['net'])]
 if own:
  cut=P.bounded_buffer(unary_union(own),.175)
  for role in ('shape','zone_outline_shape'):q[role]=set_precision(q[role].difference(cut),1e-6)
z+=newq;z,_=P.normalize_owned_via_guards({**h,'vias':d['vias']},z);z,_,_=TG.normalize_owned_track_guards({**h,'tracks':d['tracks']},z)
after,_=P.projected(g,{**h,'zones':[q for q in h['zones'] if C.norm(q['net'])=='/motherboard_power_entry/FIELD_5V']},z)
hard=[];bindings=[]
# Preserve complete actual current IO3 filled pieces, including plane-only
# relationships omitted from the earlier literal discrete-spine nomination.
for layer in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):
 shp=unary_union([q['shape'] for xs in F.graph(a,'/IO_3V3') for q in xs if q['kind']=='fill' and q['layer']==layer])
 if not shp.is_empty:hard.append({'uuid':'CURRENT_ACTUAL_IO3_FILL_'+layer,'net':'/IO_3V3','layer':layer,'shape':shp,'clearance_mm':.15});bindings.append({'kind':'actual_IO3_fill_preservation','layer':layer,'shape_sha256':P.digest(shp),'area_mm2':shp.area})
# All old source-rooted ground reference bodies remain hard, with exact physical
# caps and later native monitor footprint/pad polygons already in the base.
originalids={t['uuid'] for t in g['tracks']};tracks=[t for t in h['tracks'] if t['uuid'] in originalids]
for ground,ref,pin in [('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2')]:
 root=next(xs for xs in F.graph(a,ground) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs))
 for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]:
  source=unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==inner]);parts=[]
  for t in tracks:
   if t['layer']!=outer:continue
   body=REF.A.shape({'kind':'segment',**t})
   if body.intersects(source):parts.append(body.intersection(source))
  mask=unary_union(parts)
  if not mask.is_empty:hard.append({'uuid':'EXACT_CURRENT_RETAINED_REFERENCE_'+ground+'_'+inner,'net':ground,'layer':inner,'shape':mask,'clearance_mm':.25});bindings.append({'kind':'literal_source_reference','net':ground,'layer':inner,'sha256':P.digest(mask),'area_mm2':mask.area})
b['field_regulated_search_hard_nominees']={'planes':hard,'discrete':{'vias':[],'tracks':[]},'actual_peer_model_file':str((bp/'model.pkl').resolve()),'actual_peer_model_sha256':sha(bp/'model.pkl')}
(BASE/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(BASE/'receipt.json').write_text(json.dumps({'verdict':'SEARCH_ONLY_CURRENT_R214_FAILED_FIELD5_EXCLUDED','model_sha256':sha(BASE/'model.pkl'),'actual_R214_peer_sha256':sha(bp/'model.pkl'),'hard_bindings':bindings,'failed_R212_whole_model_not_used':True,'all_prospective_REG_source_contact_reference_gates':'OPEN'},indent=1)+'\n',encoding='utf-8')
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace("import guarded_power_projection_r44 as P","import regional_guarded_declared_projection_r140 as P")
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'","OUT=HERE/'FIELD5-actual-IO3-preserving-alternate-r223';BASE=HERE/'FIELD5-current-IO3-and-reference-preservation-search-base-r223'")
s=s.replace('for bank,net,ref,pin,policy in PORTS:',"for bank,net,ref,pin,policy in [x for x in PORTS if x[0]=='FIELD5']:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'","xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin'))==('R11071','1') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace('for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):','for margin in(8.,25.,60.):\n    for width in(.5,.35):')
s=s.replace("for a in sorted([q for q in xs if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area):",'for a in []: # no new holes in this bounded existing-barrel pass')
s=s.replace('native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)','construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)')
s=s.replace('controller-regulated-r76/','controller-field5-current-IO3-r223/').replace('.read_text()',".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
