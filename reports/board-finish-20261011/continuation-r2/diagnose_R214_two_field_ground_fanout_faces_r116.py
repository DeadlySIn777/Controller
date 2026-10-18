"""Preserve finite R115 no-path geometry and exact branch attribution."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'nominate_R214_two_bare_field_ground_pads_r115.py'
code=source.read_text();assert code.count("OUT=H/'R214-two-bare-field-ground-ordinary-fanout-nominees-r115'")==1
code=code.replace("OUT=H/'R214-two-bare-field-ground-ordinary-fanout-nominees-r115'","OUT=H/'R214-two-field-ground-fanout-face-diagnosis-r116'")
needle="            options=[]\n"
extra="""            reachable=unary_union(faces);common=reachable.intersection(landing)
            detail={'ref':ref,'radius_mm':radius,'pad_layer':layer,'pad_mm':[point.x,point.y],'landing_outer_reachable_area_mm2':common.area,'outer_reachable_landing_distance_mm':reachable.distance(landing),'source_distances_mm':{l:common.distance(sources[l]) if not common.is_empty else None for l in LAYERS}}
            print('R116_FACE_DIAG',detail,flush=True)
            for role,sh in [('landing',landing),('outer',reachable),('common',common)]:
                (OUT/(ref+'-'+str(radius)+'-'+role+'.wkb')).write_bytes(sh.wkb)
            for l in LAYERS:(OUT/(ref+'-'+str(radius)+'-source-'+l+'.wkb')).write_bytes(sources[l].intersection(query).wkb)
            write(OUT/(ref+'-'+str(radius)+'-diagnosis.json'),detail)
"""
assert code.count(needle)==1;code=code.replace(needle,extra+needle)
exec(compile(code,str(source),'exec'))
