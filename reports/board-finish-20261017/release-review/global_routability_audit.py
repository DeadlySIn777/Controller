"""Read-only placement and routing setup audit; no router or native job."""
import os,sys
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,math,pickle,re
import psutil
psutil.Process().cpu_affinity([16,17])
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection,PolyCollection
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/board-finish-20261017';OLD=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in (OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(p))
import R157_native_selected_actual_conversion_r673 as N
sys.path.insert(0,str(ROOT/'reports/board-finish-20261011/parity-repair/root106/tools'))
import pcbtext
OUT=BASE/'release-review/global-routability-review';OUT.mkdir(exist_ok=False)
CACHE=BASE/'actual-full-audit-repaired-r1/r763';CURRENT=BASE/'combined-route-stage-r4';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
h=pickle.loads((CACHE/'actual-combined-full-after-model.pkl').read_bytes());g=pickle.loads((CACHE/'actual-combined-full-after-all-net-groups.pkl').read_bytes())
board=CURRENT/'native/board.kicad_pcb';assert sha(board)=='ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55'
cu=json.loads((CURRENT/'all-copper-expected.json').read_text())['copper'];pro=json.loads((CURRENT/'native/board.kicad_pro').read_text());dru=(CURRENT/'native/board.kicad_dru').read_text()
rules=json.loads((BASE/'routing/parent-audit-review/read-only-native-R299-rule-areas-r2/exact-native-rule-areas.json').read_text());seed=json.loads((BASE/'release-review/stage4-current-peer-group-seed-r1/seed.json').read_text())
norm=N.L.norm;pads={p['uuid']:p for p in h['pads']};fps={f['ref']:f for f in h['footprints']};domains=h['domains_normalized'];layers=N.K.LAYERS
counts=pcbtext.item_counts(board.read_bytes());tracks=[r for r in cu.values()if r['kind']=='segment'];vias=[r for r in cu.values()if r['kind']=='via']
lycount=Counter();lylength=Counter();widths=Counter()
trackpoints=defaultdict(list);trackweights=defaultdict(list)
for r in tracks:
 a=np.array(r['start_IU'])/1e6;b=np.array(r['end_IU'])/1e6;length=float(np.linalg.norm(b-a));ly=r['layer'];lycount[ly]+=1;lylength[ly]+=length;widths[r['width_IU']/1e6]+=1
 # <=1 mm samples distribute length across each 20 mm tile, avoiding midpoint bias.
 n=max(1,math.ceil(length));trackpoints[ly].extend(a+(b-a)*((i+.5)/n)for i in range(n));trackweights[ly].extend([length/n]*n)
print('CURRENT_COUNTS',counts,'TRACK_LENGTH_MM',dict(lylength),flush=True)
parent={}
def find(n):
 parent.setdefault(n,n)
 while parent[n]!=n:parent[n]=parent[parent[n]];n=parent[n]
 return n
for r in seed['seed_edges']:
 net=r['net'];a,b=r['old_group_edge'];parent[find((net,a))]=find((net,b))
families=Counter();netcounts=[];refcount=Counter();air=[];air_lengths=[];baseline=0;after=0;open_net_count=0
for net,gg in g.items():
 req={i:sorted({r['uuid']for r in gr if r['kind']=='pad'and r.get('pin')and r['uuid']in pads})for i,gr in enumerate(gg)};req={i:v for i,v in req.items()if v}
 if len(req)<2:continue
 baseline+=len(req)-1;components=defaultdict(set)
 for i,uids in req.items():components[find((net,i))].update(uids)
 if len(components)<2:continue
 open_net_count+=1;n=len(components)-1;after+=n;family=net.strip('/').split('/')[0];families[family]+=n;netcounts.append((n,net,len(components)))
 for uids in components.values():
  for ref in {pads[u]['ref']for u in uids}:refcount[ref]+=1
 # Pad-centre MST is a demand projection, not native ratsnest or routed length.
 groups=list(components.values());edges=[]
 for i,aa in enumerate(groups):
  a=np.array([[pads[u]['x'],pads[u]['y']]for u in aa]);au=list(aa)
  for j in range(i+1,len(groups)):
   bu=list(groups[j]);b=np.array([[pads[u]['x'],pads[u]['y']]for u in bu]);dist=((a[:,None,:]-b[None,:,:])**2).sum(2);ia,ib=np.unravel_index(dist.argmin(),dist.shape);edges.append((float(dist[ia,ib]),i,j,a[ia],b[ib],au[ia],bu[ib]))
 p=list(range(len(groups)))
 def f(i):
  while p[i]!=i:p[i]=p[p[i]];i=p[i]
  return i
 for d,i,j,a,b,ua,ub in sorted(edges,key=lambda e:e[0]):
  if f(i)==f(j):continue
  p[f(i)]=f(j);air.append([a,b]);air_lengths.append(math.sqrt(d))
