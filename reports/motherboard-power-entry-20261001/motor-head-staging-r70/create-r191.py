from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r189.py').read_text().replace('ROOT94-health-U20-cell-r189','ROOT94-health-U20-cell-r191')
a=s.index("for pn,anchor in [('4'");z=s.index('debug();pcbnew.ZONE_FILLER',a)
s=s[:a]+'''for pn,rv,sv in [('4',(336.5,177),(346.85,175.65)),('6',(336.5,178),(344.85,174.135))]:
 p=ps['U11020',pn];n=p.GetNetname();via(rv,n,'U11020_LED_POWER_'+pn+'_receiving_transfer');existing=[t for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and t.GetNetname()==n and math.dist(mm(t.GetPosition()),sv)<1e-6]
 if not existing:via(sv,n,'U11020_LED_POWER_'+pn+'_retained_source_transfer')
 route(mm(p.GetPosition()),rv,n,pcbnew.F_Cu,'U11020_LED_POWER_'+pn+'_receiving_F',.2);route(rv,sv,n,pcbnew.B_Cu,'U11020_LED_POWER_'+pn+'_actual_source_B',.2)
route(mm(ps['U11020','5'].GetPosition()),(345.3375,175),pg,pcbnew.F_Cu,'U11020_actual_CORE_source_reconnection',.3)
''' +s[z:]
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r191.py').write_text(s)
