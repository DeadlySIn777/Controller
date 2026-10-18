"""Move two owned new vias and adjacent segments for full ordinary SMD aperture."""
import copy,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source=HERE/'ground-escape-return-native-r7/result.json'
    out=HERE/'ground-escape-smd-aperture-r8'
    audit=HERE/'audit_ground_escape_r7.py'
    derived=HERE/'audit_reset_smd_aperture_r8.py'
    if out.exists() or derived.exists():raise ValueError('Fresh strengthened aperture audit required')
    plan=json.loads(source.read_bytes())
    route=next(row for row in plan['results'] if row['paths'])['paths'][0]
    old_at=[201.0,99.6];new_at=[201.0,99.8]
    old_ground=[200.906884,100.545425];new_ground=[200.906884,100.745425]
    changes=[]
    def replace(obj):
        if isinstance(obj,list):
            if obj==old_at:changes.append({'old':old_at,'new':new_at});return list(new_at)
            if obj==old_ground:changes.append({'old':old_ground,'new':new_ground});return list(new_ground)
            return [replace(v) for v in obj]
        if isinstance(obj,dict):return {k:replace(v) for k,v in obj.items()}
        return obj
    fixed=replace(route)
    for index,side in enumerate(['source_escape','target_escape']):
        via=fixed['new_signal_vias'][index]
        via['return_distance_mm']=math.dist(via['at'],via['new_return_stitch']['at'])
        fixed[side]['via']=copy.deepcopy(via)
    row=next(row for row in plan['results'] if row['paths']);row['paths'][0]=fixed
    plan['repair']='Owned source reset transition and companion shifted0.20mm together, preserving quantized0.95mm return spacing; every new signal/return drill must clear every SMD pad by0.25mm plus0.025mm planning margin. No aperture waiver.'
    out.mkdir();(out/'result.json').write_text(json.dumps(plan,indent=1)+'\n',encoding='utf-8')
    raw=audit.read_text()
    raw=raw.replace("OUT=HERE/'ground-escape-audit-r7'","OUT=HERE/'reset-smd-aperture-audit-r8'")
    raw=raw.replace("HERE/'ground-escape-return-native-r7/result.json'","HERE/'ground-escape-smd-aperture-r8/result.json'")
    marker="smd.query(item['hole'].buffer(.125),predicate='intersects')"
    if raw.count(marker)!=1:raise ValueError('Exact original aperture marker differs')
    raw=raw.replace(marker,"smd.query(item['hole'].buffer(.275),predicate='intersects')")
    derived.write_text(raw,encoding='utf-8')
    (out/'derivation.json').write_text(json.dumps({'original_plan_sha256':sha(source),'original_audit_sha256':sha(audit),'derived_audit_sha256':sha(derived),'coordinate_changes':changes,'all_other_track_via_drill_pitch_domain_reference_contact_thresholds_preserved':True,'ordinary_SMD_drill_aperture_minimum_mm':.25,'planning_guard_mm':.025,'old_failed_aperture_preserved':'sbc-power/independent-geometry-audit-r2.json','native_jobs':0,'board_emitted':False,'adopted':False},indent=1)+'\n',encoding='utf-8')
    print(str(derived),flush=True)
if __name__=='__main__':main()
