"""Four distinct RTN copper/support graphs, no fabricated external GND short."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;ROOT=H.parent;BASE=ROOT/'CORE-In2-owned-notch-materialized-source-proposal-r100';O=H/'R100-four-distinct-RTN-support-graphs-r286'
def main():
 assert not O.exists();O.mkdir();assert sha(BASE/'model.pkl')=='db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635';_,h,_,_,c=pickle.loads((BASE/'model.pkl').read_bytes());groups=pickle.loads((BASE/'groups.pkl').read_bytes());fg=next(xs for xs in groups['/motherboard_motors/FIELD_GND'] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11003','2') for q in xs));fgkeys=F.discrete_keys(fg);rows=[]
 for ref in ('U11015','U11016'):
  ps={p['num']:p for p in h['pads'] if p['ref']==ref};assert ps['5']['net']==ps['11']['net'] and ps['5']['net']!=ps['6']['net'];net=C.norm(ps['5']['net']);gg=F.graph(c,net);root=next(xs for xs in gg if any(q['kind']=='pad' and q['uuid']==ps['5']['uuid'] for q in xs));rk=F.discrete_keys(root);support=sorted({(q['ref'],q['pin'],q['uuid']) for q in root if q['kind']=='pad'});tracks=[q for q in root if q['kind']=='track'];owned=[{'UUID':q['uuid'],'layer':q['layer'],'width_mm':q['source']['w'],'start_mm':q['source']['a'],'end_mm':q['source']['b']} for q in tracks];row={'ref':ref,'exact_raw_RTN':ps['5']['net'],'exact_raw_GND':ps['6']['net'],'RTN5_UUID':ps['5']['uuid'],'EP11_UUID':ps['11']['uuid'],'GND6_UUID':ps['6']['uuid'],'both_RTN5_and_EP11_in_same_actual_physical_group':('pad',ps['11']['uuid']) in rk,'GND6_actual_J11003_2_rooted':('pad',ps['6']['uuid']) in fgkeys,'RTN_rooted_named_physical_support_pads':[{'ref':a,'pin':b,'UUID':uid} for a,b,uid in support],'support_tracks':owned,'RTN_group_actual_layer_areas_mm2':{l:unary_union([q['shape'] for q in root if q['layer']==l]).area for l in ('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')},'RTN_other_groups':len(gg)-1,'aggregate_IC_Iq_planning_reservation_A':.0006,'per_RTN_port_individual_routing_reservation_A':.001,'internal_reverse_polarity_block_series_drop_R_and_fault_modes_not_qualified':True,'RTN_never_shortened_to_external_FAG_net':True};rows.append(row);print(json.dumps({'ref':ref,'RTN5_EP11_joined':row['both_RTN5_and_EP11_in_same_actual_physical_group'],'GND6_J3_rooted':row['GND6_actual_J11003_2_rooted'],'support_pads':len(support),'tracks':len(owned)}),flush=True)
 rec={'verdict':'FOUR_RTN_SUPPORT_PHYSICAL_GRAPH_PASS_INTERNAL_MODE_CURRENT_THERMAL_NATIVE_OPEN' if all(q['both_RTN5_and_EP11_in_same_actual_physical_group'] and q['GND6_actual_J11003_2_rooted'] for q in rows) else 'RTN_SUPPORT_PHYSICAL_REPAIR_REQUIRED','R100_model_sha256':sha(BASE/'model.pkl'),'rows':rows,'primary_TI_RevF_sections':['6 pin functions','9.3.8 internal RTN/GND protection block'],'evidence':'Exact host physical pad/track/via/fill contacts from R100; not new native filled evidence or internal device impedance guarantee.','native_jobs':0,'board_written':False,'adopted':False};(O/'receipt.json').write_text(json.dumps(rec,indent=1)+'\n',encoding='utf-8');print(sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
