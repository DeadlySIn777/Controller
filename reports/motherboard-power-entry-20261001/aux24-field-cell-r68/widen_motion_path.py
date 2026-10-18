exec(__import__('pathlib').Path('reports/motherboard-power-entry-20261001/aux24-field-cell-r68/find_switch_approach.py').read_text().split('for l in')[0])
import json,math
p=[(266,177),(273,184),(273,222),(274,223),(274,224),(275,224),(276,225),(279,225),(282,228),(300,228),(310,238),(314,238),(319,233),(319,227),(320,226),(320,217),(330,207),(336,207),(338,205),(338,201),(339,200),(339,195),(340,194)]
r=[]
for s,e in zip(p,p[1:]):
 count=math.ceil(math.dist(s,e)/2)
 for i in range(count):
  ss=tuple(s[k]+(e[k]-s[k])*i/count for k in[0,1]);ee=tuple(s[k]+(e[k]-s[k])*(i+1)/count for k in[0,1]);w=next((w for w in[16,14,12,10,8,6,4]if g.clear([ss,ee],n,pcbnew.F_Cu,w)),None);assert w;r.append(dict(points_mm=[ss,ee],width_mm=w,length_mm=math.dist(ss,ee)))
rho=1.724e-8*(1+.00393*65);R=sum(rho*(v['length_mm']/1000)/((v['width_mm']/1000)*(63e-6))for v in r)
out=dict(routes=r,length_mm=sum(v['length_mm']for v in r),resistance_screen_ohm=R,IR_motor_total_v=R*1.3464,strict_monitor_remaining_before_switch_return_v=.0203623887-R*1.3464)
Path(__file__).with_name('widen-motion-path.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
