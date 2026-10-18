"""Intersect exact continuous endpoint regions before choosing a PEN site.

Frozen R86 masks and actual current source contacts are retained. A positive
nominee has one new ordinary B/In3 via, at most one new real GND return,
two layer segments, zero old-copper removals and exact raw source chunks.
Full projected model/current/reference/contact/native proof is separate.
"""
import sys,json,pickle,time,math
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import construct_di6_direct_source_escape_r5 as K
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
C=A.C;NET='/motherboard_process/PEN_ENABLE_LOGIC';GND='/LOGIC_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def main():
 started=time.monotonic();out=HERE/'PEN-continuous-existing-In3-one-dive-nomination-r92.json';assert not out.exists();A.read(__file__);rp=HERE/'PEN-existing-In3-or-B-dive-nomination-r86.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='ea26ecb5e73f793503f64448640cb894eeab8096ef7a56dd1a94499495f30f9a';raw=A.read(r['saved_model']);assert C.sha(raw)==r['saved_model_sha256'];cache=pickle.loads(raw);free=cache['free'];via=cache['via'];terms=cache['terms'];planes=cache['refs'];h=cache['current']['h'];source=A.read(cache['current']['binding']['exact_native_discrete_board_file']);identity=A.N.SourceNets(source);inventory=C.inventory(source);existing=cache['existing_returns'];bp=[]
 for p in K.pieces(free['B.Cu']):
  a=terms['B.Cu'][1].buffer(-.05,quad_segs=128).intersection(p)
  if not a.is_empty:bp.append((p,a))
 def pairs(region):
  opts=[]
  for ret in existing:
   c=Point(ret['at_mm']);reg=region.intersection(c.buffer(1,quad_segs=128).difference(c.buffer(max(.815,.25+ret['diameter_mm']/2+.18),quad_segs=128)))
   for s in K.sites(reg,list(terms['B.Cu'][1].centroid.coords)[0],3):opts.append({'signal':s['at_mm'],'return':ret['at_mm'],'return_new':False,'old_return_uuid':ret['uuid'],'finite_existing_rooted_annuli':ret['finite_actual_rooted_annular_contact_mm2']})
  for s in K.sites(region,list(terms['B.Cu'][1].centroid.coords)[0],12):
   c=Point(s['at_mm']);reg=via[GND].intersection(c.buffer(1,quad_segs=128).difference(c.buffer(.825,quad_segs=128)))
   for rr in K.sites(reg,[c.x-.9,c.y],3):
    at=rr['at_mm'];p=Point(at);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));areas={l:ann.intersection(sh).area for l,sh in planes.items()}
    if all(x>.004 for x in areas.values()):opts.append({'signal':s['at_mm'],'return':at,'return_new':True,'old_return_uuid':None,'finite_prospective_rooted_annuli':areas})
  return opts
 rows=[];nominees=[];sourceCu=terms['In3.Cu'][0].buffer(-.05,quad_segs=128)
 for i,p in enumerate(K.pieces(free['In3.Cu'])):
  sourceRegion=sourceCu.intersection(p)
  if sourceRegion.is_empty:continue
  for j,(bpart,battach) in enumerate(bp):
   targetRegion=via[NET].intersection(p).intersection(bpart).intersection(Point(terms['B.Cu'][1].centroid).buffer(5,quad_segs=128));row={'In3_component':i,'B_component':j,'source_actual_In3_contact_mm2':sourceRegion.area,'target_ordinary_via_region_mm2':targetRegion.area};rows.append(row)
   if targetRegion.is_empty:continue
   pp=pairs(targetRegion);row['paired_options']=len(pp)
   for q in pp:
    psrc=nearest_points(sourceRegion,Point(q['signal']))[0];ptgt=nearest_points(battach,Point(q['signal']))[0];nominees.append({'In3_component':i,'B_component':j,'source_contact_at_mm':[round(psrc.x,6),round(psrc.y,6)],'target_B_contact_at_mm':[round(ptgt.x,6),round(ptgt.y,6)],'pair':q,'score_mm':psrc.distance(Point(q['signal']))+ptgt.distance(Point(q['signal']))})
 print('PEN_CONTINUOUS_REGIONS',json.dumps(rows),'NOMINEES',len(nominees),flush=True);attempts=[];selected=None;chunks={};nv=[];nt=[]
 for nom in sorted(nominees,key=lambda q:q['score_mm'])[:12]:
  row={**nom,'paths':[]};attempts.append(row);cut=Point(nom['pair']['return']).buffer(.535,quad_segs=128) if nom['pair']['return_new'] else Point().buffer(0)
  for layer,a,b in[('In3.Cu',nom['source_contact_at_mm'],nom['pair']['signal']),('B.Cu',nom['target_B_contact_at_mm'],nom['pair']['signal'])]:
   parts=[p for p in K.pieces(free[layer].difference(cut)) if p.covers(Point(a)) and p.covers(Point(b))]
   if not parts:row['failed_layer']=layer;break
   pts,search=T.route(parts[0],tuple(a),tuple(b));pts=[[round(x,6),round(y,6)] for x,y in pts]
   if len(pts)<2:row['failed_layer']=layer;break
   body=unary_union([A.shape({'kind':'segment','a':p,'b':q,'w':.2}) for p,q in zip(pts,pts[1:])]);gap=body.difference(planes['In4.Cu']);row['paths'].append({'layer':layer,'points_mm':pts,'length_mm':LineString(pts).length,'width_mm':.2,'full_body_actual_before_In4_source_reference_gap_mm2':gap.area,'search':search})
   if not gap.is_empty:row['failed_reference_layer']=layer;break
  if len(row['paths'])==2 and not row.get('failed_reference_layer'):
   selected=row
   for net,at in[(NET,nom['pair']['signal'])]+([(GND,nom['pair']['return'])] if nom['pair']['return_new'] else []):
    u,ch=SERIAL.serial_via(identity,net,at);assert u not in inventory[3];chunks[u]=ch;nv.append({'uuid':u,'net':identity.raw(net),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':LAYERS})
   for path in row['paths']:
    for a,b in zip(path['points_mm'],path['points_mm'][1:]):u,ch=identity.serial_segment(NET,path['layer'],a,b,.2);assert u not in inventory[3];chunks[u]=ch;nt.append({'uuid':u,'net':identity.raw(NET),'layer':path['layer'],'a':a,'b':b,'w':.2})
   identity.assert_chunks(chunks);break
 report={'verdict':'PEN_CURRENT_ONE_DIVE_EXACT_OPERATION_NOMINATED_INDEPENDENT_OPEN' if selected else'PEN_CONTINUOUS_EXISTING_IN3_ONE_DIVE_BOUNDED_INCOMPLETE','R86_receipt_sha256':C.sha(A.read(rp)),'frozen_local_geometry_sha256':C.sha(raw),'current_model_sha256':r['current_model_sha256'],'source_parent_sha256':C.sha(source),'raw_net':identity.raw(NET),'original_r06_relationship':r['original_r06_relationship'],'exact_current_pad_UUIDs':r['exact_current_pad_UUIDs'],'continuous_component_ledger':rows,'nominees_count':len(nominees),'attempts':attempts,'selected':selected,'new_vias':nv,'new_tracks':nt,'exact_new_chunks':{u:ch.decode() for u,ch in chunks.items()},'exact_deleted_chunks':{},'max_layer_segments':2,'new_signal_transitions':1 if selected else 0,'same_actual_In4_reference_for_B_and_In3':True,'all_new_via_native_annuli_actual_projection_source_current_r06_r07_contact_neighbour_ref_SI_DRC':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'continuous_regions':rows,'selected':selected,'new_vias':nv,'new_tracks':len(nt)}),flush=True)
if __name__=='__main__':main()
