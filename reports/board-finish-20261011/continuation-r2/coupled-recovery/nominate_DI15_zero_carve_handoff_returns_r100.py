"""Nominate real ordinary source returns for only the needed In3 islands.

Saved guarded R38 ordinary geometry is nomination authority only. Exact
current model/drills/source/groups/body coverage are rebuilt for the chosen
operation; final independent all-contact/current/native gates remain open.
"""
import sys,json,pickle,time,math,copy,itertools
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE.parent/'sbc-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import construct_di6_direct_source_escape_r5 as K
import audit_c10036_r24_full_independent_r30 as Q
import audit_ao1_positive_operation_r4 as SERIAL
import complete_geometry_r2 as GE
import guarded_power_projection_r44 as Z
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
C=A.C;GND='/LOGIC_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def main():
 started=time.monotonic();out=HERE/'DI15-zero-carve-handoff-return-nomination-r100.json';assert not out.exists();A.read(__file__);rp=HERE/'di15-zero-power-carve-reference-pieces-r94/receipt.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='271c9f168df53b0fa35150cc40575aceea3ce528b1adce40bca9ec2b3e7c6e3f';raw=A.read(r['source_only_model_file']);assert C.sha(raw)==r['source_only_model_sha256'];saved=pickle.loads(raw);cur=saved['current'];h=cur['h'];before=cur['after'];source=A.read(cur['binding']['exact_native_discrete_board_file']);identity=A.N.SourceNets(source);inventory=C.inventory(source);body=saved['body'];line=LineString(saved['points']);needed=body.difference(cur['source_planes']['In1.Cu']);chosen=[z for z in saved['new_zones'] if z['layer']=='In3.Cu' and not z['shape'].intersection(needed).is_empty];discarded=[z['uuid'] for z in saved['new_zones'] if z not in chosen];oldplanes={l:cur['source_planes'][l] for l in('In1.Cu','In4.Cu')}
 raw38=A.read(HERE/'di15-r38-local-site-checkpoint.pkl');assert C.sha(raw38)=='7f454fd9404c280a61c12eed5be338b41bacd04be58a27223e35baa17645d18c';local=pickle.loads(raw38);via=local['via'][GND];zones=[];ledger=[];allopts=[]
 for z in chosen:
  region=z['shape'].buffer(-.005,quad_segs=128).intersection(via);target=z['shape'].intersection(needed);rows=[]
  preferred=[list(target.centroid.coords)[0],*saved['points'][7:10]]
  seen=set()
  for p in preferred:
   for option in K.sites(region,p,16):
    at=option['at_mm']
    if tuple(at) in seen:continue
    seen.add(tuple(at));pt=Point(at);ann=pt.buffer(.25,quad_segs=128).difference(pt.buffer(.1,quad_segs=128));areas={l:ann.intersection(sh).area for l,sh in oldplanes.items()};area3=ann.intersection(z['shape']).area
    if not all(x>.004 for x in areas.values()) or area3<=.004:continue
    rows.append({'at_mm':at,'finite_prior_J1_plane_contact_mm2':areas,'finite_new_In3_piece_annular_contact_mm2':area3,'distance_to_saved_signal_mm':pt.distance(line),'minimum_required_old_via_pitch_mm':min(math.dist(at,[v['x'],v['y']]) for v in h['vias']),'expected_new_return_diameter_drill_mm':[.5,.2]})
  ledger.append({'piece_UUID':z['uuid'],'piece_area_mm2':z['shape'].area,'required_DI15_body_overlap_mm2':target.area,'saved_ordinary_guarded_nomination_region_mm2':region.area,'real_finite_source_return_options':rows});allopts.append(rows);zones.append(z)
 print('DI15_REQUIRED_IN3_RETURN_REGIONS',json.dumps(ledger),flush=True);selected=None;attempts=[]
 # Nominate up to two returns per required island, then exact source/body
 # graph. A single return can root a piece but cannot qualify both handoffs.
 options=[]
 for rows in allopts:
  candidates=[]
  for q in rows[:12]:candidates.append([q])
  for a,b in itertools.combinations(rows[:16],2):
   if math.dist(a['at_mm'],b['at_mm'])>=.81:candidates.append([a,b])
  options.append(candidates[:64])
 if options and all(options):
  for combination in itertools.islice(itertools.product(*options),64):
   returns=[q for rr in combination for q in rr]
   if any(math.dist(a['at_mm'],b['at_mm'])<.81 for a,b in itertools.combinations(returns,2)):continue
   nv=[];chunks={}
   for q in returns:
    u,ch=SERIAL.serial_via(identity,GND,q['at_mm']);assert u not in inventory[3] and u not in {v['uuid'] for v in h['vias']};chunks[u]=ch;nv.append({'uuid':u,'net':identity.raw(GND),'x':q['at_mm'][0],'y':q['at_mm'][1],'d':.5,'drill':.2,'flashed':LAYERS})
   fills=[]
   for z in before['zones']:
    net=L.norm(z['net']);nz={**z,'fills':{}}
    for layer,rs in z['fills'].items():
     shape=unary_union(L.poly(rs));cuts=[]
     for v in nv:
      if net==GND:radius=.1
      else:radius=max(.375,.25+max(float(z.get('clearance_mm',.15)),.15 if h['domains_normalized'].get(net)==h['domains_normalized'][GND] else .6)+.025)
      cut=Z.bounded_disk(v,radius)
      if cut.intersects(shape):cuts.append(cut)
     nz['fills'][layer]=GE.records(shape.difference(unary_union(cuts)))
    fills.append(nz)
   for z in zones:fills.append({'uuid':z['uuid'],'net':GND,'clearance_mm':.25,'priority':124,'fills':{z['layer']:GE.records(z['shape'])}})
   after={**before,'vias':h['vias']+nv,'zones':fills};_,groups=Q.physical(after,GND);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],str(q['pin']))==('J11001','2') for q in xs));refs={layer:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==layer]) for layer in('In1.Cu','In3.Cu')};uniongap=body.difference(unary_union(list(refs.values())));lost=sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root));piece_roots={z['uuid']:any(q['kind']=='fill' and q['uuid']==z['uuid'] for q in root) for z in zones};row={'returns':returns,'new_vias':nv,'actual_DI15_source_union_gap_mm2_nomination_only':uniongap.area,'old_LG_source_key_losses':lost,'actual_selected_piece_roots':piece_roots};attempts.append(row)
   if uniongap.is_empty and not lost and all(piece_roots.values()):
    identity.assert_chunks(chunks);cp=HERE/'DI15-zero-carve-handoff-source-r100-model.pkl';assert not cp.exists();cp.write_bytes(pickle.dumps({'current':cur,'after':after,'zones':cur['zones']+zones,'new_zones':zones,'new_vias':nv,'exact_new_chunks':chunks,'refs':refs,'root':root,'groups':groups,'body':body,'points':saved['points']},protocol=5));selected={**row,'exact_new_chunks':{u:b.decode() for u,b in chunks.items()},'saved_model_file':str(cp),'saved_model_sha256':C.sha(cp.read_bytes())};break
   # Do not repeat expensive full source graph for another single site when
   # failure is physical body coverage; preserve exact diagnosis.
   if not uniongap.is_empty:break
 report={'verdict':'DI15_EXACT_ZERO_CARVE_SOURCE_RETURN_OPERATION_NOMINATED_HANDOFF_QUALIFICATION_OPEN' if selected else'DI15_ZERO_CARVE_REQUIRED_ISLAND_SOURCE_RETURN_NOMINATION_INCOMPLETE','R94_receipt_sha256':C.sha(A.read(rp)),'current_exact_model_sha256':r['source_model_sha256'],'source_parent_sha256':C.sha(source),'saved_R38_nomination_masks_sha256':C.sha(raw38),'required_In3_piece_ledger':ledger,'unused_R94_zone_UUIDs_withdrawn_only_from_proposal':discarded,'attempts':attempts,'selected':selected,'original_and_proposed_power_planes_released':[],'native_jobs':0,'board_written':False,'adopted':False,'reference_union_is_nomination_only':True,'required_remaining':'Concrete handoff sites with finite actual In1/In3 source annuli within1mm of each reference transition, exact full-body assignment after all new signal/return drill cuts, all current/r06/r07/contact/neighbour/current/native/SI','read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'selected':selected,'piece_ledger':ledger}),flush=True)
if __name__=='__main__':main()
