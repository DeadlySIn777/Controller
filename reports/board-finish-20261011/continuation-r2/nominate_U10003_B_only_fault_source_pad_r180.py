"""Restore the fault on B without a new signal-via transition."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'route_U10003_fault_existing_barrel_replacement_r128.py';code=source.read_text()
code=code.replace('fault-two-existing-barrel-one-layer-replacement-r128','B-only-fault-source-pad-nomination-r180')
code=code.replace('field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl','U10003-sparse-current-ground-fault-construction-r153/model.pkl').replace('87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e','2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8')
code=code.replace("IDS={'bd3e65f9-fe77-4a1f-88a1-c704d85af39f','ca9b0c5d-8d6f-44b2-8bec-780b6f1b3f3f','774ec021-d81e-471e-a8c8-0ea85fa50f67'}","IDS={'c4e9e150-1f69-573b-bb70-d4d00441eba5','cc078be4-6bc9-5dd0-9194-ede561b48077'}")
needle="roots=pickle.loads(mp.with_name('groups.pkl').read_bytes())[GND];ground=next(xs for xs in roots if any(q['kind']=='pad' and (q['ref'],q['pin'])==('J11003','2') for q in xs))";assert code.count(needle)==1
replace="import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K;_,roots=K.physical(full,GND,K.hole_context(full));ground=K.root(roots,'J11003','2')"
code=code.replace(needle,replace)
needle="start,end=[Point(v['x'],v['y']) for v in pairs];rows=[];answer=None";assert code.count(needle)==1
code=code.replace(needle,"pad=next(p for p in h['pads']if(p['ref'],p['num'])==('U10003','10'));assert C.norm(pad['net'])==NET;start=Point(pairs[0]['x'],pairs[0]['y']);end=Point(pad['x'],pad['y']);rows=[];answer=None")
code=code.replace("for layer in ('In2.Cu','In3.Cu','F.Cu','In4.Cu'):","for layer in ('B.Cu',):")
code=code.replace('free=win.intersection(reference).difference(unary_union(obstacles))','free=win.difference(unary_union(obstacles))')
code=code.replace('if any(gap.values()):continue','paired_reference_not_qualified=any(gap.values()) # retain raw failures; nomination only')
code=code.replace("'old_cap_before_source_support_NOT_YET_QUALIFIED':True","'old_cap_before_source_support_NOT_YET_QUALIFIED':True,'new_signal_vias':0,'source_pad_UUID':pad['uuid'],'paired_reference_not_qualified':paired_reference_not_qualified,'saved_operator_existing_port_return_window_mm':[.90,1.0]")
code=code.replace('FAULT_EXISTING_BARREL_REPLACEMENT_NOMINATED_PAIRED_RETURN_AND_ALL_GATES_OPEN','B_ONLY_EXISTING_SIGNAL_PORT_AND_REAL_PAD_ROUTE_NOMINATION_RETURN_AND_ALL_GATES_OPEN')
code=code.replace('controller-U10003-fault-r128/','controller-U10003-B-only-fault-r180/')
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
