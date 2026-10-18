"""Exact target component/site and real new source-return nomination."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'nominate_Q0_FLT_owned_alternative_ports_r362.py';s=base.read_text(encoding='utf-8').split('fr=ffree();polys=')[0].replace('Q0-FLT-owned-alternative-source-port-nomination-r362','Q0-FLT-alternative-general-source-ports-r364')
# The nested R350 prefix defines the original output stem before R356 applies
# its replacement; bind this new stem directly in that replacement argument.
s=s.replace("'Q0-FLT-owned-alternative-source-port-nomination-r362'","'Q0-FLT-alternative-general-source-ports-r364'")
exec(compile(s,str(base),'exec'))
fr=ffree();polys=K.RF.parts(fr);target=signalF.buffer(-.04,quad_segs=128);rows=[];sitesout=[]
for ci,part in enumerate(polys):
 if part.intersection(target).is_empty:continue
 pp=part.intersection(viaparts);pieces=K.RF.parts(pp);row={'source_F_component':ci,'source_attachment_mm2':part.intersection(target).area,'rule_legal_ordinary_signal_port_area_mm2':pp.area,'fragment_count':len(pieces),'bounds':pp.bounds if not pp.is_empty else None};rows.append(row);(out/('source-F-component-'+str(ci)+'.wkb')).write_bytes(part.wkb);(out/('source-all6-rule-legal-centres-'+str(ci)+'.wkb')).write_bytes(pp.wkb)
 for piece in pieces:
  if piece.area<.000001:continue
  candidates=[piece.representative_point(),piece.centroid]
  for p in candidates:
   at=[round(p.x,6),round(p.y,6)];p=Point(at)
   if not piece.covers(p):continue
   caps={l:K.Z.bounded_disk({'x':at[0],'y':at[1]},.255).difference(oldrefs[l])for l in oldrefs};sitesout.append({'signal_xy_mm':at,'component':ci,'before_actual_source_cap_gap_mm2':{l:z.area for l,z in caps.items()},'before_actual_source_full_cap_empty':{l:z.is_empty for l,z in caps.items()},'nearest_existing_rooted_return_mm':min((p.distance(Point(v['x'],v['y'])),v['uuid'])for v,pp in eligible)})
put(out/'source-general-ordinary-site-nominations.json',sitesout)
result={'verdict':'EXACT_TARGET_COMPONENT_DIAGNOSIS_ONLY','model_sha256':sha(model),'operator_sha256':sha(operator),'source_components':rows,'general_source_site_count':len(sitesout),'all_source_reference_transport_after_holes_native_current':'OPEN','board_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps(result),flush=True)

