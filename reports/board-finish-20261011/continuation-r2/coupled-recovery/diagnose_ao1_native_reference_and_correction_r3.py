"""Narrow independent actual COM topology and tiny gap correction screen.

Full prior R2 input authority remains frozen. No native invocation or board write.
Actual all-board barrel holes are subtracted, including newer remote barrels.
"""
import sys,json,hashlib,math,collections,time,copy
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_ao1_reference_coupled_mon_r4 as R
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
A,P,G,S,C,F,N=R.A,R.P,R.G,R.S,R.C,R.F,R.N
Q=R.Q;COM=Q.COM
def main():
 start=time.monotonic();out=HERE/'ao1-native-reference-gap-diagnostic-r3.json';assert not out.exists();cache=HERE/'ao1-native-rooted-reference-r3';cache.mkdir()
 prior=json.loads(A.read(HERE/'ao1-native-com-reference-independent-r2.json'));assert C.sha(A.read(HERE/'ao1-native-com-reference-independent-r2.json'))=='faf362b74dd62ad4301ab6040fff4e2585c6093cf348246d92207eba07595bb1'
 for p,pin in prior['read_files_sha256'].items():assert C.sha(Path(p).read_bytes())==pin,p
 ng=json.loads(A.read(HERE.parent/'ao1-native-diagnostic-r1/scoped-native-fill/geometry.json'));og=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));nf=json.loads(A.read(HERE.parent/'ao1-native-diagnostic-r1/scoped-native-fill/actual-via-flashes.json'))['vias'];of=json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias']
 def model(geom,flashes):
  pads=copy.deepcopy(template['pads']);native={(p['ref'],p['num']):p for p in geom['pads'] if S.norm(p['net'])==COM};counter=collections.Counter();pd={};rs={l:[] for l in geom['copper_layers']}
  for p in pads:
   name=p['ref']+'.'+str(p['num']);idx=counter[name];counter[name]+=1;pid=name+'#'+str(idx);pd[pid]=p
   if S.norm(p['net'])!=COM:continue
   n=native[p['ref'],p['num']];assert math.dist((p['x'],p['y']),n['at'])<.00008 and p['net']==n['net'] and set(p['layers'])==set(n['layers']);p['x'],p['y']=n['at'];p['layers'][n['layers'][0]]=A.polys(n['poly'])
   for l,polys in p['layers'].items():
    for sh in S.poly(polys):rs[l].append({'kind':'pad','net':COM,'uuid':p['uuid'],'pad_id':pid,'key':('p',pid),'shape':sh,'layer':l})
  vias=[{'uuid':v['uuid'],'net':v['net'],'x':v['at'][0],'y':v['at'][1],'d':v['w'],'drill':v['drill']} for v in geom['vias']]
  for v in vias:
   if S.norm(v['net'])!=COM:continue
   sh=Point(v['x'],v['y']).buffer(v['d']/2,resolution=128)
   for l in flashes[v['uuid']]:rs[l].append({'kind':'via','net':COM,'uuid':v['uuid'],'key':('v',v['uuid']),'shape':sh,'layer':l})
  for t in geom['tracks']:
   if S.norm(t['net'])!=COM:continue
   assert not t.get('m');sh=LineString([t['s'],t['e']]).buffer(t['w']/2,resolution=128);rs[t['layer']].append({'kind':'track','net':COM,'uuid':t['uuid'],'key':('t',t['uuid']),'shape':sh,'layer':t['layer']})
  for z in geom['zones']:
   if S.norm(z['net'])!=COM:continue
   for l,polys in z['fills'].items():
    for i,sh in enumerate(S.poly(A.polys(polys))):rs[l].append({'kind':'fill','net':COM,'uuid':z['uuid'],'key':('z',z['uuid'],l,i),'shape':sh,'layer':l})
  return SimpleNamespace(g={'pads':pads,'vias':vias,'copper_layers':geom['copper_layers']},pads=pd,records=rs)
 actual=model(ng,nf);original=model(og,of);refs,wit,_,_=Q.rooted_reference(actual,{u:set(v) for u,v in nf.items()},next(p['net'] for p in template['pads'] if p['ref']=='U14619' and p['num']=='7'));oldrefs,_,_,_=Q.rooted_reference(original,{u:set(v) for u,v in of.items()},next(p['net'] for p in template['pads'] if p['ref']=='U14619' and p['num']=='7'))
 for l in('F.Cu','B.Cu'):
  assert abs(refs[l].area-prior['functional_source_root_witness']['In1.Cu' if l=='F.Cu' else 'In4.Cu']['source_rooted_fill_mm2'])<1e-8
  for label,s in [('actual',refs[l]),('original',oldrefs[l])]:p=cache/(label+'-'+l+'.wkb');p.write_bytes(s.wkb);A.READS[str(p)]=C.sha(s.wkb)
 nt={t['uuid']:t for t in ng['tracks']};diagnostics=[]
 for row in prior['unchanged_reference_losses']:
  t=nt[row['uuid']];body=LineString([t['s'],t['e']]).buffer(t['w']/2,resolution=128);lost=body.intersection(oldrefs[t['layer']]).difference(refs[t['layer']]);p=cache/(row['uuid']+'-old-covered-loss.wkb');p.write_bytes(lost.wkb)
  # Exact native quantized contour comparison. This labels and records a bound
  # only; it does not waive a loss or expand candidate fill/reference coverage.
  bounds={str(mm):lost.difference(refs[t['layer']].buffer(mm,resolution=128)).area for mm in(.0000001,.0000005,.000001,.000002,.000005,.005)}
  diagnostics.append({**row,'native_actual_loss_mm2':lost.area,'loss_bounds_mm':list(lost.bounds),'loss_WKB_path':str(p),'loss_WKB_sha256':C.sha(lost.wkb),'outside_actual_reference_distance_bounds_mm2':bounds,'waiver':False})
 # New SDI F polyline moves only its two short middle endpoints upward .025.
 # No via is moved and neither In1 nor In4 reference-plane cut is changed.
 points=[[375.498,128.5],[374.125,128.375],[373.925,128.325],[373.4,128.3]];rows=[]
 own=Point(373.4,128.3).buffer(.525,resolution=128)
 for a,b in zip(points,points[1:]):
  body=LineString([a,b]).buffer(.1,resolution=128);uncovered=body.difference(own).difference(refs['F.Cu']);pts=R.Q.P.K.D.components(uncovered)
  analytic=not uncovered.is_empty and all(math.dist(v[:2],(373.4,128.3))<=.525 for p in pts for v in p.exterior.coords)
  rows.append({'a':a,'b':b,'width_mm':.2,'full_body_uncovered_mm2':uncovered.area,'bounds_mm':list(uncovered.bounds) if not uncovered.is_empty else [],'only_exact_own_disk_chord_artifact':analytic,'reference_pass':uncovered.area<=1e-9 or analytic})
 report={'verdict':'EXACT_NATIVE_GAP_DIAGNOSIS_AND_LOCAL_CORRECTION_NOMINATION','native_R2_receipt_sha256':C.sha(A.read(HERE/'ao1-native-com-reference-independent-r2.json')),'actual_all_native_drilled_barrels_subtracted':len(ng['vias']),'small_model_source_rooted_area_agrees_with_full_independent_R2':True,'actual_rooted_reference_WKB_directory':str(cache),'functional_source_root_witness':wit,'unchanged_reference_set_loss_diagnostics':diagnostics,'SDI_F_upward_025mm_nomination':{'points':points,'segments':rows,'full_body_reference_nomination_pass':all(x['reference_pass'] for x in rows),'source_contact_clearance_F_COM_cut_and_native_gates':'OPEN'},'reference_loss_waivers':0,'native_jobs':0,'board_emitted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-start};out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'new_reference_nomination_pass':report['SDI_F_upward_025mm_nomination']['full_body_reference_nomination_pass'],'maximum_outside_1nm_contour_mm2':max(x['outside_actual_reference_distance_bounds_mm2']['1e-06'] for x in diagnostics),'sha256':C.sha(out.read_bytes()),'elapsed_seconds':report['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
