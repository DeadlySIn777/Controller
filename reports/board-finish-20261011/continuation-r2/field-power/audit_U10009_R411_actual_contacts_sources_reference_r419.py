"""Independent U10009 materialized source/no-loss/reference/true Cu gate."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time,collections
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_aux_exact_raw as A
import fast_contacts as F
import complete_geometry_r2 as G
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
from inventory import sha
R=H/'U10009-R397-exact-R155-coupled-source-feed-construction-r411'
B=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155'
OG=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368'
O=H/'U10009-R411-independent-current-all-contact-source-reference-r419'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic()
 assert sha(R/'model.pkl')=='4bde59b8375ad9c512307f4894c1a5c2d6919f1cfb9f91c3669079e57a75e639';assert sha(B/'model.pkl')=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 g,h,b,q,c=pickle.loads((R/'model.pkl').read_bytes());bg,bh,bb,bq,before=pickle.loads((B/'model.pkl').read_bytes());d=pickle.loads((R/'only-new-discrete-and-exact-old-delete.pkl').read_bytes());nt=d['tracks'];nv=d['vias'];removed=set(d['removed']);oldtracks={t['uuid']:t for t in bh['tracks']};assert g==bg
 assert {t['uuid']:t for t in d['exact_original_tracks']}=={u:oldtracks[u]for u in removed};assert {t['uuid']:t for t in h['tracks']}==({u:t for u,t in oldtracks.items()if u not in removed}|{t['uuid']:t for t in nt});assert h['vias']==bh['vias']+nv
 for key in bh:
  if key not in('tracks','vias'):assert h[key]==bh[key]
 bm={z['uuid']:z for z in before['zones']};cm={z['uuid']:z for z in c['zones']};dirty={L.norm(r['net'])for r in nt+nv};newq=[z for z in q if z['uuid']not in{z['uuid']for z in bq}];assert len(newq)==1;filled=[]
 for uid,z in bm.items():
  n=cm[uid];assert {k:v for k,v in z.items()if k!='fills'}=={k:v for k,v in n.items()if k!='fills'}
  for layer,rs in z['fills'].items():
   if n['fills'][layer]==rs:continue
   old=unary_union(L.poly(rs));after=unary_union(L.poly(n['fills'][layer]));assert after.difference(old).is_empty;dirty.add(L.norm(z['net']));filled.append({'UUID':uid,'layer':layer,'literal_gain_empty':True,'removed_mm2':old.difference(after).area})
 put(O/'independent-local-filled-subset.json',filled)
 records,trees=F.build({**h,'zones':[]});tm={t['uuid']:t for t in h['tracks']};vm={v['uuid']:v for v in h['vias']};checks=[]
 fills={ly:[{'UUID':z['uuid'],'raw':z['net'],'local':z.get('clearance_mm',.15),'shape':s}for z in c['zones']for s in L.poly(z['fills'].get(ly,[]))]for ly in K.LAYERS};ft={ly:STRtree([r['shape']for r in rows])for ly,rows in fills.items()}
 def check(kind,new,foreign,layer,dist,req):checks.append({'kind':kind,'new_UUID':new,'foreign_UUID':foreign,'layer':layer,'actual_mm':dist,'required_mm':req,'PASS':dist+1e-10>=req})
 for item in nt+nv:
  via='d'in item;axis=Point(item['x'],item['y'])if via else LineString([item['a'],item['b']]);radius=item['d']/2 if via else item['w']/2
  for layer in K.LAYERS if via else[item['layer']]:
   for j in trees[layer].query(axis.buffer(radius+.801),predicate='intersects'):
    a=records[layer][int(j)]
    if L.norm(a['net'])==L.norm(item['net']):continue
    gap=axis.distance(a['shape'])-radius
    if a['kind']=='track'and not tm[a['uuid']].get('m'):t=tm[a['uuid']];gap=axis.distance(LineString([t['a'],t['b']]))-radius-t['w']/2
    elif a['kind']=='via':v=vm[a['uuid']];gap=axis.distance(Point(v['x'],v['y']))-radius-v['d']/2
    check('true_cap_to_actual_'+a['kind'],item['uuid'],a['uuid'],layer,gap,G.gap(h,item['net'],a['net'])+.025)
   for j in ft[layer].query(axis.buffer(radius+.801),predicate='intersects'):
    a=fills[layer][int(j)]
    if L.norm(a['raw'])==L.norm(item['net']):continue
    check('true_cap_to_actual_fill',item['uuid'],a['UUID'],layer,axis.distance(a['shape'])-radius,max(a['local'],G.gap(h,item['net'],a['raw']))+.025)
  if via:
   for pad in h['pads']:
    if pad['smd']:
     for ly,rs in pad['layers'].items():
      if ly not in('F.Cu','B.Cu'):continue
      for s in L.poly(rs):
       gap=axis.distance(s)-item['drill']/2
       if gap<.30:check('every_SMD_even_same_raw',item['uuid'],pad['uuid'],ly,gap,.275)
    for s in L.poly(pad.get('hole')or[]):
     gap=axis.distance(s)-item['drill']/2
     if gap<.30:check('every_native_pad_hole',item['uuid'],pad['uuid'],'ALL',gap,.275)
   for v in h['vias']:
    if v['uuid']==item['uuid']:continue
    gap=axis.distance(Point(v['x'],v['y']))-(v['drill']+item['drill'])/2
    if gap<.30:check('dynamic_every_native_new_hole',item['uuid'],v['uuid'],'ALL',gap,.275)
 plane=newq[0];ps=set_precision(plane['shape'],0);layer=plane['layer']
 for j in trees[layer].query(ps.buffer(.801),predicate='intersects'):
  a=records[layer][int(j)]
  if L.norm(a['net'])==L.norm(plane['net']):continue
  gap=ps.distance(a['shape'])
  if a['kind']=='track'and not tm[a['uuid']].get('m'):t=tm[a['uuid']];gap=ps.distance(LineString([t['a'],t['b']]))-t['w']/2
  elif a['kind']=='via':v=vm[a['uuid']];gap=ps.distance(Point(v['x'],v['y']))-v['d']/2
  check('new_plane_to_true_'+a['kind'],plane['uuid'],a['uuid'],layer,gap,max(plane['clearance_mm'],G.gap(h,plane['net'],a['net']))+.025)
 for j in ft[layer].query(ps.buffer(.801),predicate='intersects'):
  a=fills[layer][int(j)]
  if L.norm(a['raw'])==L.norm(plane['net']):continue
  check('new_plane_to_actual_native_owned_fill',plane['uuid'],a['UUID'],layer,ps.distance(a['shape']),max(plane['clearance_mm'],a['local'],G.gap(h,plane['net'],a['raw']))+.025)
 errors=[r for r in checks if not r['PASS']];put(O/'all-new-true-Cu-and-aperture-checks.json',checks);put(O/'all-new-true-Cu-and-aperture-errors.json',errors);print('R419 new true guards',len(checks),'errors',len(errors),flush=True)
 assert sha(OG/'actual-drilled-current-groups.pkl')=='ee233fd9010cf3c29d0c4b47503fd93bf754dddf9dd297f9f7c58117c7589742';oldgroups=pickle.loads((OG/'actual-drilled-current-groups.pkl').read_bytes());_,rh,_,_,ractual=pickle.loads((H/'REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364/model.pkl').read_bytes());assert rh==bh and ractual==before
 groups={};contacts=[];hole=Point(nv[0]['x'],nv[0]['y']).buffer(nv[0]['drill']/2,quad_segs=128);ctx=K.hole_context(c)
 for net,a in oldgroups.items():
  affected=net in dirty or any(hole.intersects(r['shape'])for xs in a for r in xs)
  if affected:_,n=K.physical(c,net,ctx)
  else:
   for kind in('tracks','vias','pads','shapes','zones'):assert [r for r in before[kind]if L.norm(r['net'])==net]==[r for r in c[kind]if L.norm(r['net'])==net]
   n=a
  groups[net]=n;_,bad=K.contact_losses(a,n,removed);contacts.append({'net':net,'fresh_physical_rebuild':affected,'old_relationship_losses':bad});put(O/'all-contact-checkpoint.json',contacts);print('R419 contact',net,len(bad),'REBUILD'if affected else'EXACT_REUSE',flush=True)
 sources=[];refs=[]
 for net,ref,pin in K.ROOTS:
  a=K.root(oldgroups[net],ref,pin);n=K.root(groups[net],ref,pin);lost=K.keys(a)-{('track',u,ly)for u in removed for ly in K.LAYERS}-K.keys(n);sources.append({'net':net,'source':ref+'.'+pin,'prior_keys_lost':[list(k)for k in sorted(lost)]})
  if ref in('J11001','J11003','J11005'):
   bad,proof=RF.audit(before,K.source_refs(a),K.source_refs(n),net,removed);refs.append({'net':net,'new_strict_zero_reference_losses':bad,'proof':proof})
 fg=K.root(groups['/motherboard_motors/FIELD_GND'],'J11003','2');fr=K.source_refs(fg);newrefs=[]
 for t in nt:
  body=A.shape({'kind':'segment',**t});gap=body.difference(fr[t['layer']]);gf=O/(t['uuid']+'-actual-new-body-source-ground-reference-gap.wkb');gf.write_bytes(gap.wkb);newrefs.append({'UUID':t['uuid'],'raw':t['net'],'layer':t['layer'],'gap_mm2':gap.area,'gap_empty':gap.is_empty,'gap_file':str(gf.resolve()),'gap_sha256':sha(gf)})
 put(O/'all-nine-prior-source-rows.json',sources);put(O/'three-bank-strict-zero-new-reference-rows.json',refs);put(O/'all-four-new-full-body-source-reference-rows.json',newrefs);(O/'actual-current-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5))
 bad=errors or any(x['old_relationship_losses']for x in contacts)or any(x['prior_keys_lost']for x in sources)or any(x['new_strict_zero_reference_losses']for x in refs)or any(not x['gap_empty']for x in newrefs)
 rec={'verdict':'U10009_INCREMENTAL_CURRENT_ALL_CONTACT_SOURCE_REFERENCE_TRUE_CU_PASS_FULL_CURRENT_NATIVE_OPEN'if not bad else'U10009_INCREMENTAL_CURRENT_CONTACT_SOURCE_REFERENCE_TRUE_CU_REPAIR_REQUIRED','R411_model_sha256':sha(R/'model.pkl'),'R155_parent_sha256':sha(B/'model.pkl'),'new_true_guard_errors':errors,'contact_loss_count':sum(len(x['old_relationship_losses'])for x in contacts),'nine_source_loss_count':sum(len(x['prior_keys_lost'])for x in sources),'strict_new_reference_loss_count':sum(len(x['new_strict_zero_reference_losses'])for x in refs),'new_full_body_reference_rows':newrefs,'prior_R368_28strictrefs_CORE93_ROOT42_planner_current_native_FAIL_OPEN':'PRESERVED_SEPARATE','all109_old_lower_VS_physical_contacts_and_eight_VS_source':'included_in_exact_partition_and_source_comparator','full_signed_VS_simplex_current_package_barrel_sheet_drop_thermal_transient_native':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'verdict':rec['verdict'],'contacts':rec['contact_loss_count'],'sources':rec['nine_source_loss_count'],'refs':rec['strict_new_reference_loss_count'],'true_errors':len(errors)}),flush=True)
if __name__=='__main__':main()
