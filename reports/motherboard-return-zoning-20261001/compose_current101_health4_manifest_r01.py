"""Bounded receipt composition; proof must be rerun on the exact current board."""
from pathlib import Path
import hashlib,json,argparse

ap=argparse.ArgumentParser()
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args()
if a.out.exists():
    raise ValueError('Fresh immutable manifest path required')
base=Path('reports/motherboard-return-zoning-20261001/C11087-moved-bypass-ground-transfer-r01/combined100-retained-plus1-replacement-manifest.json')
health=Path('reports/motherboard-power-entry-20261001/health-supply-r99/health-four-local-owner-manifest-r02.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads(base.read_text());h=json.loads(health.read_text())
assert len(r['owned_loops'])==101
assert [(x['cap'],x['owner']) for x in h['actual_local_loops']]==[
    ('C11078','U11019'),('C11079','U11020'),('C11080','U11025'),('C11081','U11026')]
assert h['exclude_long_distribution_copper']
refs={x['ref']for x in r['owned_loops']}
for x in h['actual_local_loops']:
    assert x['cap'] not in refs
    assert (x['owner_power_pin'],x['owner_return_pin'],x['cap_power_pin'],x['cap_return_pin'])==('5','2','1','2')
    r['owned_loops'].append(dict(ref=x['cap'],owner=x['owner'],category='local_bypass',
        new_UUIDs=x['local_positive_copper']+x['local_return_copper'],retained=True,
        actual_owning_signal_return_pairs_connected=True,
        disposition='Exact separately native-proved receiving loop; current full-reference proof is mandatory. Long distribution excluded.'))
r['composition']={
    'base_current101_manifest':str(base),'base_current101_manifest_sha256':sha(base),
    'exact_health4_local_manifest':str(health),'exact_health4_local_manifest_sha256':sha(health),
    'retained_historical_groups':100,'one_actual_C11087_replacement':1,'new_health_local_groups':4,
    'total_groups':105,'composition_is_not_current_board_proof':True,
    'current_native_SOURCE_pairs_full_reference_annuli_and_return_proof_required':True,
    'loaded_supply_thermal_all_temperature_and_20ms_qualification_claim':False,
}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'composition_only':True,'groups':105,'manifest_sha256':sha(a.out)}))
