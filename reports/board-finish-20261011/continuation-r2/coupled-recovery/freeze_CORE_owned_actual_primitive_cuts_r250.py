"""Add exact new primitive masks to immutable actual owned fill records."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
src=H/'construct_CORE_R112_local_reserve_immutable_owned_r246.py'
dst=H/'construct_CORE_R112_owned_actual_primitive_cuts_r250.py'
assert not dst.exists()
t=src.read_text().replace('construction-r246','construction-r250').replace('R246_','R250_')
t=t.replace('from shapely.geometry import box','from shapely.geometry import box,Point')
anchor="before_records=before['fills'][layer];pieces=L.poly(before_records);"
assert t.count(anchor)==1
replacement="""before_records=before['fills'][layer];primitive=[];oldvia={v['uuid']for v in h0['vias']};newvia=[v for v in h['vias']if v['uuid']not in oldvia];assert len(newvia)==2;newcore=by['b0453302-df03-561f-9bc4-0560bc66658a'];dom=h['domains_normalized'];domain_gap=lambda a,b:.15 if dom.get(L.norm(a))==dom.get(L.norm(b))else .6
  for via in newvia:
   same=L.norm(z['net'])==L.norm(via['net']);radius=via['drill']/2 if same else max(via['drill']/2+.275+.0001,via['d']/2+max(float(z['clearance_mm']),domain_gap(z['net'],via['net']))+.025+.0001);mask=Z.bounded_disk(via,radius);mask_zero=set_precision(mask,0);assert mask_zero.wkb==mask.wkb;mf=O/(uid+'-'+via['uuid']+'-exact-new-ordinary-filled-cut.wkb');mf.write_bytes(mask.wkb);primitive.append({'new_UUID':via['uuid'],'kind':'same_raw_net_new_drill'if same else'new_ordinary_foreign_annulus_drill_antipad','radius_mm':radius,'cut_WKB_file':str(mf),'cut_WKB_sha256':C.sha(mask.wkb),'shape':mask_zero})
  if layer==newcore['layer']and L.norm(z['net'])!=L.norm(newcore['net']):
   clear=max(float(z['clearance_mm']),domain_gap(z['net'],newcore['net']))+.025+.0001;mask=Z.bounded_buffer(newcore['shape'],clear);mask_zero=set_precision(mask,0);assert mask_zero.wkb==mask.wkb;mf=O/(uid+'-new-CORE-body-filled-cut.wkb');mf.write_bytes(mask.wkb);primitive.append({'new_UUID':newcore['uuid'],'kind':'new_CORE_body_foreign_actual_filled_cut','clearance_with_guard_mm':clear,'cut_WKB_file':str(mf),'cut_WKB_sha256':C.sha(mask.wkb),'shape':mask_zero})
  cut=unary_union([cut,*[r['shape']for r in primitive]]);pieces=L.poly(before_records);"""
t=t.replace(anchor,replacement)
anchor="'exact_role_withdrawal_WKB_sha256':C.sha(wr0),"
assert t.count(anchor)==1
t=t.replace(anchor,anchor+"'exact_NEW_primitive_owned_fill_cuts':[{k:v for k,v in row.items()if k!='shape'}for row in primitive],")
dst.write_text(t);compile(t,str(dst),'exec')
print(hashlib.sha256(dst.read_bytes()).hexdigest())
