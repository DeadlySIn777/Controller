"""Use the same real common old-In4/current-In2 electrodes for the third sheet."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'solve_prospective_real_corridor_r7.py').read_text().replace("OUT=HERE/'prospective-real-corridor-two-level-current-r7'","OUT=HERE/'prospective-real-corridor-common-electrode-current-r8'")
s=s.replace("BASE=HERE/'actual-native-sheet-two-level-r1'","BASE=HERE/'old-In4-vs-new-In2-matched-electrodes-r1'")
s=s.replace("BASE/'actual-e19f-In2-source-contact.wkb'","BASE/'exact-common-real-source-electrode.wkb'").replace("BASE/'actual-0901-In2-target-contact.wkb'","BASE/'exact-common-real-target-electrode.wkb'")
s=s.replace("'whole_actual_In2_e19f_finite_source_to_0901_finite_target'","'new_In2_exact_common_finite_electrodes'")
exec(compile(s,str(HERE/'solve_prospective_real_corridor_r7.py'),'exec'),globals())
