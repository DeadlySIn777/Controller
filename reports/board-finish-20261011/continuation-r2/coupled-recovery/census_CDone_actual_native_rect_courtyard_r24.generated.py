"""Inspect isolated FPGA CDONE producer with exact current Cu and native SOURCE.

No repair, new drill or process exception is emitted by this census.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from verify_source import parse,children,child,atom
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union,polygonize
OUT=H/'FPGA-CDONE-actual-native-courtyard-current-anchor-return-census-r24'
NET='/fpga_core/FPGA_CDONE';LG='/LOGIC_GND'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def info(s):return{'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,w=None):
  p=Path(p);v=sha(p);assert w is None or v==w;pins[str(p.resolve())]=v;return p
 bp=pin(ROOT/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-model.pkl','dbeba66691d45ee12206f77e5060b4c845681014d19b3d9e633e9aed08a2b0c2');c=pickle.loads(bp.read_bytes());gf=pin(bp.parent/'actual-full-R157-before-all-net-groups.pkl','d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a');groups=pickle.loads(gf.read_bytes());source=K.root(groups[LG],'J11001','2');refs={ly:unary_union([q['shape']for q in source if q['kind']=='fill'and q['layer']==ly])for ly in('In1.Cu','In4.Cu')};sourcekeys=K.keys(source);target=next(p for p in c['pads']if p['ref']=='U1001'and str(p['num'])=='R1');assert K.L.norm(target['net'])==NET and(target['x'],target['y'])==(155.29,94.877);producerGroup=next(g for g in groups[NET]if any(q['kind']=='pad'and q['uuid']==target['uuid']for q in g))
 sp=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');native=K.C.inventory(sp.read_bytes())[3];ident=K.A.N.SourceNets(sp.read_bytes());ep=pin(ROOT/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json','13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3');expected=json.loads(ep.read_bytes())['copper'];posefile=pin(ROOT/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json','ffa3ff0880c004a6c4ad443b60bed9015a8094a04c952bdd56d09ec60d59b91d');pose=json.loads(posefile.read_bytes());pr=pose['pads'][target['uuid']];assert(str(pr[0]),pr[1],pr[2]/1e6,pr[3]/1e6)==('R1',target['net'],155.29,94.877)
 originalNetCu=[t for t in c['tracks']+c['vias']if K.L.norm(t['net'])==NET]
 for t in originalNetCu:
  e=expected[t['uuid']];assert e['raw_net']==t['net']
  if'd'in t:assert e['at_IU']==[round(t['x']*1e6),round(t['y']*1e6)]and e['drill_IU']==round(t['drill']*1e6)
  else:assert e['start_IU']==[round(x*1e6)for x in t['a']]and e['end_IU']==[round(x*1e6)for x in t['b']]and e['width_IU']==round(t['w']*1e6)
 fuid=next(u for u,r in pose['footprints'].items()if r[0]=='U1001');fp=parse(native[fuid].decode());at=child(fp,'at');assert atom(fp,'layer')=='F.Cu'and len(at)>=3 and(len(at)<4 or float(at[3])==0);loc=[float(x)for x in at[1:3]];lines=[]
 for line in children(fp,'fp_line'):
  if atom(line,'layer')=='F.CrtYd':a=child(line,'start')[1:3];b=child(line,'end')[1:3];lines.append(LineString([(loc[0]+float(a[0]),loc[1]+float(a[1])),(loc[0]+float(b[0]),loc[1]+float(b[1]))]))
 polygons=[]
 for poly in children(fp,'fp_poly'):
  if atom(poly,'layer')=='F.CrtYd':polygons.append(Polygon([(loc[0]+float(q[1]),loc[1]+float(q[2]))for q in child(poly,'pts')[1:]]))
 for rect in children(fp,'fp_rect'):
  if atom(rect,'layer')=='F.CrtYd':
   aa=child(rect,'start')[1:3];bb=child(rect,'end')[1:3];polygons.append(box(loc[0]+min(float(aa[0]),float(bb[0])),loc[1]+min(float(aa[1]),float(bb[1])),loc[0]+max(float(aa[0]),float(bb[0])),loc[1]+max(float(aa[1]),float(bb[1]))))
 put('native-footprint-courtyard-primitive-schema.json',[{'kind':p[0],'layer':atom(p,'layer')}for p in fp[1:]if isinstance(p,list)and p[0].startswith('fp_')and atom(p,'layer')and 'CrtYd'in atom(p,'layer')])
 courtyard=unary_union(polygons+list(polygonize(lines)));assert not courtyard.is_empty and courtyard.covers(Point(target['x'],target['y']));put('actual-source-FPGA-courtyard-D4-D5-scope.json',{'footprint_UUID':fuid,'reference':'U1001','actual_current_native_pose':pose['footprints'][fuid],'native_chunk_SHA256':hashlib.sha256(native[fuid]).hexdigest(),'courtyard':info(courtyard),'D4_only_this_real_courtyard':True,'D5_Bfirst_no_In1_In4_zone_redesign':True});(OUT/'actual-native-U1001-F-courtyard.wkb').write_bytes(courtyard.wkb)
 win=courtyard.envelope.buffer(3);tracks=[];vias=[];oldvia={v['uuid']:v for v in c['vias']}
 for uid,e in expected.items():
  if e['kind']=='via':
   v={'uuid':uid,'net':e['raw_net'],'x':e['at_IU'][0]/1e6,'y':e['at_IU'][1]/1e6,'d':next(iter(e['diameters_IU'].values()))/1e6,'drill':e['drill_IU']/1e6,'flashed':oldvia[uid]['flashed']if uid in oldvia else list(K.LAYERS)}
   if win.covers(Point(v['x'],v['y'])):vias.append(v)
  else:
   t={'uuid':uid,'net':e['raw_net'],'layer':e['layer'],'a':[x/1e6 for x in e['start_IU']],'b':[x/1e6 for x in e['end_IU']],'w':e['width_IU']/1e6}
   if not LineString([t['a'],t['b']]).envelope.disjoint(win):tracks.append(t)
 pads=[p for p in c['pads']if win.covers(Point(p['x'],p['y']))];local={**c,'tracks':tracks,'vias':vias,'pads':pads,'zones':[]};returns=[]
 groundpads=[p for p in c['pads']if p['ref']=='U1001'and K.L.norm(p['net'])==LG]
 for p in groundpads:
  if math.dist([p['x'],p['y']],[target['x'],target['y']])>3:continue
  padbody=unary_union(K.L.poly(p['layers'].get('F.Cu',[])))
  for v in vias:
   if K.L.norm(v['net'])!=LG or math.dist([v['x'],v['y']],[p['x'],p['y']])>.65:continue
   ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));direct=padbody.intersection(ann);finite={ly:ann.intersection(refs[ly]).area for ly in refs};row={'via':v,'same_part_ground_pad_UUID':p['uuid'],'same_part_ground_ball':str(p['num']),'ground_ball_at_mm':[p['x'],p['y']],'pad_to_via_direct_annular_contact':info(direct),'signal_ball_to_return_centre_mm':math.dist([target['x'],target['y']],[v['x'],v['y']]),'actually_observed_In1_In4_masks':all(ly in v['flashed']for ly in('In1.Cu','In4.Cu')),'actual_SOURCE_ground_layer_keys':all(('via',v['uuid'],ly)in sourcekeys for ly in('In1.Cu','In4.Cu')),'finite_actual_SOURCE_annular_area_mm2':finite,'direct_ownership_contact_proven':not direct.is_empty and direct.area>0};returns.append(row)
 anchors=[]
 for index,g in enumerate(groups[NET]):
  for q in g:
   if q['layer']!='B.Cu' or q['kind']not in('via','track','pad'):continue
   anchors.append({'native_group':index,'kind':q['kind'],'UUID':q['uuid'],'layer':q['layer'],'shape':info(q['shape']),'distance_to_producer_mm':q['shape'].distance(Point(target['x'],target['y'])),'SOURCE_In4_supported_portion':info(q['shape'].intersection(refs['In4.Cu']))})
 put('CDONE-actual-native-group-pad-and-B-anchor-census.json',{'raw_net':target['net'],'producer_pad':{k:target[k]for k in('uuid','ref','num','net','x','y','smd')},'group_count':len(groups[NET]),'producer_group_nonfill_keys':[list(k)for k in K.keys(producerGroup)],'B_anchors':sorted(anchors,key=lambda q:q['distance_to_producer_mm'])});put('nearby-same-U1001-LG-return-observed-SOURCE-annuli.json',returns);put('nearby-actual-U1001-native-pads.json',[{k:p[k]for k in('uuid','ref','num','net','x','y','smd')}for p in pads if p['ref']=='U1001'and math.dist([p['x'],p['y']],[target['x'],target['y']])<2])
 nf=pin(ROOT/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net','070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2');nd=parse(nf.read_text());n=next(n for n in children(child(nd,'nets'),'net')if K.L.norm(atom(n,'name'))==NET);put('fresh-CDONE-source-pin-contract.json',{'raw_net':atom(n,'name'),'nodes':[{q[0]:q[1]for q in p[1:]}for p in children(n,'node')],'SOURCE_names_not_renamed':True})
 cache=OUT/'exact-current-CDONE-local-Cu-full-before-SOURCE-and-D4-courtyard.pkl';cache.write_bytes(pickle.dumps({'full_before':c,'groups':groups[NET],'ground_SOURCE':source,'source_refs':refs,'local_current':local,'producer':target,'courtyard':courtyard,'own_return_candidates':returns,'current_native_source':str(sp),'win':win},protocol=5));result={'verdict':'CDONE_NATIVE_PRODUCER_CURRENT_Cu_B_ANCHORS_AND_OWN_SOURCE_RETURN_CENSUS_BOUND','producer_group_discrete_keys':len(K.keys(producerGroup)),'CDONE_groups':len(groups[NET]),'B_anchor_records':len(anchors),'near_own_return_candidates':len(returns),'direct_owned_and_both_SOURCE_plane_return_candidates':sum(q['direct_ownership_contact_proven']and q['actually_observed_In1_In4_masks']and q['actual_SOURCE_ground_layer_keys']and all(a>0 for a in q['finite_actual_SOURCE_annular_area_mm2'].values())for q in returns),'local_current_tracks':len(tracks),'local_current_vias':len(vias),'new_via_or_process_exception_locations':0,'cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'native_jobs':0,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','producer_group_discrete_keys','CDONE_groups','B_anchor_records','near_own_return_candidates','direct_owned_and_both_SOURCE_plane_return_candidates','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
