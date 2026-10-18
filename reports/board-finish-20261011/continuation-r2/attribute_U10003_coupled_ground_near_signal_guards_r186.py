"""Attribute exact blockers at several compliant-distance return coordinates."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_fault_coupled_ground_barrels_r147.py';code=source.read_text()
code=code.replace('barrel-nominees-r147','coupled-ground-near-signal-guard-attribution-r186')
code=code.replace("for d in('field-power','sbc-power'):","for d in('field-power','sbc-power','coupled-recovery'):")
code=code.replace('field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl','U10003-preserved-branch-exact-two-port-reference-construction-r176/model.pkl').replace('87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e','c13b478b0cea7b09a510c221913d3a4d0774fcc74042605c17d69b35b37a9d20')
needle="hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in ids]+r['repair']['tracks']};records,trees=F.build({**hard,'zones':[]});groups=pickle.loads(mp.with_name('groups.pkl').read_bytes());root=next(xs for xs in groups[NET]if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs))"
assert code.count(needle)==1
replacement="ownvia='ef759308-e664-5253-b016-ff17794eac74';ownstub='18ddb0fe-6821-5fe9-b71b-dc25ea06443b';roles={'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'};h={**h,'tracks':[t for t in h['tracks']if t['uuid']!=ownstub],'vias':[v for v in h['vias']if v['uuid']!=ownvia]};full={**full,'tracks':h['tracks'],'vias':h['vias'],'zones':[q for q in full['zones']if q['uuid']not in roles]};z=[q for q in z if q['uuid']not in roles];hard=h;records,trees=F.build({**hard,'zones':[]});import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K;_,groups=K.physical(full,NET,K.hole_context(full));root=K.root(groups,'J11003','2')"
code=code.replace(needle,replacement)
start=code.index(' sites=[');end=code.index('\n rows=[];accepted=[]',start)
code=code[:start]+" sites=[(216.04,143.32),(216.10,143.32),(216.2,143.33),(216.3,143.35),(216.4,143.37),(216.5,143.42)]"+code[end:]
code=code.replace("row={'site_mm':[x,y]","row={'distance_to_signal_mm':pt.distance(Point(216.078702,144.270524)),'saved_operator_window_mm':[.90,1.0],'site_mm':[x,y]")
code=code.replace("'exact_three_fault_deletes':sorted(ids)","'no_original_fault_deletions':True,'exact_unadopted_primary_ground_withdrawal':[ownvia,ownstub,*sorted(roles)]")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
