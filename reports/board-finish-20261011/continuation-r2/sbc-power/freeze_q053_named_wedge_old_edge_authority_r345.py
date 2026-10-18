"""Freeze the exact authorized twelve cut intersections and negative wedges."""
from pathlib import Path
import json,hashlib,traceback
from shapely import from_wkb
from shapely.geometry import LineString,Polygon
H=Path(__file__).resolve().parent.parent
O=H/'sbc-power/q053-twelve-new-intersections-exact-old-edge-and-named-negative-wedge-authority-r345'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def geom(name,s):
 p=O/(name+'.wkb');p.write_bytes(s.wkb)
 return {'file':str(p.resolve()),'sha256':sha(p),'type':s.geom_type,'empty':s.is_empty,'area_mm2':s.area,'length_mm':s.length,'bounds':list(s.bounds)if not s.is_empty else None}
def main():
 assert not O.exists();O.mkdir()
 r339=H/'sbc-power/q053-R338-raw-gain-controlling-edge-and-declared-corridor-attribution-r339'
 r343=H/'sbc-power/q053-only-new-native-inward-intersection-splice-explicit-controlled-boundary-wedge-proposal-r343'
 assert sha(r339/'receipt.json')=='c9d0fac1b6e01d61b7c732952c12557b4fe3e8ff1bcb95a7d3ddba4e7ee5bf91'
 assert sha(r343/'receipt.json')=='0e246f659437a94cd6320c65ee3338eb2999c7e97fb278ecf59b587ce97528dc'
 a=json.loads((r339/'receipt.json').read_text());b=json.loads((r343/'receipt.json').read_text());nom={tuple(r['raw_new_vertex']):r for r in a['only_new_fractional_cut_intersections']};rows=[]
 for role in b['rows']:
  parent=from_wkb((r339/(role['role']+'-exact-parent.wkb')).read_bytes());assert hashlib.sha256(parent.wkb).hexdigest()==role['before_sha256']
  ps=list(parent.geoms)if parent.geom_type=='MultiPolygon'else[parent];edges={tuple((tuple(x),tuple(y)))for p in ps for r in[p.exterior,*p.interiors]for x,y in zip(list(r.coords),list(r.coords)[1:])}
  for i,s in enumerate(role['explicit_controlling_new_intersection_scopes']):
   v=tuple(s['raw_new_cut_intersection']);n=nom[v];edge=[tuple(x)for x in n['nearest_parent_edge']];assert tuple(edge)in edges or tuple(reversed(edge))in edges
   m=tuple(s['native_inward_replacement']);aa=tuple(s['unchanged_preceding_vertex']);bb=tuple(s['unchanged_following_vertex']);file=Path(s['explicit_negative_scope_file']);assert sha(file)==s['explicit_negative_scope_SHA256']
   rows.append({'role':role['role'],'index':i,'parent_role_sha256':role['before_sha256'],'whole_exact_original_controlling_edge':geom(role['role']+'-'+str(i)+'-unchanged-before-controlling-edge',LineString(edge)),'original_edge_coordinate_tokens':edge,'new_cut_intersection':v,'native_inward_replacement':m,'unchanged_preceding_vertex':aa,'unchanged_following_vertex':bb,'actual_two_incident_negative_wedges':[geom(role['role']+'-'+str(i)+'-preceding-exact-wedge',Polygon([v,m,aa,v])),geom(role['role']+'-'+str(i)+'-following-exact-wedge',Polygon([v,m,bb,v]))],'only_named_local_scope_file':str(file.resolve()),'only_named_local_scope_sha256':sha(file),'outside_prior_corridor':s['scope_outside_prior_declared_corridor'],'original_edge_exact_in_parent':True})
 whole=[]
 for r in b['rows']:
  whole.append({'role':r['role'],'literal_no_gain':r['strict_gain_EMPTY'],'actual_whole_additional_negative_wedges':r['extra_negative_outside_primary_guard'],'exact_outside_prior_corridor_witness':r['extra_negative_outside_declared_owner_corridor'],'removed':r['removed']})
  for k in('extra_negative_outside_primary_guard','extra_negative_outside_declared_owner_corridor','removed'):assert sha(r[k]['file'])==r[k]['sha256']
 bad=H/'sbc-power/construct_CM79_q053_literal_original_vertex_splice_current_r344.py'
 put(O/'frozen-r344-compile-failure.json',{'script':str(bad.resolve()),'sha256':sha(bad),'failure':'IndentationError: unexpected indent at expanded line 69','no_directory_model_or_geometry_emitted':True,'reason':'Missing main-body indentation on appended roles initialization; separately named successor required'})
 put(O/'exact-before-edge-twelve-intersection-whole-negative-wedge-ledger.json',{'R339_receipt_sha256':sha(r339/'receipt.json'),'R343_receipt_sha256':sha(r343/'receipt.json'),'rows':rows,'whole_actual_negative_and_outside_old_corridor':whole,'authorized_scope':'ONLY bound normal new-primitive cut plus these named incident-edge wedge polygons; no rectangle expansion, remote trim or regrid','all_unaffected_old_coordinate_tokens_preserved':True,'source_contacts_references_current_mesh_native':'OPEN'})
 manifest={str(p.resolve()):sha(p)for p in O.iterdir()if p.is_file()}
 put(O/'receipt.json',{'verdict':'EXACT_NAMED_NEGATIVE_WEDGE_AND_ORIGINAL_EDGE_AUTHORITY_FROZEN_NO_MODEL','files':manifest,'twelve_intersections_per_role':len(rows)//2,'roles':2,'literal_no_gain_both_roles':True,'source_contacts_references_current_mesh_native':'OPEN','adopted':False,'script_sha256':sha(__file__)})
 print('R345_AUTHORITY',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc()})
  raise
