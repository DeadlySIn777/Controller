"""Exact retained via alternatives around the blocked lower network."""
import json
import math
import plan_repair as P
from shapely.geometry import Point,LineString

def main():
 rows,_=P.I.own_additions();g,_,_=P.R.overlay_and_targets();r,e=P.exemptions();model=P.S.Model(g,r,e)
 n=P.NETWORKS[1];a,b=n['anchors'];window=LineString([a,b]).envelope.buffer(12,cap_style=3).envelope
 via_index={v['uuid']:v for v in g['vias']};local=[]
 for v in g['vias']:
  if P.S.norm(v['net'])!=P.NET or not window.covers(Point(v['x'],v['y'])):continue
  local.append({**v,'anchor_distances_mm':[math.dist(p,(v['x'],v['y'])) for p in(a,b)]})
 out={'network':n,'window':list(window.bounds),'retained_same_net_vias':local,
      'layers':g['copper_layers'],'native_jobs':0,'board_emitted':False}
 destination=P.HERE/'layer-anchors.json'
 if destination.exists():raise ValueError('distinct receipt required')
 destination.write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8')
 print(json.dumps(out,indent=1),flush=True)

if __name__=='__main__':main()
