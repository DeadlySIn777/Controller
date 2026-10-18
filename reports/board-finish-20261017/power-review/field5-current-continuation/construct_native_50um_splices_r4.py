"""Six native source changes with explicit old filled-band removal targets.

Some native filled copper lies outside its saved literal outline. Those desired
negative target pieces are inventoried separately, and are not falsely claimed
to be the literal source-outline set difference. Only a fresh native fill can
confirm their physical removal. This file never calls a native fill.
"""
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'construct_native_50um_splices.py'
s=SOURCE.read_text().replace("OUT=HERE/'native-50um-splice-construction-r3'","OUT=HERE/'native-50um-splice-construction-r4'").replace("CON=HERE/'bounded-current-In2-widening-construction-r2'","CON=HERE/'bounded-current-In2-widening-construction-r4'")
s=s.replace("mask=delta.buffer(gap,quad_segs=128)","mask=delta.buffer(gap+.05001,quad_segs=128)")
s=s.replace("actualcut=oldfill.intersection(negative)","actualcut=oldfill.intersection(negative.union(mask));outside_literal=actualcut.difference(negative)")
s=s.replace("negative_rows[z['uuid']]=negative;cuts.append", "negative_rows[z['uuid']]=negative.union(mask);(OUT/(z['uuid']+'-actual-Cu-negative-target.wkb')).write_bytes(actualcut.wkb);(OUT/(z['uuid']+'-negative-fill-target-outside-literal-source-cut.wkb')).write_bytes(outside_literal.wkb);cuts.append")
s=s.replace("'native_Cu_cut':sm(actualcut)","'native_Cu_cut':sm(actualcut),'native_fill_negative_target_outside_literal_intent_cut':sm(outside_literal),'source_cut_extra_band_reservation_mm':.05001,'native_fill_required_to_prove_target_removal':True")
s=s.replace("'native_serialization_source_contacts_current_ground_return_thermal_and_AFTERMATH':'OPEN'","'native_serialization_source_contacts_current_ground_return_thermal_and_AFTERMATH':'OPEN; actual negative Cu targets outside literal source cuts explicitly require fresh native fill'")
exec(compile(s,str(SOURCE),'exec'),globals())
