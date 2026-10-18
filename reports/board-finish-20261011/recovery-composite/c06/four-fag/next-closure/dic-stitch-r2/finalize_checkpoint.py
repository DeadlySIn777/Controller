import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
out=HERE/'final-checkpoint.json'
if out.exists():raise ValueError('Distinct immutable final receipt required')
prior=HERE/'checkpoint.json'
packet=json.loads(prior.read_bytes())
for path,digest in packet['files_sha256'].items():
    if sha(path)!=digest:raise ValueError('Checkpoint file changed:'+path)
packet['schema']='frozen-dic-ownstitch-final-checkpoint-r2'
packet['prior_checkpoint_sha256']=sha(prior)
packet['historical_report']=str((HERE.parent/'REPORT.txt').resolve())
packet['historical_report_sha256']=sha(HERE.parent/'REPORT.txt')
packet['current_report']=str((HERE/'REPORT.txt').resolve())
packet['current_report_sha256']=sha(HERE/'REPORT.txt')
packet['owned_tail_trim_diagnosis']={'uuid':'2b903a9f-df92-4263-bf2c-3a15ea640cab','width_mm':.8,'layer':'In3.Cu','old_endpoints_mm':[[353.3,201.7],[353.3,203.2]],'retained_actual_all6_flashed_via':'48bb17dc-e15c-4500-87b2-9784faa6bd96','retained_via_point_mm':[353.45,202.4],'pure_copper_subset_trim_mm':[[353.3,202.4],[353.3,203.2]],'recentered_replacement_mm':[[353.45,202.4],[353.3,203.2]],'distinction':'Recentered0.8mm replacement adds a small copper wedge, needs separate full clearance/contact construction; literal same-x trim is a copper subset but warning behavior remains native-open','either_applied':False}
packet['search_bounds']={'window_growth_mm':[8,14],'deadline_s_per_window':100,'max_signal_sites_per_side':8,'max_return_sites_per_signal':6,'max_whole_pairs':12,'grid_mm':.1,'ground_stub_target_neighborhood_mm':2.5,'max_ground_stub_length_mm':5,'stub_deadline_s':1.5,'stub_node_cap':18000,'actual_signal_sites_identified_per_side':[2,7],'actual_signal_sites_processed_per_side_each_window':[2,2],'scope':'Sampled-site/window/time bound only; no global infeasibility'}
packet['files_sha256'][str((HERE/'REPORT.txt').resolve())]=sha(HERE/'REPORT.txt')
packet['files_sha256'][str(Path(__file__).resolve())]=sha(__file__)
out.write_text(json.dumps(packet,indent=1)+'\n',encoding='utf-8')
print(json.dumps({'receipt':str(out),'sha256':sha(out),'verdict':packet['verdict']}))