print('OPEN_GROUP_METRIC',baseline,after,open_net_count,'families',families.most_common(15),flush=True)
courtyards=[];court_area=Counter();side=Counter();fpdomains={}
for f in fps.values():
 side[f['side']]+=1
 pd=[domains.get(norm(p['net']),'UNASSIGNED')for p in h['pads']if p['ref']==f['ref']and p['net']];fpdomains[f['ref']]=Counter(pd).most_common(1)[0][0]if pd else 'UNASSIGNED'
 for ly,polys in f['courtyard'].items():
  for s in N.L.poly(polys):courtyards.append(s);court_area[ly]+=s.area
actual_areas=[]
for r in rules:
 if not r['GetDoNotAllowTracks']:continue
 for p in r['outlines']:actual_areas.append((r,[(x/1e6,y/1e6)for x,y in p['outer_IU']]))
viaxy=np.array([[v/1e6 for v in r['at_IU']]for r in vias]);binsx=np.arange(0,461,20);binsy=np.arange(0,241,20)
viahist=np.histogram2d(viaxy[:,0],viaxy[:,1],bins=[binsx,binsy])[0]
def density_rows(points,weights=None):
 points=np.asarray(points)
 return np.histogram2d(points[:,0],points[:,1],bins=[binsx,binsy],weights=weights)[0]
def top_tiles(hist,n=6):
 order=np.argsort(hist.ravel())[::-1][:n]
 return [([int(binsx[i]),int(binsy[j]),int(binsx[i+1]),int(binsy[j+1])],round(float(hist[i,j]),1))for i,j in(np.unravel_index(k,hist.shape)for k in order)]
trackhist={ly:density_rows(trackpoints[ly],trackweights[ly])for ly in layers}
rootfloors={};floorstats={}
for net,ref,pin in [('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2')]:
 gr=next(gr for gr in g[net]if any(r['kind']=='pad'and r.get('ref')==ref and str(r.get('pin'))==pin for r in gr))
 for ly in ('In1.Cu','In4.Cu'):
  shapes=[r['shape']for r in gr if r['kind']=='fill'and r['layer']==ly];u=unary_union(shapes);rootfloors[net,ly]=u;floorstats[net+' '+ly]={'area_mm2':round(u.area,1),'components':len(u.geoms)if hasattr(u,'geoms')else 1}
print('REFERENCE_FLOORS',floorstats,flush=True)
fillarea=Counter();fillnets=defaultdict(Counter)
for z in h['zones']:
 for ly,ps in z['fills'].items():
  area=sum(p.area for p in N.L.poly(ps));fillarea[ly]+=area;fillnets[ly][norm(z['net'])]+=area
fig,axs=plt.subplots(2,3,figsize=(18,10.5),constrained_layout=True);fig.suptitle('450 × 235 mm motherboard — global routing review\nStage4 discrete Cu; R299 actual filled reference basis; projected opens are not a native AFTER result',fontsize=14)
for ax in axs.ravel():ax.set(xlim=(0,450),ylim=(235,0),aspect='equal',xlabel='x / mm',ylabel='y / mm');ax.set_facecolor('#fafafa');ax.grid(alpha=.12)
axs[0,0].add_collection(PolyCollection([np.asarray(s.exterior.coords)for s in courtyards],facecolor='#788c9c',edgecolor='none',alpha=.48))
axs[0,0].add_collection(PolyCollection([p for _,p in actual_areas],facecolor='none',edgecolor='#b82f31',linewidth=.5,alpha=.8))
for ref in ['U1001']+[r for r,_ in refcount.most_common(4)if r!='U1001']:
 f=fps[ref];axs[0,0].plot(f['x'],f['y'],'o',ms=3,color='#a31222');axs[0,0].annotate(ref,(f['x'],f['y']),xytext=(3,-8),textcoords='offset points',fontsize=8)
