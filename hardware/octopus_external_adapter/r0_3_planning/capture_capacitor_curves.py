"""Capture manufacturer's typical reference data, not guaranteed capacitance minima."""
from pathlib import Path
from urllib.request import urlopen,Request
import json,bisect
R=Path(__file__).resolve().parent
parts={'CL31B475KBHNNNE':(4.7,[3.3,4.75,5.2,12,24,26.4,45.4]),'CL31A226KAHNNNE':(22,[3.3,5.2]),'CL21B225KAFNNNE':(2.2,[3.3])}
result=[]
for mpn,(nom,targets) in parts.items():
    url='https://product.samsungsem.com/mlcc/'+mpn[:-1]+'.do'
    html=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode()
    pos=html.index('"graphType" : "DCBias"')
    pos=html.index('"data" :',pos)+len('"data" :')
    data=json.JSONDecoder().raw_decode(html[pos:].lstrip())[0]
    if isinstance(data,dict): raise RuntimeError('Unexpected curve structure')
    points=sorted((float(d['x']),float(d['y'])) for d in data)
    screens=[]
    xs=[p[0] for p in points]
    for v in targets:
        i=bisect.bisect_left(xs,v)
        if i==0 or i==len(points): raise RuntimeError('Target outside source curve')
        a,b=points[i-1],points[i]
        y=a[1]+(v-a[0])/(b[0]-a[0])*(b[1]-a[1])
        typ=nom*(1+y/100)
        screens.append(dict(voltage_v=v,interpolated_typical_change_percent=y,typical_capacitance_uf=typ,screen_uf_after_10pct_tolerance_and_15pct_temperature=typ*.9*.85,source_bracket_points=[a,b]))
    result.append(dict(mpn=mpn,source_url=url,nominal_uf=nom,curve_kind='Manufacturer typical DCBias reference graph',points=points,screens=screens))
out=dict(date='2026-10-06',not_guaranteed_minima=True,note='Manufacturer graph values are typical reference characteristics. Multiplication by nominal tolerance and dielectric temperature limits is an engineering screen, not a supplier guarantee of combined worst-case performance.',parts=result)
(R/'capacitor-bias-source-data.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps([{k:v for k,v in x.items() if k!='points'} for x in result],indent=2))
