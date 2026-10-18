"""Fresh exact CMD return locus with only four owned tracks withdrawn.

Original CMD barrel/annuli/flags are unchanged; new ordinary return must
retain every foreign body, SMD/hole margin, source annulus and neighbour ref.
"""
import sys,json,pickle,time,copy,math
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import construct_di6_direct_source_escape_r5 as K
import construct_DIC_three_track_coupled_r164 as B
from shapely.geometry import Point,box
from shapely.ops import unary_union
C=A.C;GND=B.GND;NET=B.NET;CMD='/motherboard_io_control/DIC_IOL1_CMD_BUFFER';LAYERS=B.LAYERS
def main():
 started=time.monotonic();out=H/'DIC-CMD-fresh-ordinary-return-r184.json';assert not out.exists();A.read(__file__);rp=H/'DIC-three-track-coupled-r164.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='cdb152ede9fbb637191668297405e07af5be24f7e984dc23687dd37d5209ca4b';raw=A.read(r['selected']['model_file']);assert C.sha(raw)=='7e11621fb23ee9fdabdbed66ca3edf51841848d231c50f02370305e5fc5e16b5';old=pickle.loads(raw);cur=old['current'];h=copy.deepcopy(cur['h']);removed=set(old['removed_UUIDs'])|{'811a28fc-3124-4526-b8b8-287522e6a219'};h['tracks']=[q for q in h['tracks'] if q['uuid'] not in removed]+[q for q in old['new_tracks'] if L.norm(q['net'])!=NET];nv=copy.deepcopy(old['new_vias']);target=next(v for v in nv if v['uuid']=='a16e89d4-e503-59a2-9eb7-8715bf92019b');target['x'],target['y']=130.782294,90.235607;ret=next(v for v in nv if v['uuid']=='25e42288-ebe1-51a1-8e07-26f429e1d46f');ret['x'],ret['y']=130.951774,91.046517
 # These virtual position rows are nomination only; serialization will create
 # fresh UUIDs in the concrete candidate. No stale UUID/pose is emitted.
 h['vias']+=nv;dom=h['domains_normalized'];signal=next(v for v in h['vias'] if v['uuid']=='1f815e33-e973-46e2-833e-96fee8d37fcf');assert(signal['x'],signal['y'],signal['d'],signal['drill'])==(128.549999,100.55,.6,.3);point=Point(signal['x'],signal['y']);win=point.buffer(1.05,quad_segs=128).envelope;records,trees=F.build({**h,'zones':[]});reserve,exempt=A.reservations();region=win;ledger=[]
 for layer in LAYERS:
  obs=[]
  for i in trees[layer].query(win.buffer(2),predicate='intersects'):
   q=records[layer][int(i)];n=L.norm(q['net'])
   if n!=GND:obs.append(Z.bounded_buffer(q['shape'],.25+(.15 if dom.get(n)==dom[GND] else .6)+.030))
  for z in cur['zones']:
   n=L.norm(z['net'])
   if z['layer']!=layer or n==GND or z['shape'].distance(win)>2:continue
   head=next(q for q in cur['after']['zones'] if q['uuid']==z['uuid']);assert 'clearance_mm' in head;obs.append(Z.bounded_buffer(z['shape'],.25+max(float(head['clearance_mm']),.15 if dom.get(n)==dom[GND] else .6)+.030))
  for z in cur['after']['zones']:
   n=L.norm(z['net'])
   if n==GND or dom.get(n)==dom[GND]:continue
   obs.extend(Z.bounded_buffer(p,.25+max(float(z['clearance_mm']),.6)+.030) for p in L.poly(z['fills'].get(layer,[])) if p.distance(win)<2)
  for q in h['rule_areas']:
   if layer in q['layers'] and q.get('no_vias'):obs.extend(Z.bounded_buffer(p,.275) for p in L.poly(q['outline']) if p.distance(win)<2)
  for q in reserve['keepouts']:
   if layer in q['layers'] and GND not in exempt.get(q['name'],set()):obs.extend(Z.bounded_buffer(p,.275) for p in L.poly(q['outline']) if p.distance(win)<2)
  region=region.difference(unary_union(obs));ledger.append({'layer':layer,'obstacle_count':len(obs),'remaining_mm2':region.area})
 holes=[]
 for v in h['vias']:
  if Point(v['x'],v['y']).distance(win)<2:holes.append(Z.bounded_disk(v,max(.815,v['drill']/2+.380)))
 for p in h['pads']:
  holes.extend(Z.bounded_buffer(q,.380) for q in L.poly(p.get('hole') or []) if q.distance(win)<2)
  if p['smd']:holes.extend(Z.bounded_buffer(q,.380) for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for q in L.poly(rs) if q.distance(win)<2)
 region=region.difference(unary_union(holes));root,refs,_=B.refs_for(cur['after']);required=[]
 for t in cur['after']['tracks']:
  if t['uuid'] in removed or t['layer'] not in('F.Cu','B.Cu','In3.Cu') or L.norm(t['net'])==GND or dom.get(L.norm(t['net']))!=dom[GND]:continue
  body=L.body(t)
  if body.distance(win)>1:continue
  required.append(body.intersection(refs['In1.Cu' if t['layer']=='F.Cu' else'In4.Cu']))
 region=region.difference(Z.bounded_buffer(unary_union(required),.105));region=region.intersection(point.buffer(.98,quad_segs=128).difference(point.buffer(.820,quad_segs=128)));pre,_=B.project(cur,h,[],nv);root,finalrefs,_=B.refs_for(pre);insets={l:sh.buffer(-.075,quad_segs=128) for l,sh in finalrefs.items()};options=[]
 for s in K.sites(region,[signal['x'],signal['y']],64):
  at=[round(x,6) for x in s['at_mm']];p=Point(at)
  if not region.covers(p):continue
  ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));contacts={l:ann.intersection(sh).area for l,sh in insets.items()}
  if all(a>.004 for a in contacts.values()):options.append({'return_at_mm':at,'actual_signal_distance_mm':point.distance(p),'actual_after_four_DIC_holes_source_interior_annulus_mm2':contacts,'ordinary_diameter_drill_mm':[.5,.2]})
 model=H/'DIC-CMD-fresh-ordinary-return-r184-model.pkl';assert not model.exists();model.write_bytes(pickle.dumps({'current':cur,'h_nomination_virtual_only':h,'region':region,'signal':signal,'options':options,'source_refs_after_DIC_four_holes':finalrefs,'removed_UUIDs':removed},protocol=5));result={'verdict':'DIC_CMD_EXACT_FRESH_ORDINARY_RETURN_POSITIVE_CONSTRUCTION_OPEN' if options else'DIC_CMD_EXACT_FRESH_ORDINARY_RETURN_EMPTY_INCOMPLETE','source_parent_sha256':r['source_parent_sha256'],'R164_receipt_sha256':C.sha(A.read(rp)),'removed_only_four_original_track_UUIDs':sorted(removed),'actual_retained_signal_UUID':signal['uuid'],'actual_retained_signal_at_mm':[signal['x'],signal['y']],'unchanged_exact_signal_own_radius_mm':.575,'radius_expansion_mm':0,'actual_six_layer_physical_mask_ledger':ledger,'final_ordinary_current_neighbour_safe_return_region_mm2':region.area,'new_return_options':options,'nomination_virtual_changed_UUID_positions_never_serialized':True,'model_file':str(model),'model_sha256':C.sha(model.read_bytes()),'full_after_actual_five_vias_source_contacts_native_reference_current_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':result['verdict'],'options':len(options),'region_mm2':region.area}),flush=True)
if __name__=='__main__':main()
