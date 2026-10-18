"""Coupled ordinary clock relocation and one precise logic-wall detour."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_exact_clock_fault_coupled_ground_r187.py';code=source.read_text()
code=code.replace('exact-clock-fault-coupled-ground-return-nomination-r187','clock-and-exact-logic-wall-rework-nomination-r203')
code=code.replace('U10003-preserved-branch-exact-two-port-reference-construction-r176/model.pkl','U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl').replace('c13b478b0cea7b09a510c221913d3a4d0774fcc74042605c17d69b35b37a9d20','dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5')
start=code.index(" g,h,b,z,full=pickle.loads(mp.read_bytes());old=");end=code.index(" reserved=C.BASE",start)
replacement="""
 g,h,b,z,full=pickle.loads(mp.read_bytes());old={t['uuid']:t for t in h['tracks']};ownvia='1f45e002-4f40-4087-bbed-3be260272d8f';logicid='eeb33c09-9494-4734-b174-e3c3ceffd73b';bid='894a2447-c6c2-4b9f-8c2e-f5d85bfec5be';native_ids={t['uuid']for t in g['tracks']}
 oldCLK=next(v for v in h['vias']if v['uuid']==ownvia);via={**oldCLK,'x':216.45,'y':142.49,'host_only_existing_clock_relocation':True};signal=next(v for v in h['vias']if v['uuid']=='ef759308-e664-5253-b016-ff17794eac74');spacing=Point(via['x'],via['y']).distance(Point(signal['x'],signal['y']));assert .90<=spacing<=1.0 and(via['d'],via['drill'])==(.5,.2)
 own_clock={t['uuid']for t in h['tracks']if t['uuid']not in native_ids and C.norm(t['net'])==CLK and t['layer']=='F.Cu'and t.get('prospective_not_native')};assert len(own_clock)==3
 deletes={logicid,bid,*own_clock};assert deletes<=old.keys();assert all(any(s==old[u]for s in g['tracks'])for u in(logicid,bid))
 faultids={logicid,bid};clkid=logicid;ownstub=next(iter(own_clock));roles={'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9','bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a'}
 hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in deletes],'vias':[v for v in h['vias']if v['uuid']!=ownvia]+[via]};z=[q for q in z if q['uuid']not in roles]
"""
code=code[:start]+replacement+code[end:]
code=code.replace('if net==FG:continue','if net==CLK:continue')
needle="endpoints=[(FG,'B.Cu',[pad['x'],pad['y']],[via['x'],via['y']]),(CLK,'F.Cu',old[clkid]['a'],old[clkid]['b'])]";assert code.count(needle)==1
code=code.replace(needle,"endpoints=[('/FPGA_OUTPUT_REQUEST','F.Cu',old[logicid]['a'],old[logicid]['b']),(CLK,'F.Cu',[214.799999,143.711969],[via['x'],via['y']]),(CLK,'B.Cu',[via['x'],via['y']],old[bid]['b'])]")
needle="free=win.difference(unary_union(cuts));faces=";assert code.count(needle)==1
code=code.replace(needle,"free=win.difference(unary_union(cuts));\n   if net=='/FPGA_OUTPUT_REQUEST':\n    import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K\n    if'logic_reference'not in locals():\n     _,gg=K.physical(full,'/LOGIC_GND',K.hole_context(full));rr=K.root(gg,'J11001','2');logic_reference=unary_union([r['shape']for r in rr if r['kind']=='fill'and r['layer']=='In1.Cu'])\n    free=free.intersection(logic_reference)\n   faces=")
code=code.replace("raw=pad['net']if net==FG else old[clkid]['net']","raw=old[logicid]['net']if net=='/FPGA_OUTPUT_REQUEST'else old[bid]['net']")
code=code.replace("if len({C.norm(t['net'])for t in added})==2 and not errors:","if len({t['layer']for t in added if C.norm(t['net'])==CLK})==2 and any(C.norm(t['net'])=='/FPGA_OUTPUT_REQUEST'for t in added)and not errors:")
code=code.replace('for net in(FLT,CLK):',"for net in('/FPGA_OUTPUT_REQUEST',CLK):")
needle="delta={'delete_original_tracks':";assert code.count(needle)==1
code=code.replace(needle,"delta={'exact_existing_clock_via_before':oldCLK,'exact_existing_clock_via_relocation':via,'logic_reference_mode':'literal actual J11001-rooted In1 full-body with no aperture credit','delete_original_tracks':")
code=code.replace('U10003-clock-fault-ground-r187/','U10003-clock-logic-rework-r203/')
code=code.replace("'native_jobs':0","'exact_retained_native_clock_mask_requires_post_native_fill':oldCLK['flashed'],'coupled_logic_clock_full_current_old_ground_reference_and_actual_source_gates':'OPEN','native_jobs':0")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
