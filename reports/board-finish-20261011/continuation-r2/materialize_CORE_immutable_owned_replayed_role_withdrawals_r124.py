"""Replay only documented generated role operation grids; never native fills."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'materialize_CORE_R112_immutable_owned_fill_records_r121.py';wrapper=source.read_text()
needle="exec(compile(code,str(source),'exec'))";assert wrapper.count(needle)==1
extra="""code=code.replace("out=H/'CORE-R112-immutable-native-and-owned-filled-records-r121'","out=H/'CORE-immutable-owned-replayed-role-withdrawals-r124'")
needle="immutable_tuple=pickle.loads(immutable_head.read_bytes());prior_owned=";assert code.count(needle)==1
code=code.replace(needle,"immutable_tuple=pickle.loads(immutable_head.read_bytes());old_replay=PS.restore_bound_generated_precision_states(immutable_tuple[2],immutable_tuple[3]);put(out/'exact-R214-generated-role-operation-replay.json',old_replay);prior_owned=")
needle="oldshape=set_precision(original['shape'],0);newshape=set_precision(q['shape'],0);assert oldshape.wkb==original['shape'].wkb and newshape.wkb==q['shape'].wkb";assert code.count(needle)==1
code=code.replace(needle,"oldshape=original['shape'];newshape=q['shape'];assert set_precision(oldshape,1e-6,mode='pointwise').wkb==oldshape.wkb and set_precision(newshape,1e-6,mode='pointwise').wkb==newshape.wkb")
needle="remaining=base_zero.difference(withdrawal);";assert code.count(needle)==1
code=code.replace(needle,"cut_zero=set_precision(withdrawal,0);assert cut_zero.wkb==withdrawal.wkb;remaining=base_zero.difference(cut_zero);")
code=code.replace('R121_','R124_')
"""
wrapper=wrapper.replace(needle,extra+needle)
exec(compile(wrapper,str(source),'exec'))
