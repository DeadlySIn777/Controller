"""Read-only exact obstacle attribution for compliant clock relocation sites."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_fault_coupled_ground_barrels_r147.py';code=source.read_text()
code=code.replace('barrel-nominees-r147','clock-relocation-specific-guard-attribution-r202').replace("NET='/motherboard_motors/FIELD_GND'","NET='/motherboard_do/DOA_SCLK_FIELD'")
code=code.replace("for d in('field-power','sbc-power'):","for d in('field-power','sbc-power','coupled-recovery'):")
code=code.replace('field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl','U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl').replace('87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e','dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5')
needle="hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in ids]+r['repair']['tracks']};records,trees=F.build({**hard,'zones':[]});groups=pickle.loads(mp.with_name('groups.pkl').read_bytes());root=next(xs for xs in groups[NET]if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs))";assert code.count(needle)==1
replacement="oldclock=next(v for v in h['vias']if v['uuid']=='1f45e002-4f40-4087-bbed-3be260272d8f');h={**h,'vias':[v for v in h['vias']if v['uuid']!=oldclock['uuid']]};full={**full,'vias':h['vias']};hard=h;z=[q for q in z if q['uuid']not in{'bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a','9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}];records,trees=F.build({**hard,'zones':[]});import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K;_,groups=K.physical(full,'/motherboard_motors/FIELD_GND',K.hole_context(full));root=K.root(groups,'J11003','2')"
code=code.replace(needle,replacement)
start=code.index(' sites=[');end=code.index('\n rows=[];accepted=[]',start);code=code[:start]+" sites=[(216.35,142.44),(216.45,142.49),(216.5,142.49),(216.55,142.54),(216.58,144.035)]"+code[end:]
code=code.replace("row={'site_mm':[x,y]","row={'candidate_distance_to_actual_ground_mm':pt.distance(Point(215.97,143.29)),'saved_return_window_mm':[.90,1.0],'exact_existing_clock_native_mask':oldclock['flashed'],'screen_all6_conservative_caps':True,'site_mm':[x,y]")
code=code.replace("'exact_three_fault_deletes':sorted(ids)","'only_existing_clock_removed_in_read_only_nomination_scene':oldclock['uuid'],'no_copper_changes_emitted':True")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