axs[0,0].set_title(f'Placement: {len(fps):,} footprints; red = native no-track areas')
axs[0,1].add_collection(LineCollection(air,colors='#bc3038',linewidths=.5,alpha=.24));axs[0,1].scatter([f['x']for f in fps.values()],[f['y']for f in fps.values()],s=.3,c='#82919d',alpha=.45)
axs[0,1].set_title(f'{after:,} remaining named-pad group links (conditional stage4 seed)')
im=axs[0,2].pcolormesh(binsx,binsy,viahist.T,cmap='magma',shading='auto');fig.colorbar(im,ax=axs[0,2],shrink=.65,label='via centres / 20 × 20 mm tile');axs[0,2].set_title('Through-via concentration')
for ax,ls,title in [(axs[1,0],('F.Cu','In2.Cu'),'F.Cu + In2.Cu'),(axs[1,1],('In3.Cu','B.Cu'),'In3.Cu + B.Cu')]:
 z=sum(trackhist[ly]for ly in ls);im=ax.pcolormesh(binsx,binsy,z.T,cmap='viridis',shading='auto');fig.colorbar(im,ax=ax,shrink=.65,label='routed track length / tile, mm');ax.set_title(title+' route concentration')
for ly,color in [('In1.Cu','#246bba'),('In4.Cu','#ee9a30')]:
 u=rootfloors['/LOGIC_GND',ly];ss=list(u.geoms)if hasattr(u,'geoms')else[u];axs[1,2].add_collection(PolyCollection([np.asarray(s.exterior.coords)for s in ss if s.geom_type=='Polygon'],facecolor=color,edgecolor='none',alpha=.35,label=ly))
axs[1,2].set_title('Source-rooted logic ground footprint\nIn1 blue / In4 orange; holes not rendered');axs[1,2].legend(loc='upper left',fontsize=8)
fig.savefig(OUT/'global-routability.png',dpi=150);plt.close(fig)
data={'board_SHA256':sha(board),'native_top_level_counts':counts,'footprint_sides':dict(side),'courtyard_area_sum_mm2':dict(court_area),'layer_track_count':dict(lycount),'layer_track_length_mm':dict(lylength),'track_width_histogram':dict(widths),'via_sizes':dict(Counter(str((max(r['diameters_IU'].values())/1e6,r['drill_IU']/1e6))for r in vias)),'named_pad_open_metric_baseline':baseline,'named_pad_open_metric_after_conditional_current_seed':after,'unresolved_nets':open_net_count,'open_families':families.most_common(),'largest_open_nets':sorted(netcounts,reverse=True)[:20],'open_net_incidence_by_footprint':refcount.most_common(15),'via_hot_tiles':top_tiles(viahist),'track_hot_tiles':{ly:top_tiles(hist)for ly,hist in trackhist.items()},'pad_projection_MST_span_mm':{'min':min(air_lengths),'median':float(np.median(air_lengths)),'p90':float(np.quantile(air_lengths,.9)),'max':max(air_lengths),'sum':sum(air_lengths)},'actual_native_rule_areas':len(rules),'actual_native_track_prohibitions':len({r['uuid']if 'uuid'in r else r['name']for r,_ in actual_areas}),'reference_floor_basis_R299':floorstats,'native_jobs':0,'PCB_modified':False}
data.update(native_pad_count=len(re.findall(rb'\n\t\t\(pad ',board.read_bytes())),actual_native_track_prohibitions=sum(r['GetDoNotAllowTracks']for r in rules),actual_native_via_prohibitions=sum(r['GetDoNotAllowVias']for r in rules),R299_actual_fill_sum_area_mm2=dict(fillarea),R299_actual_fill_sum_area_by_layer_top6_nets={ly:cc.most_common(6)for ly,cc in fillnets.items()})
(OUT/'measured-setup.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=1),flush=True)
