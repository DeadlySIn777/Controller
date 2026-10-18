from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-IN1-blockers-r183.py').read_text();s=s[:s.index("for r,p in g.barriers:")] if 'for r,p in g.barriers:'in s else s
s=s.replace('ROOT94-health-U20-cell-r181/debug','ROOT94-health-U20-cell-r196/literal-retired-input').replace("pt=(343.8625,174.35);n='/motherboard_power_entry/CORE_HEALTH_A_N'","pt=(346.85,173.635);n='/motherboard_power_entry/CORE_HEALTH_B_LED_K'")
s=s.replace("print('sourceclear',g.clear([(338.1625,174.35)]*2,n,pcbnew.F_Cu,.2),'endclear',g.clear([pt]*2,n,pcbnew.F_Cu,.2))", "print('SOURCE_POINT_CLEAR_F',g.clear([pt]*2,n,pcbnew.F_Cu,.2),'B',g.clear([pt]*2,n,pcbnew.B_Cu,.2))")
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U24-pin2-blockers-r199.py').write_text(s)
