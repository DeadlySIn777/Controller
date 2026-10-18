"""Broaden the finite detour search with the same physical obstacles and record rejection causes."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'repair_DI7_power_feature_r24.py').read_text().replace('import sys,json,math,copy,uuid,shutil,subprocess','import sys,json,math,copy,uuid,shutil,subprocess,heapq,collections')
s=s.replace('actual-source26-root87-DI7-detour-r24','actual-source26-root87-DI7-detour-r25')
s=s.replace('def clear(points):','reasons=collections.Counter()\ndef reject(reason):reasons[reason]+=1;return False\ndef clear(points):')
s=s.replace("pcbnew.FromMM(.30)):return False", "pcbnew.FromMM(.30)):return reject('foreign pad')")
s=s.replace(".1+w/2+.20-1e-6:return False", ".1+w/2+.20-1e-6:return reject('foreign track')")
s=s.replace("if proposed.OutlineCount():return False", "if proposed.OutlineCount():return reject('old thin IO3')")
s=s.replace("if hit.OutlineCount():return False", "if hit.OutlineCount():return reject('keepout')")
s=s.replace("except ValueError:return False", "except ValueError as exc:return reject('actual reference: '+str(exc))")
marker="e.write(out/'search.json',dict("
before,after=s.split(marker,1)
grid='''
if chosen is None:
 step=1.;limit=100.;queue=[(math.dist(start,end),0.,(0,0))];cost={(0,0):0.};prior={};memo={}
 point=lambda k:(round(start[0]+step*k[0],6),round(start[1]+step*k[1],6))
 while queue and len(cost)<7000:
  _,d,k=heapq.heappop(queue)
  if d>cost[k]+1e-8:continue
  at=point(k)
  if math.dist(at,end)<1.5 and clear([at,end]):
   found=[end,at]
   while k!=(0,0):k=prior[k];found.append(point(k))
   found.reverse();simple=[]
   for v in found:
    if simple and math.dist(simple[-1],v)<1e-7:continue
    while len(simple)>1:
     a,z=simple[-2:]
     if abs((z[0]-a[0])*(v[1]-z[1])-(z[1]-a[1])*(v[0]-z[0]))>1e-8:break
     simple.pop()
    simple.append(v)
   if clear(simple):chosen=simple
   break
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   nxt=(k[0]+dx,k[1]+dy);pt=point(nxt);nd=d+math.hypot(dx,dy)
   if nd+math.dist(pt,end)>limit or nd>=cost.get(nxt,float('inf'))-1e-8:continue
   if not(100<=pt[0]<=145 and 158<=pt[1]<=216):continue
   key=tuple(sorted((k,nxt)))
   if key not in memo:memo[key]=clear([at,pt])
   if not memo[key]:continue
   cost[nxt]=nd;prior[nxt]=k;heapq.heappush(queue,(nd+math.dist(pt,end),nd,nxt))
e.write(out/'search-rejection-causes.json',dict(reasons))
'''
s=before+grid+marker+after
# Emit every actual polyline segment; the original proposed trace becomes
# the first segment and exact fresh UUIDs identify the later sections.
old="newid=str(uuid.uuid4());second=copy.deepcopy(node)\ndef point(node,which,p):e.child(node,which)[1:]=[format(v,'.6f')for v in p]\npoint(node,'end',chosen[1]);point(second,'start',chosen[1]);e.child(second,'uuid')[1]=e.q(newid);tree.append(second)"
new="""template=copy.deepcopy(node);newids=[]
def point(node,which,p):e.child(node,which)[1:]=[format(v,'.6f')for v in p]
point(node,'start',chosen[0]);point(node,'end',chosen[1])
for p,q in zip(chosen[1:],chosen[2:]):
 second=copy.deepcopy(template);point(second,'start',p);point(second,'end',q)
 newid=str(uuid.uuid4());newids.append(newid);e.child(second,'uuid')[1]=e.q(newid);tree.append(second)"""
assert old in s;s=s.replace(old,new)
s=s.replace("g['signal_UUIDs'].append(newid);g['new_copper_UUIDs'].append(newid);plan['new_copper_UUIDs'].append(newid)", "g['signal_UUIDs'].extend(newids);g['new_copper_UUIDs'].extend(newids);plan['new_copper_UUIDs'].extend(newids)")
s=s.replace('added_UUID=newid','added_UUIDs=newids').replace('new_copper=8','new_copper=len(plan[\'new_copper_UUIDs\'])')
out=p/'repair_DI7_power_feature_r25.py';assert not out.exists();out.write_text(s)
