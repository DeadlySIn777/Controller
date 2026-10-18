"""Exact protected-port simplex bound for the coupled U10017 nine-pad branch."""
import hashlib,json,math,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):Path(p).write_text(json.dumps(x,indent=1)+'\n')
mp=H/'field-power/u17-u10017-reference-safe-incremental-audit-r162/model.pkl';mr=mp.with_name('receipt.json')
assert sha(mp)=='051715d71b8650923695211f4560584ed0bd44e6c573681a3fe4767eb9b9c566';assert sha(mr)=='10bae09e7343683d918e333a19e43b90906b15fb794fcdd7be401ef7176b609a'
old,h,b,z,current=pickle.loads(mp.read_bytes())
ap=H/'protected24-port-allocation-r1/receipt.json';a=json.loads(ap.read_bytes());assert a['verdict']=='PASS_PROTECTED24_PLANNING_KCL_EXACT_NATIVE_ENDPOINTS_CURRENT_MESH_OPEN'and len(a['terms'])==57 and all(abs(x)<1e-12 for x in a['KCL_residual_a'].values())
refs=[('C19028','1'),('U19004','1'),('C10031','1'),('R19021','1'),('U19018','8')]+[('U10017',str(i))for i in(34,35,36,37)]
pads={p['uuid']:p for p in current['pads']};selected={p['uuid']for p in h['pads']if(p['ref'],p['num'])in refs};assert len(selected)==len(refs)==9
net='/motherboard_power_entry/FIELD_B_24V_PROTECTED';assert all(C.norm(pads[uid]['net'])==net for uid in selected)
for t in a['terms']:
 for e in t['eligible_physical_endpoints']:
  p=pads[e['physical_pad_uuid']];assert p['net']==e['raw_net']and(p['ref'],p['num'])==(e['ref'],e['pin'])
def bounds(ids):
 impacts=[]
 for t in a['terms']:
  if t['domain']!='FB':continue
  ports={e['physical_pad_uuid']for e in t['eligible_physical_endpoints']};hits=ids&ports
  if not hits:continue
  v=t['signed_supply_current_a'];lo,hi=(v,v)if hits==ports else(min(v,0.),max(v,0.))
  impacts.append({'term':t['name'],'kind':t['kind'],'conserved_signed_total_a':v,'signed_branch_interval_a':[lo,hi],'all_eligible_ports_in_branch':hits==ports,'branch_exact_ports':[{'ref':pads[uid]['ref'],'pin':pads[uid]['num'],'uuid':uid}for uid in sorted(hits)],'eligible_term_ports_total':len(ports)})
 lo=math.fsum(x['signed_branch_interval_a'][0]for x in impacts);hi=math.fsum(x['signed_branch_interval_a'][1]for x in impacts)
 return {'signed_nodal_injection_interval_a':[lo,hi],'conservative_single_cut_magnitude_a':max(abs(lo),abs(hi)),'term_impacts':impacts}
out=H/'u10017-nine-pad-protected-bypass-current-bound-r48';assert not out.exists();out.mkdir();nominated=bounds(selected);put(out/'nine-pad-simplex-checkpoint.json',nominated)
gs=F.graph(current,net);root=next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==('U11006','17')for q in xs));rootids={q['uuid']for q in root if q['kind']=='pad'};assert selected<=rootids
vid='c55416b9';via=next(v for v in h['vias']if v['uuid'].startswith(vid));assert via['d']==.6 and via['drill']==.3
cut={**current,'vias':[v for v in current['vias']if v['uuid']!=via['uuid']]};cuts=F.graph(cut,net);sr=next(xs for xs in cuts if any(q['kind']=='pad'and(q['ref'],q['pin'])==('U11006','17')for q in xs));detached=rootids-{q['uuid']for q in sr if q['kind']=='pad'};actual=bounds(detached)
report={'verdict':'PASS_EXACT_NINE_PAD_PROTECTED_SIMPLEX_ALLOCATION_GRAPH_CUT_CURRENT_MESH_NATIVE_OPEN','model_sha256':sha(mp),'model_receipt_sha256':sha(mr),'protected57_allocation_sha256':sha(ap),'nine_pad_exact_UUIDs':sorted(selected),'nominated_branch':nominated,'actual_source':'U11006.17/.18','barrel_uuid':via['uuid'],'barrel_diameter_drill_mm':[.6,.3],'actual_single_barrel_cut_detached_pads':[{'ref':pads[uid]['ref'],'pin':pads[uid]['num'],'uuid':uid}for uid in sorted(detached)],'exact_nine_pad_set_is_whole_detached_branch':detached==selected,'single_barrel_cut_bound':actual if detached else None,'non_dominating_barrel_current':'UNSOLVED_NO_ZERO_CURRENT_INFERENCE'if not detached else None,'all57_terms_and_domain_KCL_preserved':True,'no_equal_pad_sharing':True,'group_extrema_not_independently_simultaneous':True,'ideal_cap_DC':'zero ideal DC; conserved5mA margin allocated across actual eligible ports, startup/ripple/Cdvdt separately OPEN','sheet_neck_barrel_drop_thermal_transient_ratings':'OPEN','source_board_written':False,'native_jobs':0,'adopted':False,'script_sha256':sha(__file__)}
put(out/'receipt.json',report);print('R48_BOUND',nominated['signed_nodal_injection_interval_a'],'ACTUAL_CUT',len(detached),actual['signed_nodal_injection_interval_a'],'EXACT9',detached==selected,sha(out/'receipt.json'))
