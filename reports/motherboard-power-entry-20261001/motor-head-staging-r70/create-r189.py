from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r186.py').read_text().replace('ROOT94-health-U20-cell-r186','ROOT94-health-U20-cell-r189')
s=s.replace("t=parse(without_generated_fills(B.read_text()))", "ret-={'8b76be20-4f22-4741-b6f6-b7150c195020','cdb2b347-fd52-4b51-8258-07f2f94d7ba7','881c2e60-ce80-40f5-ba25-23299c7aa94e','3dd7e290-39bc-4c38-9bdb-7cd9ff4a697a'}\nt=parse(without_generated_fills(B.read_text()))")
a=s.index('# Reattach the exact');z=s.index('debug();pcbnew.ZONE_FILLER',a)
s=s[:a]+'''# Reattach two logic inputs through their actual retained source transfers.
for pn,rv,sv,sg in [('1',(340.6875,175.85),(343.847560,176.360060),(343.0,176.3)),('3',(340.5875,174.15),(344.1375,178.65),(344.1375,179.5))]:
 p=ps['U11020',pn];cn=p.GetNetname();via(rv,cn,'U11020_input_'+pn+'_actual_receiving_transfer');via(sg,gn,'U11020_input_'+pn+'_actual_SOURCE_Ground_stitch');route(mm(p.GetPosition()),rv,cn,pcbnew.F_Cu,'U11020_input_'+pn+'_actual_receiving_F',.2);route(rv,sv,cn,pcbnew.B_Cu,'U11020_input_'+pn+'_actual_source_B',.2)
# Preserve the actual Source Ground at the output-side source transfer.
route((344.1375,179.5),mm(ps['C11078','2'].GetPosition()),gn,pcbnew.B_Cu,'U11020_input_3_SOURCE_Ground_to_actual_C11078',.25)
for pn,anchor in [('4',(346.85,175.65)),('6',(344.85,174.135)),('5',(345.3375,175))]:
 p=ps['U11020',pn];route(mm(p.GetPosition()),anchor,p.GetNetname(),pcbnew.F_Cu,'U11020_reconnect_actual_pin_'+pn,.3 if pn=='5'else.2)
''' +s[z:]
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r189.py').write_text(s)
