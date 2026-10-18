"""Finite exact fullwidth CM51 routes to ordinary via centre free polygons."""
import hashlib,json,math,pickle,sys,uuid,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import physical_reference_losses_r3_zero_r208 as RF
import tri_route as TR
O=H/'sbc-power/CM51-exact-polygon-routed-ordinary-ground-fanout-nominations-r276'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def zero(s):a=set_precision(s,0);assert a.wkb==s.wkb;return a
def buf(s,r):return zero(Z.bounded_buffer(s,r))
def main():
 assert not O.exists();O.mkdir();base=H/'sbc-power/R270-true-literal-DOB-current-filled-alignment-requalification-r271/T4-plus-R7';mp=base/'model.pkl';assert sha(mp)=='3d086d6f0935cd1760dc95c383049f04e86a31b2c4fb00d925e1d1c43d0be006';g,h,b,q,c=pickle.loads(mp.read_bytes());gp=base/'actual-drilled-groups.pkl';gs=pickle.loads(gp.read_bytes());root=K.root(gs['/LOGIC_GND'],'J11001','2');ref=zero(K.source_refs(root)['F.Cu']);rootby={l:[r for r in root if r['layer']==l and r['kind']=='fill']for l in K.LAYERS};rtrees={l:STRtree([r['shape']for r in rr])for l,rr in rootby.items()}
 dp=H/'sbc-power/CM51-ordinary-inward-first-ground-fanout-nominations-r275/partial-only-nominated-discrete.pkl';d=pickle.loads(dp.read_bytes());prior=json.loads((dp.parent/'receipt.json').read_text());tracks=d['tracks'][:];vias=d['vias'][:];accepted=prior['accepted'][:];done={r['pad_UUID']for r in accepted};dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get('/LOGIC_GND')else .6;rec,trees=F.build({**c,'zones':[]});holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([s for uid,n,s in holes]);smd=[(p,s)for p in h['pads']if p['smd']for l,ps in p['layers'].items()if l in('F.Cu','B.Cu')for s in L.poly(ps)];st=STRtree([s for p,s in smd]);vps=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vps);reserve,exempt=A.reservations();outline=unary_union(L.poly(h['outline'])).buffer(-.525);cm=sorted([p for p in h['pads']if p['ref']in('J15001','J15002')and p['net']=='/LOGIC_GND'],key=lambda p:(p['ref'],p['y'],p['x']));assert len(cm)==51;rows=[]
 for p in cm:
  if p['uuid']in done:continue
  start=[p['x'],p['y']];sp=Point(start);attempts=[];winner=None
  for radius in(2.,4.,8.):
   clip=box(sp.x-radius,sp.y-radius,sp.x+radius,sp.y+radius);broad=clip.buffer(1.3);tc=[];vc=[];ledger=[]
   for l in K.LAYERS:
    for j in trees[l].query(broad,predicate='intersects'):
     r=rec[l][int(j)]
     if L.norm(r['net'])=='/LOGIC_GND':continue
     clear=gap(r['net'])+.025+.000003
     if r['kind']=='track'and not r['source'].get('m'):
      t=r['source'];axis=LineString([t['a'],t['b']]);sh=buf(axis,t['w']/2+.25+clear);tr=buf(axis,t['w']/2+.1+clear)if l=='F.Cu'else None
     elif r['kind']=='via':v=r['source'];axis=Point(v['x'],v['y']);sh=buf(axis,v['d']/2+.25+clear);tr=buf(axis,v['d']/2+.1+clear)if l=='F.Cu'else None
     else:sh=buf(r['shape'],.25+clear);tr=buf(r['shape'],.1+clear)if l=='F.Cu'else None
     vc.append(sh)
     if tr is not None:tc.append(tr)
     ledger.append({'UUID':r['uuid'],'layer':l,'net':r['net'],'kind':r['kind'],'required_true_native_mm':gap(r['net']),'planner_reserve_mm':.025})
   for j in ht.query(broad,predicate='intersects'):
    uid,n,sh=holes[int(j)];vc.append(buf(sh,.380003))
    if L.norm(n)!='/LOGIC_GND':tc.append(buf(sh,.380003))
   for j in st.query(broad,predicate='intersects'):vc.append(buf(smd[int(j)][1],.380003))
   for j in vt.query(broad,predicate='intersects'):vc.append(buf(vps[int(j)],.815003))
   for v in vias:
    point=Point(v['x'],v['y'])
    if broad.intersects(point):vc.append(buf(point,.815003))
   for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
    for rule in rules:
     if ex and'/LOGIC_GND'in exempt.get(rule['name'],set()):continue
     layers=rule['layers'];shs=L.poly(rule['outline'])
     for sh in shs:
      if not broad.intersects(sh):continue
      if (ex or rule.get('no_tracks'))and'F.Cu'in layers:tc.append(buf(sh,.125003))
      if (ex or rule.get('no_vias'))and set(K.LAYERS)&set(layers):vc.append(buf(sh,.275003))
   sourcecentre=zero(ref.intersection(clip.buffer(.3))).buffer(-.100005);tf=clip.intersection(outline.buffer(-.100003)).intersection(sourcecentre).difference(unary_union(tc));faces=[x for x in RF.parts(tf)if x.covers(sp)];a={'radius_mm':radius,'foreign_hard_count':len(ledger),'exact_source_covered_track_start_face_count':len(faces),'attempts':[]};attempts.append(a)
   if not faces:continue
   vf=clip.intersection(outline.buffer(-.250003)).difference(unary_union(vc));(O/(p['uuid']+'-'+str(radius)+'-exact-via-centre-free.wkb')).write_bytes(vf.wkb)
   for fi,f in enumerate(faces):
    target=f.buffer(-.000005).intersection(vf);attempt={'face':fi,'via_target_empty':target.is_empty};a['attempts'].append(attempt)
    if target.is_empty:continue
    ep=nearest_points(sp,target)[1];end=[round(ep.x,6),round(ep.y,6)];pt=Point(end)
    if not(target.covers(pt)and f.covers(pt)):end=list(ep.coords[0]);pt=Point(end)
    path,method=TR.route(f,start,end);path=[[round(x,6),round(y,6)]for x,y in path]
    if not f.covers(LineString(path)):attempt['error']='rounded_path_outside_exact_free_face';continue
    vb=buf(pt,.25);drill=buf(pt,.10000002);ann=pt.buffer(.25,quad_segs=128).difference(drill);areas={l:sum(ann.intersection(rootby[l][int(j)]['shape']).area for j in rtrees[l].query(ann,predicate='intersects'))for l in K.LAYERS};errors=[];newtracks=[];refs=[]
    for n,(aa,bb)in enumerate(zip(path,path[1:])):
     body=buf(LineString([aa,bb]),.1);ctx=[holes[int(i)][2]for i in ht.query(body,predicate='intersects')];actual=body.difference(unary_union([*ctx,drill]));rg=actual.difference(ref);refs.append({'leg':n,'gap_mm2':rg.area,'gap_empty':rg.is_empty})
     if not rg.is_empty:errors.append({'kind':'actual_drilled_fullbody_reference','leg':n,'gap_mm2':rg.area})
     newtracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM51-R276:'+p['uuid']+':leg:'+str(n))),'net':'/LOGIC_GND','layer':'F.Cu','w':.2,'a':aa,'b':bb})
    if not any(x>0 for x in areas.values()):errors.append({'kind':'no_finite_actual_source_fill_annulus'})
    attempt.update(path=path,method=method,actual_fullbody_reference_rows=refs,actual_source_fill_annulus_mm2_by_layer=areas,errors=errors)
    if errors:continue
    v={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM51-R276:'+p['uuid']+':via')),'net':'/LOGIC_GND','x':end[0],'y':end[1],'d':.5,'drill':.2,'flashed':K.LAYERS};winner={'ref':p['ref'],'pin':p['num'],'pad_UUID':p['uuid'],'new_tracks':newtracks,'via':v,'finite_radius_mm':radius,'polygon_route':attempt,'full_analytic_later_joint_rebind_required':True};accepted.append(winner);tracks+=newtracks;vias.append(v);done.add(p['uuid']);break
   if winner:break
  rows.append({'ref':p['ref'],'pin':p['num'],'pad_UUID':p['uuid'],'accepted':winner is not None,'attempts':attempts});put(O/'exact-free-polygon-search-progress.json',rows);print('R276_PAD',p['ref'],p['num'],winner is not None,len(accepted),flush=True)
 put(O/'receipt.json',{'verdict':'CM51_ALL_ORDINARY_POLYGON_ROUTE_NOMINEES_CURRENT_HEAD_CONSTRUCTION_AND_SOURCE_PROOF_OPEN'if len(accepted)==51 else'CM51_PARTIAL_FINITE_POLYGON_ROUTE_NOMINATION_NO_COMPLETE_SOURCE_CREDIT','exact_nomination_model_sha256':sha(mp),'exact_prior_discrete_sha256':sha(dp),'CM_pad_count':51,'accepted_count':len(accepted),'remaining_count':51-len(accepted),'new_track_count':len(tracks),'new_via_count':len(vias),'accepted':accepted,'search_progress_file':'exact-free-polygon-search-progress.json','ordinary_width_diameter_drill_mm':[.2,.5,.2],'true_source_finite_annulus_no_generic_plane_disk':True,'local_foreign_antipads_current_full_contact_source_strictrefs_true_analytic_native_current_capacity_fault':'OPEN','CM_signed_return_A':3.5593046439628484,'no_equal_share_or_current_derating_credit':True,'inherited_failed_gates_preserved':True,'board_written':False,'native_jobs':0,'adopted':False,'script_sha256':sha(__file__)})
 (O/'only-nominated-discrete.pkl').write_bytes(pickle.dumps({'tracks':tracks,'vias':vias,'removed_original_track_UUIDs':[]},protocol=5));print('R276_COMPLETE',len(accepted),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
