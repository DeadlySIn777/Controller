"""Reuse exact R94 legal regions for finite-contact R95 ordinary port pairs."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import from_wkb,set_precision,get_num_coordinates
from shapely.geometry import LineString
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for folder in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/folder))
import contact_layout as C
import guarded_declared_settings_projection_r58 as N
import tri_route as T
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for q in getattr(s,'geoms',[])for p in parts(q)]
def main():
 assert len(sys.argv)==2,'exact frozen R95 receipt SHA'
 parent=H/'joint-positive-head-signal-reference-mask-proposal-r83';mp=parent/'model.pkl';assert sha(mp)=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c';ports=H/'CORE-partial-annular-native-IO3-antipad-port-nominees-r95';assert sha(ports/'receipt.json')==sys.argv[1];r95=json.loads((ports/'receipt.json').read_bytes());assert r95['parent_model_sha256']==sha(mp)and r95['all_clearance_hole_keepout_oldreference_predicates_unchanged']
 cache=H/'CORE-two-new-ordinary-port-layer-feed-proposals-r94';assert sha(cache/'receipt.json')=='a49cdd8478de883fd3b57c3f4b92abae2ca6cb2c51a1f0bc8209adca7a7db369';assert json.loads((cache/'receipt.json').read_bytes())['parent_model_sha256']==sha(mp)
 script=H/'nominate_CORE_partial_annular_external_ports_r95.py';assert sha(script)=='b943403a1da6e5d56e512fc5c6215f42bfad430441ee49dee8a0a6b959f03178';g,h,b,z,current=pickle.loads(mp.read_bytes());sources=pickle.loads((ports/'source-prospective-new-ordinary-ports.pkl').read_bytes());targets=pickle.loads((ports/'main-prospective-new-ordinary-ports.pkl').read_bytes());assert 0<len(sources)<=20 and 0<len(targets)<=20
 out=H/'CORE-partial-port-cached-layer-feed-proposals-r96';assert not out.exists();out.mkdir();pins={str(p.resolve()):sha(p)for p in [mp,ports/'receipt.json',cache/'receipt.json',script,ports/'source-prospective-new-ordinary-ports.pkl',ports/'main-prospective-new-ordinary-ports.pkl']};routes=[];attempts=[];raw='/CORE_1V2';in2=[q['uuid']for q in z if q['layer']=='In2.Cu'and q['uuid'].startswith('6b1d4fb8-')];assert len(in2)==1;cuttable={'In2.Cu':in2[0],'In3.Cu':'47888e35-9a96-5393-b579-7c0b4a64ec93'}
 for layer in ('In2.Cu','F.Cu','B.Cu','In4.Cu','In3.Cu','In1.Cu'):
  lp=cache/(layer+'-legal.wkb');pins[str(lp.resolve())]=sha(lp);legal=from_wkb(lp.read_bytes());print('R96_CACHED_LAYER',layer,len(sources),len(targets),flush=True)
  for width in (4.,3.,2.,1.,.5,.35,.25):
   common=[]
   for face in parts(legal.buffer(-width/2-.000100)):
    aa=[];bb=[]
    for nominee in sources:
     v=nominee['via'];ann=N.bounded_disk(v,.25).difference(N.bounded_disk(v,.1));contact=face.intersection(ann)
     if contact.area>.01:aa.append((v,ann,contact))
    for nominee in targets:
     v=nominee['via'];ann=N.bounded_disk(v,.25).difference(N.bounded_disk(v,.1));contact=face.intersection(ann)
     if contact.area>.01:bb.append((v,ann,contact))
    common.extend((a[2].distance(c[2]),face,a,c)for a in aa for c in bb)
   attempts.append({'layer':layer,'minimum_core_width_mm':width,'common_nominee_pairs_and_faces':len(common)});put(out/'route-face-checkpoint.json',attempts)
   for distance,face,aa,bb in sorted(common,key=lambda q:q[0]):
    vs,sa,sc=aa;vt,ta,tc=bb
    if get_num_coordinates(face)>5000:
     simple=face.buffer(-.002).simplify(.0005,preserve_topology=True).intersection(face);eligible=[p for p in parts(simple)if p.intersection(sc).area>.01 and p.intersection(tc).area>.01]
     if not eligible:continue
     face=max(eligible,key=lambda q:q.area);sc=face.intersection(sc);tc=face.intersection(tc)
    a,end=nearest_points(sc,tc);chord=LineString([a,end]);print('R96_ROUTE',layer,width,distance,get_num_coordinates(face),flush=True)
    if face.covers(chord):points=list(chord.coords);proof={'method':'exact_covered_nearest_chord'}
    else:
     try:points,proof=T.route(face,tuple(a.coords[0]),tuple(end.coords[0]))
     except(AssertionError,ValueError):continue
    points=[[round(x,6),round(y,6)]for x,y in points];line=LineString(points)
    if not face.covers(line)or not legal.covers(N.bounded_buffer(line,width/2)):continue
    native=set_precision(unary_union([p for p in parts(N.bounded_buffer(line,max(.6,width)).intersection(legal))if p.intersection(N.bounded_buffer(line,width/2)).area>0]),1e-6);pair=[vs,vt];holes=unary_union([N.bounded_disk(v,v['drill']/2)for v in h['vias']+pair if v['net']==raw]+[p for pad in h['pads']if pad['net']==raw for p in C.poly(pad.get('hole')or[])]);physical=native.difference(holes)
    if physical.intersection(sa).area<.01 or physical.intersection(ta).area<.01:continue
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-core-partial-port-layer-feed-r96/'+layer+'/'+repr(points)));q={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':native,'priority':124,'clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3,'physical_Cu_drill_subtracted':True,'label':'CORE finite native fill contact ordinary port feed R96'};routes.append({'zone':q,'vias':pair,'width_core_mm':width,'length_mm':line.length,'points':points,'route_constructor':proof,'only_new_owned_LG_notch_proposed':cuttable.get(layer),'normal_native_IO3_antipads_required':'54921f4b-0308-4821-9549-ff9360bf05ca'});break
   if routes:break
  if routes:break
 assert all(sha(p)==value for p,value in pins.items());put(out/'input-bytes.json',pins);(out/'proposed-route-and-zone.pkl').write_bytes(pickle.dumps(routes,protocol=5));(out/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':routes[0]['vias']if routes else[],'tracks':[]},protocol=5));put(out/'receipt.json',{'verdict':'CORE_PARTIAL_CONTACT_NEW_ORDINARY_PAIR_FEED_NOMINEE_FULL_GATES_OPEN'if routes else'NO_ACCEPTED_PARTIAL_CONTACT_PAIR_FEED_IN_DECLARED_SIX_CACHED_REGIONS','parent_model_sha256':sha(mp),'R95_receipt_sha256':sha(ports/'receipt.json'),'R94_cached_legal_regions_receipt_sha256':sha(cache/'receipt.json'),'source_nominees':len(sources),'target_nominees':len(targets),'route_count':len(routes),'routes':[{'zone_UUID':r['zone']['uuid'],'layer':r['zone']['layer'],'physical_WKB_sha256':hashlib.sha256(r['zone']['shape'].wkb).hexdigest(),'length_mm':r['length_mm'],'width_core_mm':r['width_core_mm'],'ordinary_new_vias':[v['uuid']for v in r['vias']],'proposed_LG_notch':r['only_new_owned_LG_notch_proposed']}for r in routes],'attempts':attempts,'full_CORE1V2_load_A':.8,'full_IO3_load_A':2.,'all77_source_direct_layer_contacts_full_return_current_drop_stability_native':'OPEN','original104_power_reference_candidate_and_failed_source_ledgers_not_waived':True,'native_jobs':0,'board_written':False,'adopted':False});print('R96_CACHED_PAIR_FEED_FROZEN',len(routes),sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
