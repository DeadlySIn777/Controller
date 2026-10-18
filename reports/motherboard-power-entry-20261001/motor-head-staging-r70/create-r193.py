from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r191.py').read_text().replace('ROOT94-health-U20-cell-r191','ROOT94-health-U20-cell-r193')
s=s.replace("ret-={'8b76be20", "for pn in['4','6']:\n n=original_ps['U11020',pn].GetNetname();ret|={t.m_Uuid.AsString()for t in original.GetTracks()if t.GetNetname()==n}\nret-={'8b76be20")
a=s.index("for pn,rv,sv in [('4'");z=s.index('route(mm(ps[\'U11020\',\'5\']',a)
s=s[:a]+'''for pn,rv,other,sv in [('4',(336.5,177),('U11024','2'),(347.6,173.635)),('6',(336.5,178),('U11022','2'),(271.6,234.635))]:
 p=ps['U11020',pn];n=p.GetNetname();via(rv,n,'U11020_LED_POWER_'+pn+'_receiving_transfer');via(sv,n,'U11020_LED_POWER_'+pn+'_actual_contact_transfer');route(mm(ps[other].GetPosition()),sv,n,pcbnew.F_Cu,'U11020_LED_POWER_'+pn+'_actual_contact_F',.2);route(mm(p.GetPosition()),rv,n,pcbnew.F_Cu,'U11020_LED_POWER_'+pn+'_receiving_F',.2);route(rv,sv,n,pcbnew.B_Cu,'U11020_LED_POWER_'+pn+'_actual_contact_B',.2)
''' +s[z:]
s=s.replace('padding=15,max_nodes=180000','padding=15,max_nodes=500000')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r193.py').write_text(s)
