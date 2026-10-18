"""Draw the saved native-source geometry for diagnosis, not an accepted layout."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb,affinity
from shapely.geometry import box,Point
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'R10007-actual-source-reference-local-diagnostic-r231';assert not OUT.exists();OUT.mkdir()
mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl';g,h,b,q,full=pickle.loads(mp.read_bytes())
rp=H/'U10003-R10007-shared-return-logic-side-source-reference-rigid-pose-nomination-r220/receipt.json';r=json.loads(rp.read_bytes());withdraw=set(r['only_unadopted_wall_UUIDs_withdrawn_for_joint_nomination']);ids={p['uuid']for p in r['original_pads']};scene={**h,'pads':[p for p in h['pads']if p['uuid']not in ids],'tracks':[t for t in h['tracks']if t['uuid']not in withdraw]};records,trees=K.F.build({**scene,'zones':[]},layers={'F.Cu','B.Cu'})
window=box(198,126,222,150);SIG=K.L.norm(next(p['net']for p in r['original_pads']if p['num']=='1'));LG='/LOGIC_GND';FG='/motherboard_motors/FIELD_GND';parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1250" height="700" viewBox="0 0 1250 700"><rect width="1250" height="700" fill="white"/><text x="30" y="28" font-family="sans-serif" font-size="19">R10007 diagnostic: actual saved copper and J1 source reference; proposed pose, no board adoption</text>']
def path(s,xoff,color,opacity=1):
 for p in K.RF.parts(s):
  rings=[p.exterior,*p.interiors];d=' '.join('M '+' L '.join(f'{xoff+(x-198)*23:.5f},{70+(y-126)*23:.5f}'for x,y in ring.coords)+' Z'for ring in rings)
  parts.append(f'<path d="{d}" fill="{color}" fill-opacity="{opacity}" fill-rule="evenodd"/>')
for layer,inner,xoff in [('F.Cu','In1.Cu',35),('B.Cu','In4.Cu',660)]:
 ref=from_wkb((H/'R10007-HOST-existing-source-return-B-F-port-screen-r229'/('actual-J1-'+inner+'-source-reference.wkb')).read_bytes());path(ref.intersection(window),xoff,'#afddb0')
 for j in trees[layer].query(window,predicate='intersects'):
  row=records[layer][int(j)];net=K.L.norm(row['net']);path(row['shape'].intersection(window),xoff,'#ad32b3'if net==SIG else'#226dbc'if net==LG else'#d8a600'if net==FG else'#777777',.9)
 fp=r['original_footprint'];pose=next(p for p in r['nominees']if p['pose']==[180,-10.5,-3.5]);ang,dx,dy=pose['pose'];trans=lambda s:affinity.translate(affinity.rotate(s,ang,origin=(fp['x'],fp['y'])),dx,dy)
 if layer=='B.Cu':
  for p in r['original_pads']:path(trans(K.L.poly(p['layers']['B.Cu'])[0]),xoff,'#ad32b3'if p['num']=='1'else'#226dbc')
 for v in h['vias']:
  p=Point(v['x'],v['y'])
  if window.covers(p):path(p.buffer(v['drill']/2),xoff,'white')
 parts.append(f'<text x="{xoff}" y="58" font-family="sans-serif" font-size="17">{layer}: pale green = actual {inner} J1-source fill</text>')
 parts.append(f'<rect x="{xoff}" y="70" width="552" height="552" fill="none" stroke="black"/>')
 for x in range(198,223,4):parts.append(f'<text x="{xoff+(x-198)*23}" y="644" font-family="sans-serif" font-size="12">{x}</text>')
parts.append('<text x="35" y="682" font-family="sans-serif" font-size="14">Magenta: HOST signal; blue: LOGIC_GND; gold: FIELD_GND; gray: other native copper. Coordinates in mm, Y down.</text></svg>')
svg=OUT/'actual-source-reference.svg';svg.write_text(''.join(parts));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();(OUT/'receipt.json').write_text(json.dumps({'model_sha256':sha(mp),'pose_receipt_sha256':sha(rp),'svg_sha256':sha(svg),'proposed_pose_only':[180,-10.5,-3.5],'native_jobs':0,'adopted':False},indent=1)+'\n');print(svg.resolve(),flush=True)
