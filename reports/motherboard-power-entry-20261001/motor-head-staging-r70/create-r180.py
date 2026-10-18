from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r177.py').read_text()
s=s.replace('ROOT94-health-U20-cell-r177','ROOT94-health-U26-local-r180')
a=s.index("frozen=json.loads(");z=s.index("ps={(f.GetReference()",a)
s=s[:a]+'''ret={'69baa506-08f7-4684-a96f-ed1dcb1d5f07','36d15a6c-aa47-4f2f-9d51-39164aab84dc','20f63433-0362-4a66-8e04-b7574e462983','a92cddfc-8a59-44ae-a44b-ddd07bcd2f43','fff55e02-ad70-401f-9f89-6d2f6263b67f'}
# Resolve partial UUIDs against actual immutable source; only literal reviewed LED leaves.
for prefix in['20f63433','a92cddfc','fff55e02']:
 ret={u for u in ret if not u.startswith(prefix)}|{u for u in old if u.startswith(prefix)}
assert len(ret)==5 and ret<=set(old)
t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-retired-input.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));fs={f.GetReference():f for f in b.GetFootprints()};oldposes={}
''' +s[z:]
a=s.index("pg=ps['U11020'");z=s.index('debug();pcbnew.ZONE_FILLER',a)
s=s[:a]+'''pg=ps['U11026','5'].GetNetname();gn=ps['U11026','2'].GetNetname();pv=(329.4,191);gv=(329.25,191.8)
via(pv,pg,'U11026_local_positive_transfer');via(gv,gn,'U11026_local_Source_return_stitch')
route(mm(ps['U11026','5'].GetPosition()),pv,pg,pcbnew.F_Cu,'U11026_own_positive_F');route(mm(ps['C11081','1'].GetPosition()),pv,pg,pcbnew.B_Cu,'U11026_own_positive_B');route(mm(ps['C11081','2'].GetPosition()),gv,gn,pcbnew.B_Cu,'U11026_own_bypass_return_stitch')
led=ps['U11026','6'].GetNetname();route((327.9,192.865),(329.0875,190.35),led,pcbnew.B_Cu,'FIELD_LED_A_exact_low_current_power_leaf_reroute',.2)
''' +s[z:]
s=s.replace("[('U11020','5','C11079','1'),('U11020','2','C11079','2'),('U11020','5','C11029','1'),('U11020','2','C11088','2')]","[('U11026','5','C11081','1'),('U11026','2','C11081','2'),('U11026','5','C11055','1'),('U11026','2','C11055','2')]")
s=s.replace('motor-health-U20-cell-candidate','motor-health-U26-local-candidate')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-local-r180.py').write_text(s)
