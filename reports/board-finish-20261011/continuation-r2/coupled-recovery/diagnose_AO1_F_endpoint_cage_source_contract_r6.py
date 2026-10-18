"""Bound the F-port blockage and inspect fresh source ownership, no repair."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
OUT=H/'AO1-F-endpoint-current-cage-and-fresh-source-contract-r6'
VREF='/motherboard_analog_output/AO1_VREF';COM='/motherboard_analog_output/AO1_COM';MON='/motherboard_analog_output/AO1_MON_12V'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for g in s.geoms for p in parts(g)]if hasattr(s,'geoms')else[]
def info(s):return{'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 rr=pin(H/'AO1-VREF-ONLY-NEW-native-intent-current-port-constructor-r4/receipt.json');r=json.loads(rr.read_bytes());cf=pin(rr.parent/'exact-current-Cu-continuous-source-only-regions.pkl',r['region_cache_SHA256']);d=pickle.loads(cf.read_bytes());cp=pin(H/'AO1-saved-four-add-exact-current-native-screen-r1/pinned-current-local-Cu-native-before-source-only-screen.pkl','0349ddad81a9dc6dd0ef106c3a65ce03e0ff44ae3d04244e882bbe0475590a2e');ctx=pickle.loads(cp.read_bytes());ep=Point(375.498,129);fc=[p for p in parts(d['free'][VREF,'F.Cu'])if p.covers(ep)];fs=[p for p in parts(d['sourcefree']['F.Cu'])if p.covers(ep)];fcu=unary_union(fc);fsource=unary_union(fs);v=d['viaregions'][VREF];ports={'current_Cu_only_F_endpoint_component':info(fcu),'current_Cu_and_SOURCE_F_endpoint_component':info(fsource),'Cu_only_legal_F_via_sites':info(fcu.intersection(v)),'Cu_and_SOURCE_legal_F_via_sites':info(fsource.intersection(v))}
 if not v.is_empty:
  a,b=nearest_points(ep,v);ports['nearest_legal_current_all6_via_to_endpoint_mm']=[b.x,b.y];ports['nearest_distance_mm']=a.distance(b)
 local=ctx['current'];rows=[]
 for t in local['tracks']:
  if t['layer']!='F.Cu' or K.L.norm(t['net'])==VREF:continue
  body=LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128)
  if body.distance(fsource)<.6:rows.append({'uuid':t['uuid'],'net':t['net'],'a':t['a'],'b':t['b'],'w':t['w'],'distance_to_endpoint_source_component_mm':body.distance(fsource)})
 put('literal-F-endpoint-cage-summary.json',ports);put('exact-nearby-retained-original-F-tracks.json',rows)
 nf=pin(ROOT/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net','070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2');doc=ET.fromstring(nf.read_bytes());nets=[];neededrefs=set()
 for n in doc.find('nets'):
  if K.L.norm(n.attrib['name'])in(VREF,COM,MON,'/motherboard_analog_output/AO1_DAC_SDI'):
   ns=[dict(q.attrib)for q in n];neededrefs.update(q['ref']for q in ns);nets.append({'raw_name':n.attrib['name'],'nodes':ns})
 components=[]
 for c in doc.find('components'):
  if c.attrib['ref']in neededrefs:
   components.append({'ref':c.attrib['ref'],'value':c.findtext('value'),'footprint':c.findtext('footprint'),'libsource':dict(c.find('libsource').attrib)if c.find('libsource')is not None else None})
 put('fresh-current-source-net-and-pin-contract.json',{'netlist_SHA256':sha(nf),'nets':nets,'components':components,'electrical_semantics_changed':False,'source_ERC_is_distinct_from_current_board_DRC':True})
 report={'verdict':'ACTUAL_CURRENT_F_VREF_ENDPOINT_BOUND_CAGE_CHARACTERIZED_SOURCE_CONTRACT_PINNED','ports':ports,'nearby_track_count':len(rows),'native_jobs':0,'Cu_changed':False,'source_changed':False,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',report);print(json.dumps({'verdict':report['verdict'],'ports':ports,'elapsed_seconds':report['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
