"""Preserve the diagnostic R4 planner and strengthen the next construction."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=H/'construct_protected24_dogbones_r4.py';dst=H/'construct_protected24_dogbones_r5.py'
    assert not dst.exists()
    code=src.read_text(encoding='utf-8')
    replacements={
        "OUT=ROOT/'protected24-dogbones-r4'":"OUT=ROOT/'protected24-dogbones-r5'",
        "controller-protected24-dogbone-r4/":"controller-protected24-dogbone-r5/",
        "{'shape':s,'uuid':q['uuid']} for q in g['pads']":"{'shape':s,'uuid':q['uuid'],'net':q.get('net','')} for q in g['pads']",
        "'uuid':v['uuid']} for v in g['vias']":"'uuid':v['uuid'],'net':v['net']} for v in g['vias']",
        "for drill in drills:dd.append((drill['uuid'],drill['shape'].buffer(.275)))":"for drill in drills:\n                if not drill['net'] or drill['net']!=raw:dd.append((drill['uuid'],drill['shape'].buffer(.275)))",
        "hole.buffer(.05).intersects(smd[int(j)]['shape']) for j in st.query(hole.buffer(.05),predicate='intersects')":"hole.distance(smd[int(j)]['shape'])<.275-1e-7 for j in st.query(hole.buffer(.275),predicate='intersects')",
        "if any(hole.distance(drills[int(j)]['shape'])<.275-1e-7 for j in dt.query(hole.buffer(.275),predicate='intersects')):continue":"if any(hole.distance(drills[int(j)]['shape'])<.275-1e-7 for j in dt.query(hole.buffer(.275),predicate='intersects')):continue\n                            if any(hole.distance(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=32))<.275-1e-7 for v in vias):continue",
        "for gi in wanted:\n            if gi in connected:continue":"for gi in wanted:\n            if gi in connected:continue\n            print(bank,gi,'SEARCH_STRONG_APERTURE_DOGBONE',flush=True)",
        "for a in pads[:24]:\n                anchor":"for a in pads[:24]:\n                print(bank,gi,'PAD',a.get('ref'),a.get('pin'),a['layer'],flush=True)\n                anchor",
        "'prospective_all6_annuli_screened':True":"'prospective_all6_annuli_screened':True,'every_SMD_drilled_aperture_guard_mm':.275,'all_old_and_previous_new_drill_spacing_mm':.275",
        "'all_current_contacts_full_mutual_native_aperture_flash_fill_gates':'OPEN'":"'all_current_contacts_full_mutual_native_aperture_flash_fill_gates':'OPEN','same_raw_PTH_source_plane_overlap':'Positive annulus required; same-net plated hole is not a foreign plane clearance obstacle'",
    }
    for old,new in replacements.items():
        if code.count(old)!=1:raise ValueError('Exact derivation anchor differs: '+old)
        code=code.replace(old,new)
    compile(code,str(dst),'exec');dst.write_text(code,encoding='utf-8')
    out=H/'protected24-dogbones-r5-derivation.json'
    out.write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'replacements':replacements,'previous_run_disposition':'R4 intentionally stopped before any accepted recipe; false source-annulus drill obstacle and weak new via guards corrected','native_rule_bytes_changed':False,'native_jobs':0,'board_written':False},indent=1)+'\n',encoding='utf-8')
    print(sha(out))
if __name__=='__main__':main()
