from pathlib import Path
HERE=Path(__file__).resolve().parent
src=HERE/'qualify_di6_native_existing_target_r20.py';dst=HERE/'qualify_di6_native_existing_target_r22.py';assert not dst.exists();t=src.read_text().replace("out=HERE/'di6-native-existing-target-return-r20.json'","out=HERE/'di6-native-existing-target-return-r22.json'")
t=t.replace("radius=.3+max(.15,max(n['exact_source_local_clearance_mm'] for n in near))+.025;assert radius==.575;", "radius_IU=300000+max(150000,max(round(n['exact_source_local_clearance_mm']*1000000) for n in near))+25000;assert radius_IU==575000;radius=radius_IU/1000000;")
t=t.replace("'native_candidate_sha256':", "'preserved_R20_failed_float_sum_assertion_source_sha256':C.sha(A.read(HERE/'qualify_di6_native_existing_target_r20.py')),'exact_existing_target_disk_radius_IU':radius_IU,'native_candidate_sha256':")
assert t!=src.read_text();dst.write_text(t);print(dst)
