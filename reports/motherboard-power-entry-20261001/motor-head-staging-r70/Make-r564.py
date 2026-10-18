from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r562.py');t=p.read_text();t=t.replace('r562','r564')
a=t.index('for t in b0.GetTracks():');z=t.index('tree=parse(',a)
t=t[:a]+'''added27={q['uuid']for q in json.loads(Path('reports/motherboard-power-entry-20261001/Source27-B-controls-off-CORE-F-r524/actual-Cu.json').read_text())['new_Cu']}
for t in b0.GetTracks():
 if t.m_Uuid.AsString()in added27 and t.GetNetname()in ['/LOGIC_GND','/motherboard_power_entry/MOTION_5V_RAW']:ret.add(t.m_Uuid.AsString())
assert all(u not in rootCu for u in ret)
'''+t[z:]
a=t.index('seen=set()');z=t.index("dest=O/",a)
t=t[:a]+'''for cap,owner,power,ground,raw in [('C11089','U11035','6','2','C11083'),('C11090','U11036','5','3','C11083'),('C11091','U11037','6','2','C11086'),('C11092','U11038','5','3','C11086')]:
 route(mm(ps[cap,'1'].GetPosition()),mm(ps[owner,power].GetPosition()),ps[cap,'1'].GetNetname(),'Short exact owning-VDD local bypass '+cap)
 route(mm(ps[cap,'2'].GetPosition()),mm(ps[owner,ground].GetPosition()),ps[cap,'2'].GetNetname(),'Actual exact owning-GND local bypass '+cap)
 route(mm(ps[cap,'1'].GetPosition()),mm(ps[raw,'1'].GetPosition()),ps[cap,'1'].GetNetname(),'Actual same-rail existing Source feed '+cap)
 route(mm(ps[cap,'2'].GetPosition()),mm(ps[raw,'2'].GetPosition()),ps[cap,'2'].GetNetname(),'Actual same-domain existing Source return '+cap)
for por in ['U11035','U11037']:
 for pin in ['3','5']:route(mm(ps[por,pin].GetPosition()),mm(ps[por,'6'].GetPosition()),ps[por,pin].GetNetname(),'Actual POR MR/SENSE source tie '+por+'.'+pin)
for pd,cap in [('R11082','C11090'),('R11083','C11092')]:route(mm(ps[pd,'2'].GetPosition()),mm(ps[cap,'2'].GetPosition()),ps[pd,'2'].GetNetname(),'Actual default Source return '+pd)
'''+t[z:]
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r564.py').write_text(t)
