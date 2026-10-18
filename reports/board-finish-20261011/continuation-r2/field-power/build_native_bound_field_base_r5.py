"""Bind root1beb+SBC owned model to exact eedf discrete native attestation."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import complete_geometry_r2 as G
from inventory import sha
from fast_contacts import graph
OUT=HERE/'native-bound-field-base-r5'

def main():
    assert not OUT.exists();OUT.mkdir();np=HERE.parent/'sbc-native-contract-r3-layer-ids';native=json.loads((np/'receipt.json').read_text());assert native['candidate_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';actual=json.loads((np/'native-parity.json.actual-vias.json').read_text());assert actual['board_sha256']==native['candidate_sha256'];g,h,tail,binding,zones=G.model(final_frozen=True,with_field=True,coupled_revision='r7',new_root_base=True,allow_prior_geometry=True);vs={v['uuid']:v for v in h['vias']}
    for q in actual['rows']:
        v=vs[q['expected']['uuid']];assert v['net']==q['actual_net_raw'];assert max(abs(v[k]-q['actual_mm'][i]) for i,k in enumerate(('x','y')))<1e-6;assert abs(v['d']-q['actual_diameter_mm'])<1e-6 and abs(v['drill']-q['actual_drill_mm'])<1e-6;v['flashed']=q['actual_flashed_layers']
    pp=json.loads((np/'native-parity.json').read_text());assert (len(h['pads']),len(h['tracks']),len(h['vias']))==(pp['summary']['board_pads'],pp['board_copper']['tracks_and_arcs'],pp['board_copper']['vias']);before,retreats=G.projected(g,h,zones);(OUT/'model.pkl').write_bytes(pickle.dumps({'old':g,'discrete':h,'projected':before,'new_zones':zones},protocol=5));old=pickle.loads((HERE/'coupled-logic-base-r1/groups.pkl').read_bytes())['old_groups'];new=graph(before,'/LOGIC_GND');(OUT/'groups.pkl').write_bytes(pickle.dumps({'old_groups':old,'new_groups':new},protocol=5));receipt={'verdict':'EXACT_NATIVE_DISCRETE_COUNTS_AND_68_VIA_GEOMETRY_AND_FLASHES_BOUND_NO_FILL_CLAIM','model_sha256':sha(OUT/'model.pkl'),'groups_sha256':sha(OUT/'groups.pkl'),'native_discrete_sha256':native['candidate_sha256'],'native_contract_receipt_sha256':sha(np/'receipt.json'),'native_68_via_attestation_sha256':sha(np/'native-parity.json.actual-vias.json'),'loader_binding':binding,'fresh_geometry_native_source_root_198b_fills':True,'new_zones_are_historical_r7_before_SBC_IO3_final_restoration':True,'native_jobs':0};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
