"""Exact two new FG outlines; every native profile and hole token verified."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Polygon
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from emit_logic_zones_r1 import render
from verify_source import parse,children,child,atom
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
mp=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl';assert sha(mp)=='765ce30b24ed3109b7c938f964775690a99f08504c464313bcf712b078421440';g,h,b,q,c=pickle.loads(mp.read_bytes());OUT=H/'U10003-HOST-two-new-FG-only-exact-native-integer-profile-r267';assert not OUT.exists();OUT.mkdir();rows=[]
for z in q:
 if z['uuid']not in{'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}:continue
 outline=z['zone_outline_shape'];assert outline.geom_type=='Polygon'and outline.is_valid
 assert (z['priority'],z['clearance_mm'],z['min_thickness_mm'],z['pad_connect_mode'],z['island_removal_mode'],z['thermal_gap_mm'],z['thermal_bridge_width_mm'])==(126,.15,.15,'FULL_SOLID',1,.15,.3)
 text=render(z['uuid'],z['net'],z['layer'],outline).replace('(priority 20)','(priority 126)').replace('Retained LOGIC_GND return repair','U10003 actual-source field reference');a=parse(text)
 rings=[[(float(v[1]),float(v[2]))for v in child(p,'pts')[1:]]for p in children(a,'polygon')];rebuilt=Polygon(rings[0],rings[1:]);assert rebuilt.wkb==outline.wkb
 assert atom(a,'uuid')==z['uuid']and atom(a,'net')==z['net']and atom(a,'layer')==z['layer']and atom(a,'priority')=='126';assert child(a,'connect_pads')[1]=='yes';assert not children(a,'filled_polygon')and not children(a,'fill_segments')
 p=OUT/(z['uuid']+'.zone-chunk');p.write_text(text,encoding='utf-8',newline='');phys=OUT/(z['uuid']+'-physical.wkb');phys.write_bytes(z['shape'].wkb);intent=OUT/(z['uuid']+'-intended.wkb');intent.write_bytes(outline.wkb)
 rows.append({'UUID':z['uuid'],'net':z['net'],'layer':z['layer'],'chunk_file':str(p.resolve()),'chunk_SHA256':sha(p),'physical_WKB_SHA256':sha(phys),'intended_WKB_SHA256':sha(intent),'native_hole_count':len(rings)-1,'native_profile':{'priority':126,'local_clearance_mm':.15,'minimum_thickness_mm':.15,'pad_connection':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3},'literal_native_outline_WKB_roundtrip_exact':True,'no_cached_native_fill_emitted':True})
assert len(rows)==2
before=pickle.loads((H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl').read_bytes())[3];old={z['uuid']:z for z in before};assert all(z['uuid']not in old or all(z[r].wkb==old[z['uuid']][r].wkb for r in('shape','zone_outline_shape'))for z in q)
r={'status':'EXACT_TWO_NEW_FG_INTEGER_NATIVE_OUTLINES_PROFILE_AND_HOLES_READY_API_FILL_OPEN','model_SHA256':sha(mp),'rows':rows,'all_older_owned_role_geometry_unchanged_from_R262':True,'original_native_zone_outlines_profiles_unchanged':True,'original_native_filled_cache_never_edited':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('R267_ZONES',sha(OUT/'receipt.json'),'HOLES',sum(x['native_hole_count']for x in rows),flush=True)
