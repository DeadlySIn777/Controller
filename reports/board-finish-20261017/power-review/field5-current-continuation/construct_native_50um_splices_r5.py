"""Explicitly support complete negative retirement of an empty-fill FG role."""
from pathlib import Path
import shapely
import native_lattice_boolean_splice as N
original=N.splice
def splice(old,boolean,positive):
    if boolean.is_empty:
        assert not positive
        return shapely.GeometryCollection(),{'positive':False,'literal_new_subset_of_old':True,'entire_literal_old_intent_retired':True,'selected_margin_nm':0,'no_area_or_distance_waiver':True}
    return original(old,boolean,positive)
N.splice=splice
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_native_50um_splices_r4.py').read_text()
s=s.replace("'native-50um-splice-construction-r4'","'native-50um-splice-construction-r5'")
exec(compile(s,str(HERE/'construct_native_50um_splices_r4.py'),'exec'),globals())
