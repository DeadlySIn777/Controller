exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/preflight.py').read().split('for s,e,w,n,lay')[0])
poses={'U11010':((272,179),0),'U11011':((272,186),0),'C11057':((270.2,177),90),'C11058':((275.25,178.5),0),'C11059':((270.2,184),90),'C11060':((275.25,185.5),0)}
for n,(p,a)in poses.items():fs[n].SetPosition(xy(p));fs[n].SetOrientationDegrees(a)
for n in refs:
 f=fs[n];print('FIT272',n,[other.GetReference()for other in b.GetFootprints()if other.GetReference()!=n and other.GetLayer()==f.GetLayer()and intersects(side_box(f),side_box(other),0)])
g=Geometry(b)
for s,e,w,n,lay in [((266.2,171),(266,177),4,'/motherboard_power_entry/MOTION_5V_RAW',pcbnew.F_Cu),((266,177),(272,179),1.6,'/motherboard_power_entry/MOTION_5V_RAW',pcbnew.B_Cu),((272,179),(272,186),1.6,'/motherboard_power_entry/MOTION_5V_RAW',pcbnew.B_Cu),((271.8,171),(271,173),2,'/LOGIC_GND',pcbnew.F_Cu),((271,173),(269.5,174.5),2,'/LOGIC_GND',pcbnew.F_Cu),((269.5,174.5),(269.5,189),2,'/LOGIC_GND',pcbnew.F_Cu),((276.025,180),(275,181),(0)or.5,'/LOGIC_GND',pcbnew.F_Cu),((275,181),(269.5,181),.5,'/LOGIC_GND',pcbnew.F_Cu)]:print('TEST272',s,e,w,b.GetLayerName(lay),g.clear([s,e],n,lay,w))
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/poses272.json').write_text(json.dumps(poses,indent=2))
