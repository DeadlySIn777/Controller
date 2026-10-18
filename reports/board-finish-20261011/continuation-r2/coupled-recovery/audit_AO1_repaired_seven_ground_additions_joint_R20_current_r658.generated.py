"""Independent true Cu/drill/rule/SOURCE audit of seven additive GROUND tracks.

Read-only R20 audit context; no whole-board overlay. Every existing material
record and all physical holes stay exact, only the seven named tracks are added.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
OUT=H/'AO1-R656-seven-GROUND-additions-joint-R20-independent-source-geometry-r658';COM='/motherboard_analog_output/AO1_COM'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def axis(t):return Point(t['x'],t['y'])if'd'in t else LineString([t['a'],t['b']])
def radius(t):return t['d']/2 if'd'in t else t['w']/2
def inf(s):return{'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 rp=pin(H/'AO1-MON3-VREF-b177-5V-source-complete-independent-host-audit-r20/receipt.json','8e1213a3a723bf7fd9c006183b9ba90d11e70420ea46bde4e0c268375fda8b58');parent=json.loads(rp.read_bytes());mp=pin(parent['host_model_file'],'3605d85bb9c672bb2d8dc58b3a6d2c01b01c2e3412978c9941846ee5ad415b72');before=pickle.loads(mp.read_bytes());gp=pin(mp.parent/'AO1-and-local-antipad-all-drilled-after-groups.pkl','4587bd3d6b32ba0cfac8f4c1dfcddd193184ef0bb8049ddac85419a9a9f191de');bg=pickle.loads(gp.read_bytes());sp=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');identity=K.A.N.SourceNets(sp.read_bytes());iv=K.C.inventory(sp.read_bytes())[3];tracks=[];chunks={}
 for rel,s in[('AO1-COM-seven-only-NEW-ground-tracks-local-inside-margin-repair-and-widths-r656/only-seven-NEW-COM-ground-tracks-inside-margin-repaired-widths-NOMINEE.pkl','cb36851a8df37c5e197cea6c8a4de7720ed7e8ec19543ba9a03a5c3b17f1b1b3')]:
  p=pin(H/rel,s);packet=pickle.loads(p.read_bytes());assert not packet['vias']and not packet['original_deletes'];tracks+=packet['tracks'];chunks.update(packet['exact_new_chunks'])
 assert len(tracks)==len(chunks)==7;identity.assert_chunks(chunks);assert set(chunks).isdisjoint(iv);assert set(chunks).isdisjoint({t['uuid']for t in before['tracks']})
 for t in tracks:
  p=K.A.G.parse(t['uuid'],chunks[t['uuid']],{});assert(p['net'],p['layer'],p['a'],p['b'],p['w'])==(COM,t['layer'],t['a'],t['b'],t['w']);assert t['w']in(.20,.30,.50)
 after={**before,'tracks':before['tracks']+tracks};assert all(after[k]is before[k]for k in before if k!='tracks');context=K.hole_context(after);rec,trees=K.F.build({**after,'zones':[]});dom=before['domains_normalized'];gap=lambda n:.15 if dom[K.L.norm(n)]==dom[COM]else .6;checks=[];errors=[];widths=[];holes=[]
 for v in after['vias']:holes.append((v['uuid'],K.L.norm(v['net']),False,Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)))
 for p in after['pads']:
  for sh in K.L.poly(p.get('hole')or[]):holes.append((p['uuid'],K.L.norm(p['net']),p['npth'],sh))
 ht=STRtree([r[3]for r in holes]);reserve,exempt=K.A.reservations();outline=unary_union(K.L.poly(after['outline']));latefile=pin(ROOT/'field-power/R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665/only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl');late=pickle.loads(latefile.read_bytes());fillrows=[]
 for z in after['zones']:
  if K.L.norm(z['net'])==COM:continue
  for ly,rs in z['fills'].items():fillrows.extend({'UUID':z['uuid'],'net':z['net'],'layer':ly,'local':float(z['clearance_mm']),'shape':sh,'kind':'R20_prospective_foreign_fill_HARD'}for sh in K.L.poly(rs))
 for z in late:
  if K.L.norm(z['net'])==COM:continue
  for role in('shape','zone_outline_shape'):fillrows.append({'UUID':z['uuid'],'net':z['net'],'layer':z['layer'],'local':float(z['clearance_mm']),'shape':z[role],'kind':'R665_held_peer_'+role})
 def check(row,ok):
  checks.append(row)
  if not ok:errors.append(row)
 for t in tracks:
  ax=axis(t);ly=t['layer'];rad=t['w']/2;body=K.Z.bounded_buffer(ax,rad);limits=[]
  for i in trees[ly].query(body.buffer(1),predicate='intersects'):
   q=rec[ly][int(i)]
   if q['uuid']==t['uuid']or K.L.norm(q['net'])==COM:continue
   if q['kind']in('track','via'):d=ax.distance(axis(q['source']))-radius(q['source']);inside=0.
   else:d=ax.distance(q['shape']);inside=.005 if q['kind']=='pad'else 0.
   req=gap(q['net'])+.025+inside;truegap=d-rad;check({'kind':'analytic_true_Cu','UUID':t['uuid'],'other_UUID':q['uuid'],'other_net':q['net'],'layer':ly,'true_gap_mm':truegap,'required_with_planner_and_native_inside_bound_mm':req},truegap>=req);limits.append((d-req,q['uuid'],'Cu'))
  for i in ht.query(body.buffer(1),predicate='intersects'):
   uid,n,np,sh=holes[int(i)]
   if not np and n==COM:continue # actual same-net plated annular connection; body is physically drilled below
   d=ax.distance(sh);truegap=d-rad;check({'kind':'all_foreign_or_NPTH_drill','UUID':t['uuid'],'other_UUID':uid,'true_gap_mm':truegap,'required_mm':.275},truegap>=.275);limits.append((d-.275,uid,'drill'))
  for q in fillrows:
   if q['layer']!=ly or q['shape'].envelope.disjoint(body.buffer(1).envelope):continue
   d=ax.distance(q['shape']);req=max(q['local'],gap(q['net']))+.025;truegap=d-rad;check({'kind':q['kind'],'UUID':t['uuid'],'other_UUID':q['UUID'],'other_net':q['net'],'true_gap_mm':truegap,'required_mm':req},truegap>=req);limits.append((d-req,q['UUID'],'fill'))
  check({'kind':'outline','UUID':t['uuid']},outline.buffer(-.025).covers(body))
  for rule in after['rule_areas']:
   if ly in rule['layers']and rule.get('no_tracks'):
    for sh in K.L.poly(rule['outline']):
     d=ax.distance(sh);check({'kind':'native_rule','UUID':t['uuid'],'rule_UUID':rule['uuid'],'gap_mm':d-rad,'required_mm':.025},d-rad>=.025);limits.append((d-.025,rule['uuid'],'rule'))
  for rule in reserve['keepouts']:
   if ly in rule['layers']and COM not in exempt.get(rule['name'],set()):
    for sh in K.L.poly(rule['outline']):
     d=ax.distance(sh);check({'kind':'reserved_barrier','UUID':t['uuid'],'rule':rule['name'],'gap_mm':d-rad,'required_mm':.025},d-rad>=.025);limits.append((d-.025,rule['name'],'barrier'))
  limit=min(limits,key=lambda r:r[0])if limits else(float('inf'),None,None);headroom=2*limit[0];candidates=[w for w in(.20,.25,.30,.40,.50,.60,.80,1.)if w<=headroom-.000002];widths.append({'UUID':t['uuid'],'layer':ly,'length_mm':ax.length,'current_width_mm':t['w'],'analytic_guarded_max_width_mm':headroom,'limiting_item':limit[1],'limiting_kind':limit[2],'discrete_width_choices_with_2nm_margin':candidates,'suggested_width_mm':max(candidates)if candidates else .20})
 ng=K.physical(after,COM,context)[1];groupchecks,groupbad=K.contact_losses(bg[COM],ng);oldroot=K.root(bg[COM],'U14619','7');newroot=K.root(ng,'U14619','7');sourcebad=sorted(K.keys(oldroot)-K.keys(newroot));direct=[]
 for group in bg[COM]:
  for r in group:
   if r['kind']=='fill':continue
   if not any(q['kind']=='fill'and q['layer']==r['layer']and r['shape'].distance(q['shape'])<=.000002 for q in group):continue
   choices=[g for g in ng if any(q['kind']==r['kind']and q['uuid']==r['uuid']and q['layer']==r['layer']for q in g)]
   if not any(any(q['kind']=='fill'and q['layer']==r['layer']and r['shape'].distance(q['shape'])<=.000002 for q in g)for g in choices):direct.append({'UUID':r['uuid'],'kind':r['kind'],'layer':r['layer']})
 oldref=K.source_refs(oldroot);newref=K.source_refs(newroot);deltas={ly:oldref[ly].difference(newref[ly])for ly in oldref};refrows=[];refbad=[]
 for t in before['tracks']:
  if K.L.norm(t['net'])==COM or t['layer']not in deltas or dom.get(K.L.norm(t['net']))!=dom[COM]:continue
  loss=K.L.body(t).intersection(deltas[t['layer']]);row={'UUID':t['uuid'],'net':t['net'],'layer':t['layer'],'literal_old_SOURCE_body_loss':inf(loss)};refrows.append(row)
  if not loss.is_empty:refbad.append(row)
 rootkeys=K.keys(newroot);newsourcebad=[t['uuid']for t in tracks if('track',t['uuid'],t['layer'])not in rootkeys];targetbad=[uid for uid in('013f67e9-bc46-4e7d-8c0e-0cf4e9cf6e4b','53ea5aa5-a009-4367-accd-c5b6de94f6fd')if not any(r['kind']=='pad'and r['uuid']==uid for r in newroot)]
 outputs={'all-true-new-Cu-drill-fill-and-rule-checks.json':checks,'raw-new-geometry-errors.json':errors,'exact-axis-width-headroom-and-conditional-widening.json':widths,'all-old-COM-group-contact-checks.json':groupchecks,'raw-old-COM-group-losses.json':groupbad,'raw-old-COM-SOURCE-key-losses.json':[list(k)for k in sourcebad],'raw-old-direct-COM-fill-contact-losses.json':direct,'all-old-retained-COM-domain-SOURCE-body-reference-checks.json':refrows,'raw-old-retained-SOURCE-body-losses.json':refbad}
 for name,data in outputs.items():(OUT/name).write_text(json.dumps(data,indent=1,allow_nan=False)+'\n')
 model=OUT/'R20-plus-only-seven-ground-tracks-prospective-source-audit-context.pkl';model.write_bytes(pickle.dumps(after,protocol=5));gf=OUT/'actual-before-R20-and-prospective-ground-added-COM-groups.pkl';gf.write_bytes(pickle.dumps({'before':bg[COM],'after':ng},protocol=5));passed=not(errors or groupbad or sourcebad or direct or refbad or newsourcebad or targetbad)
 for p,s in pins.items():assert sha(p)==s,p
 result={'verdict':'SEVEN_ADDITIVE_GROUND_TRACKS_TRUE_GEOMETRY_SOURCE_CONTACT_OLDREF_SCOPED_PASS_NATIVE_CURRENT_SI_OPEN'if passed else'SEVEN_ADDITIVE_GROUND_TRACKS_RAW_SCOPE_REPAIR_REQUIRED','input_SHA256':pins,'new_ground_tracks':7,'new_ground_holes':0,'old_material_and_all_holes_exact_identity_retained':True,'geometry_errors':len(errors),'all_old_COM_group_losses':len(groupbad),'old_COM_SOURCE_keys_lost':len(sourcebad),'old_direct_COM_fill_contacts_lost':len(direct),'strict_literal_old_SOURCE_body_losses':len(refbad),'new_ground_tracks_not_SOURCE':newsourcebad,'required_real_target_ground_members_not_SOURCE':targetbad,'source_keys_before_R20':len(K.keys(oldroot)),'source_keys_after_ground_additions':len(rootkeys),'COM_pad_islands_before':sum(any(r['kind']=='pad'for r in g)for g in bg[COM]),'COM_pad_islands_after':sum(any(r['kind']=='pad'for r in g)for g in ng),'widening_applied_only_on_individually_guarded_NEW_tracks':True,'after_context_file':str(model.resolve()),'after_context_SHA256':sha(model),'COM_groups_SHA256':sha(gf),'native_AFTER_current_load_voltage_closed_loops_SI_thermal':'OPEN','parent_R20_raw_and_native_current_gates_held':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st};(OUT/'receipt.json').write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print('R658_COMPLETE',sha(OUT/'receipt.json'),result['verdict'],'errors',len(errors),'oldrefs',len(refbad),'source',len(rootkeys),flush=True)
if __name__=='__main__':main()
