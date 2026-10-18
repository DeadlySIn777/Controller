"""Preserve R417 failed aggregate proof; reserve its literal local remainder."""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'compose_FIELD5_owned_valid_boundary_original_cut_rim_r417.py'
ns={'__file__':str(owner),'__name__':'_generate_exact_owned_valid_rim_source'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'];s=s.replace('minimal-R155-valid-owned-boundary-cut-rim-restoration-r417','minimal-R155-strict-aggregate-boundary-cut-rim-restoration-r423')
s=s.replace('import immutable_local_fill_subtraction_r254 as IM','import immutable_restored_fill_aggregate_subtraction_r421 as IM')
s=s.replace("'R413_topology_failure_preserved':True","'R413_topology_failure_preserved':True,'R417_aggregate_literal_gain_failure_preserved':True,'strict_restored_aggregate_helper':'immutable_restored_fill_aggregate_subtraction_r421.py'")
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
