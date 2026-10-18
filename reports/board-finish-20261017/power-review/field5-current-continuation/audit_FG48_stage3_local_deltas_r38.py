"""Close local new-ground foreign-Cu/HoleSet deltas from actual R299 to stage3."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,math,re
import shapely
from shapely.geometry import Point
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'additive-FG48-stage3-local-delta-guard-r38';MAN=HERE/'additive-FG48-stage3-sparse-packet-r36/manifest.json';OLD=ROOT/'reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb';hp=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(name,p):s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
H=module('pcbtext',hp);P=module('sexpr',HERE/'freeze_single_outer_power_packet_r11.py')
def value(node,key):return next((x for x in node[1:]if isinstance(x,list)and x[0]==key),None)
def main():
 assert not OUT.exists();OUT.mkdir();d=json.loads(MAN.read_text());base=Path(d['parent_board']);assert sha(base)==d['parent_board_SHA256'];oa,oc,ot=H.split(OLD.read_bytes());ba,bc,bt=H.split(base.read_bytes());old={H.chunk_uuid(c):c for c in oc if H.chunk_uuid(c)};now={H.chunk_uuid(c):c for c in bc if H.chunk_uuid(c)};body=shapely.from_wkb((HERE/'additive-existing-barrel-FG48-In3-host-r35/new-track-body-upper-envelope.wkb').read_bytes());zones=[u for u,c in old.items()if H.chunk_kind(c)=='zone'];assert all(now.get(u)==old[u]for u in zones);assert not[u for u,c in now.items()if H.chunk_kind(c)=='zone'and u not in old];rows=[];fails=[]
 for u in sorted(set(old)|set(now)):
  if old.get(u)==now.get(u):continue
  c=now.get(u)or old[u];kind=H.chunk_kind(c);r={'UUID':u,'kind':kind,'action':'change'if u in old and u in now else'add'if u in now else'remove'}
  if kind in('segment','arc'):
   assert b'(layer "In3.Cu")'not in c;r['reason']='Changed or added/retired track is on another layer; no drill.'
  elif kind=='via':
   tree=P.parsed(c);at=value(tree,b'at');xy=[float(x)for x in at[1:3]];size=float(value(tree,b'size')[1]);drill=float(value(tree,b'drill')[1]);gap=body.distance(Point(*xy))-max(size/2,drill/2);r.update(center_mm=xy,outer_diameter_mm=size,drill_mm=drill,guaranteed_body_to_true_circle_gap_mm=gap,reason='All edited via circles are remote from the new In3 body.');assert gap>.6251
  elif kind=='footprint':
   assert u in old and u in now;a=P.parsed(old[u]);b=P.parsed(now[u]);assert value(a,b'at')==value(b,b'at')and value(a,b'layer')==value(b,b'layer');ap=[x for x in a[1:]if isinstance(x,list)and x[0]==b'pad'];bp=[x for x in b[1:]if isinstance(x,list)and x[0]==b'pad']
   if ap==bp:r['reason']='All native pad geometries, drill nodes, placement and layer unchanged; property-only footprint delta.'
   else:
    for p in ap+bp:
     assert p[2]==b'smd'and value(p,b'drill')is None;layers=value(p,b'layers');assert b'"In3.Cu"'not in layers and b'"*.Cu"'not in layers
    r['reason']='Changed pad-angle metadata is exclusively surface-mount with no drills or In3 copper; existing root canonical-angle/source gates remain separate.'
  else:fails.append(r)
  rows.append(r)
 assert not fails;allnon=lambda cs:[c for c in cs if H.chunk_uuid(c)is None];same_non_uuid=oa==ba and ot==bt and allnon(oc)==allnon(bc);assert same_non_uuid;r={'utc':datetime.now(timezone.utc).isoformat(),'status':'EXACT_STAGE3_LOCAL_FOREIGN_CU_DRILL_ZONE_RULE_DELTA_GUARD_PASS','input_sha256':{str(p):sha(p)for p in(MAN,base,OLD,Path(__file__),hp,HERE/'freeze_single_outer_power_packet_r11.py',HERE/'additive-existing-barrel-FG48-In3-host-r35/new-track-body-upper-envelope.wkb')},'all_native_zone_and_rulearea_chunks_unchanged':len(zones),'all_non_UUID_board_settings_outline_rule_profile_bytes_unchanged':same_non_uuid,'all_different_UUID_chunks_reviewed':rows,'new_or_changed_In3_foreign_tracks':0,'new_or_changed_nearby_foreign_or_true_drill_obstacles':0,'native_ruleareas_and_source_intents_unchanged':True,'existing_canonical_surface_pad_source_contact_proofs':'Root metadata geometry receipts and fresh actual native AFTER remain separate, not claimed by this local obstacle guard.','native_fill_DRC_all_source_return_current_signed_KCL_material_thermal_SI':'OPEN','native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'changed_chunks_reviewed':len(rows),'zones_ruleareas_exact':len(zones)}))
if __name__=='__main__':main()
