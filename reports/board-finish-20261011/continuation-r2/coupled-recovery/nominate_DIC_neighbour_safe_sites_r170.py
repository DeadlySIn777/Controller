"""New-only DIC transition correction; exact old body-reference masks.

Retains R164/R168 failed witnesses. Nomination cannot waive old reference,
native annuli, contact/source or final latest-head composition obligations.
"""
import sys,json,pickle,time,copy,math
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in (H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import construct_di6_direct_source_escape_r5 as K
import construct_DIC_three_track_coupled_r164 as B
import restore_SAFE_generated_precision_states_r168 as PS
from shapely.geometry import Point,box
from shapely.ops import unary_union
C=A.C;NET=B.NET;GND=B.GND;LAYERS=B.LAYERS

def main():
 started=time.monotonic();out=H/'DIC-neighbour-safe-site-nomination-r170.json';assert not out.exists();A.read(__file__)
 rp=H/'DIC-three-track-coupled-r164.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='cdb152ede9fbb637191668297405e07af5be24f7e984dc23687dd37d5209ca4b';raw=A.read(r['selected']['model_file']);assert C.sha(raw)=='7e11621fb23ee9fdabdbed66ca3edf51841848d231c50f02370305e5fc5e16b5';old=pickle.loads(raw);cur=old['current'];h=copy.deepcopy(cur['h']);removed=set(old['removed_UUIDs']);h['tracks']=[q for q in h['tracks'] if q['uuid'] not in removed]+[q for q in old['new_tracks'] if L.norm(q['net'])!=NET];dom=h['domains_normalized'];win=box(122,87,135,101);records,trees=F.build({**h,'zones':[]});reserve,exempt=A.reservations();root,refs,_=B.refs_for(cur['after'])
 required=[];reference_rows=[]
 for t in cur['after']['tracks']:
  if t['uuid'] in removed or t['layer'] not in ('F.Cu','B.Cu','In3.Cu') or L.norm(t['net'])==GND or dom.get(L.norm(t['net']))!=dom[GND]:continue
  body=L.body(t)
  if body.distance(win)>1:continue
  plane='In1.Cu' if t['layer']=='F.Cu' else 'In4.Cu';actual=body.intersection(refs[plane])
  if actual.is_empty:continue
  required.append(actual);reference_rows.append({'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'old_actual_source_body_reference_WKB_sha256':C.sha(actual.wkb),'required_area_mm2':actual.area})
 required_shape=unary_union(required);print('DIC_R170_EXACT_OLD_REQUIRED_REFERENCE_MASK',len(reference_rows),C.sha(required_shape.wkb),flush=True)
 holes=[];smd=[]
 for v in h['vias']:
  p=Point(v['x'],v['y'])
  if p.distance(win)<2:holes.append(Z.bounded_disk(v,max(.815,v['drill']/2+.380)))
 for p in h['pads']:
  holes.extend(Z.bounded_buffer(q,.380) for q in L.poly(p.get('hole') or []) if q.distance(win)<2)
  if p['smd']:smd.extend(Z.bounded_buffer(q,.380) for layer,ps in p['layers'].items() if layer in('F.Cu','B.Cu') for q in L.poly(ps) if q.distance(win)<2)
 holemask=unary_union(holes+smd);region_ledger=[];regions={}
 for net in (NET,GND):
  region=win.difference(holemask)
  for layer in LAYERS:
   obs=[]
   for i in trees[layer].query(win.buffer(2),predicate='intersects'):
    q=records[layer][int(i)];n=L.norm(q['net'])
    if n!=net:obs.append(Z.bounded_buffer(q['shape'],.25+(.15 if dom.get(n)==dom[net] else .6)+.030))
   for z in cur['zones']:
    n=L.norm(z['net'])
    if z['layer']==layer and n!=net and z['shape'].distance(win)<2:
     # Exact frozen native/header clearance, no fallback profile.
     header=next(q for q in cur['after']['zones'] if q['uuid']==z['uuid']);assert 'clearance_mm' in header
     obs.append(Z.bounded_buffer(z['shape'],.25+max(float(header['clearance_mm']),.15 if dom.get(n)==dom[net] else .6)+.030))
   for z in cur['after']['zones']:
    n=L.norm(z['net'])
    if n==net or dom.get(n)==dom[net]:continue
    obs.extend(Z.bounded_buffer(q,.25+max(float(z['clearance_mm']),.6)+.030) for q in L.poly(z['fills'].get(layer,[])) if q.distance(win)<2)
   for q in h['rule_areas']:
    if layer in q['layers'] and q.get('no_vias'):obs.extend(Z.bounded_buffer(p,.275) for p in L.poly(q['outline']) if p.distance(win)<2)
   for q in reserve['keepouts']:
    if layer in q['layers'] and net not in exempt.get(q['name'],set()):obs.extend(Z.bounded_buffer(p,.275) for p in L.poly(q['outline']) if p.distance(win)<2)
   region=region.difference(unary_union(obs));region_ledger.append({'raw_net':net,'layer':layer,'physical_region_mm2':region.area,'mask_count':len(obs)})
  # Signal cuts LG by .525, return cuts only its .1 actual drill. This
  # is a conservative nomination margin; final exact delta stays separate.
  refmask=Z.bounded_buffer(required_shape,.530 if net==NET else .105);regions[net]=region.difference(refmask);print('DIC_R170_NEIGHBOUR_SAFE_REGION',net,regions[net].area,flush=True)
 nominations=[]
 for kind,marker in (('source',[127.057072,98.292323]),('target',[130.775665,90.219031])):
  local=regions[NET].intersection(Point(marker).buffer(1.2,quad_segs=128));opts=[]
  for s in K.sites(local,marker,64):
   at=[round(v,6) for v in s['at_mm']];pt=Point(at)
   if not local.covers(pt):continue
   returns=regions[GND].intersection(pt.buffer(.98,quad_segs=128).difference(pt.buffer(.825,quad_segs=128)))
   pairs=[]
   for rs in K.sites(returns,marker,16):
    ret=[round(v,6) for v in rs['at_mm']];p=Point(ret)
    if not returns.covers(p):continue
    ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));contacts={l:ann.intersection(sh.buffer(-.075,quad_segs=128)).area for l,sh in refs.items()}
    if all(a>.004 for a in contacts.values()):pairs.append({'return':ret,'distance_mm':math.dist(at,ret),'actual_source_interior_annulus_mm2':contacts})
   if pairs:opts.append({'signal':at,'distance_from_R164_mm':math.dist(at,marker),'pairs':pairs})
  nominations.append({'kind':kind,'local_signal_region_mm2':local.area,'options':opts});print('DIC_R170_NEIGHBOUR_SAFE_OPTIONS',kind,len(opts),flush=True)
 # Exact accepted IO3 successor mutual screen, including outward antipads.
 io=H.parent/'sbc-power/IO3-wider-minimal-validated-integration-packet-r201/receipt.json';ir=json.loads(A.read(io));assert C.sha(A.read(io))=='cee3eacedd73ba63788decafd0a3b169afee6a0fbfa76f76e5acc60e8cc83e2d';ib=A.read(ir['replacement_objects_file']);assert C.sha(ib)=='ff59c9d7f91230a57ea11f1c4b98832cf3eb2601306f57ed8da6086e8f89282d';packet=pickle.loads(ib);fr=A.read(ir['frozen_full_model_file']);assert C.sha(fr)=='bf5603eebd87b3c5c197b8ae1266c0c0e780c3628dc65adbaa6b7f94f31721af';fg,fh,fb,fq,fa=pickle.loads(fr);precision=PS.restore_bound_generated_precision_states(fb,fq);canonical={q['uuid']:q for q in fq};keys=('net','layer','clearance_mm','min_thickness_mm','pad_connect_mode','priority','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm');assert len(packet)==1;z=canonical[packet[0]['uuid']];assert all(packet[0][k]==z[k] for k in keys) and all(packet[0][role].wkb==z[role].wkb for role in('shape','zone_outline_shape'));mutual=[]
 for v in old['new_vias']:
  for role in ('shape','zone_outline_shape'):
   body=Z.bounded_disk(v,v['d']/2);drill=Z.bounded_disk(v,v['drill']/2);cut=Z.bounded_disk(v,v['d']/2+float(z['clearance_mm'])+.025);mutual.append({'original_R164_via_UUID':v['uuid'],'IO3_UUID':z['uuid'],'role':role,'WKB_sha256':C.sha(z[role].wkb),'body_distance_mm':body.distance(z[role]),'drill_intersection_mm2':drill.intersection(z[role]).area,'outward_antipad_radius_mm':.425,'outward_antipad_intersection_mm2':cut.intersection(z[role]).area})
 model=H/'DIC-neighbour-safe-site-nomination-r170-model.pkl';assert not model.exists();model.write_bytes(pickle.dumps({'current':cur,'h_without_owned3_with_R164_CS_RSP':h,'regions':regions,'required_ref_shape':required_shape,'required_ref_rows':reference_rows,'nominations':nominations,'latest_IO3_canonical':z},protocol=5));result={'verdict':'DIC_NEW_ONLY_NEIGHBOUR_SAFE_SITE_NOMINATION_OPEN' if all(q['options'] for q in nominations) else'DIC_NEW_ONLY_NEIGHBOUR_SAFE_SITE_NOMINATION_INCOMPLETE','R164_preserved_receipt_sha256':C.sha(A.read(rp)),'R168_strict_failure_preserved_sha256':C.sha(A.read(H/'DIC-three-track-independent-r168.json')),'exact_old_required_reference_rows':reference_rows,'region_ledger':region_ledger,'nominations':nominations,'R201_receipt_sha256':C.sha(A.read(io)),'latest_IO3_original_R164_all4_via_physical_intended_drill_outward_antipad_screen':mutual,'latest_IO3_nine_direct_settings':{k:z[k] for k in keys},'precision_restore_roles':precision,'model_file':str(model),'model_sha256':C.sha(model.read_bytes()),'full_candidate_old_new_contact_reference_source_current_native_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':result['verdict'],'options':[len(q['options']) for q in nominations],'IO3_outward_antipad_intersections_mm2':[q['outward_antipad_intersection_mm2'] for q in mutual]}),flush=True)
if __name__=='__main__':main()
