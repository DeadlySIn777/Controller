from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-cell-r195.py').read_text().replace('ROOT94-health-U26-cell-r195','ROOT94-health-U26-cell-r197')
a=s.index("for pn in['1','3']:\n p=ps['U11026'");z=s.index("for pn,rv,sv in [('4'",a)
s=s[:a]+'''p=ps['U11026','1'];route(mm(p.GetPosition()),mm(ps[control_source['1']].GetPosition()),p.GetNetname(),pcbnew.F_Cu,'U11026_actual_input_1',.2)
p=ps['U11026','3'];cn=p.GetNetname();rv=(331.9125,188.85);sv=(333,191.8);sg=(333,192.65)
via(rv,cn,'U11026_input_3_receiving_transfer');via(sv,cn,'U11026_input_3_actual_SOURCE_transfer');via(sg,gn,'U11026_input_3_actual_SOURCE_return_stitch');route(mm(ps['C11080','2'].GetPosition()),sg,gn,pcbnew.B_Cu,'U11026_input_3_SOURCE_return_to_C11080',.25);route(mm(p.GetPosition()),rv,cn,pcbnew.F_Cu,'U11026_input_3_receiving_F',.2);route(mm(ps[control_source['3']].GetPosition()),sv,cn,pcbnew.F_Cu,'U11026_input_3_SOURCE_F',.2);route(rv,sv,cn,pcbnew.B_Cu,'U11026_input_3_actual_source_B',.2)
''' +s[z:]
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-cell-r197.py').write_text(s)
