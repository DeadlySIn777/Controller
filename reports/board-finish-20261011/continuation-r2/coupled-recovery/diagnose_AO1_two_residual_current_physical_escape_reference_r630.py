"""Separate DAC-CS physical escape walls from missing COM reference support."""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.geometry import Point
from shapely.ops import unary_union
OUT=H/'AO1-two-residual-current-physical-escape-versus-source-reference-attribution-r630';NET='/motherboard_analog_output/AO1_DAC_CS_N'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pieces(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for x in getattr(s,'geoms',[])for p in pieces(x)]
def inf(s):return{'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');_,h,_,_,_=pickle.loads(mp.read_bytes());pf=pin(H/'AO1-DAC-CS-current-ordinary-F-In3-B-two-pair-constructor-r624/bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl');ca=pickle.loads(pf.read_bytes());cf=pin(H/'AO1-COM-actual-full-native-current-source-and-two-residual-port-binding-r622/exact_actual_current_AO1_COM_source_and_ports_NOMINATION_ONLY.pkl','02e9ea37628b2dba138d1e57514a390f1c4419ef3ca8c66ed6f2653eecb6b72b');refs=pickle.loads(cf.read_bytes())['references'];rows=[]
 ef=pin(H/'AO1-ENABLE-current-ordinary-F-In3-B-two-pair-constructor-r626/bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl');enable=pickle.loads(ef.read_bytes());cs=ca
 for uid,ly,rly,net,ca in[('5bd36a6a-0ece-4d8a-bb54-e362786d2249','F.Cu','In1.Cu',NET,cs),('6cc6e8f2-29a9-482e-a9b7-c53dea062394','B.Cu','In4.Cu',NET,cs),('aacc0bdf-0449-4b0f-95b8-cccb718c4d90','B.Cu','In4.Cu',NET,cs),('e1c48f25-f337-46ce-9587-4b5f4df4573a','F.Cu','In1.Cu','/motherboard_analog_output/AO1_ENABLE_ISOLATED',enable),('81cec19c-07ad-4052-81d7-07d09940c79e','B.Cu','In4.Cu','/motherboard_analog_output/AO1_ENABLE_ISOLATED',enable)]:
  p=next(p for p in h['pads']if p['uuid']==uid);point=Point(p['x'],p['y']);face=unary_union([s for s in pieces(ca['free'][net,ly])if s.covers(point)]);physical=face.intersection(ca['via'][net]);source=refs[rly];supported=physical.intersection(source.buffer(-.105,quad_segs=128));missing=point.buffer(.105005,quad_segs=128).difference(source);tag=p['ref']+'-'+str(p['num']);(OUT/(tag+'-current-physical-connected-face.wkb')).write_bytes(face.wkb);(OUT/(tag+'-physical-signal-via-potential.wkb')).write_bytes(physical.wkb);(OUT/(tag+'-source-supported-signal-via-region.wkb')).write_bytes(supported.wkb);rows.append({'ref':p['ref'],'pin':str(p['num']),'UUID':uid,'net':net,'at_mm':[p['x'],p['y']],'layer':ly,'required_source_plane':rly,'actual_current_source_covers_origin':source.covers(point),'actual_source_origin_distance_mm':point.distance(source),'literal_source_origin_disk_gap':inf(missing),'physical_face':inf(face),'all_layer_and_hole_legal_signal_via_region_inside_physical_face':inf(physical),'source_supported_via_region_inside_physical_face':inf(supported)});print('R630_PORT',tag,'sourceorigin',source.covers(point),'physical_via',physical.area,'source_via',supported.area,flush=True)
 (OUT/'receipt.json').write_text(json.dumps({'verdict':'CURRENT_AO1_TWO_RESIDUAL_ESCAPE_AND_SOURCE_REFERENCE_FAILURE_ATTRIBUTED_NO_WAIVER','input_SHA256':pins,'ports':rows,'all_original_Cu_and_VREF_four_peer_constraints_held':True,'native_jobs':0,'adopted':False,'current_source_contact_routing_body_native_current_SI':'OPEN','elapsed_seconds':time.monotonic()-st},indent=1,allow_nan=False)+'\n');print('R630_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
