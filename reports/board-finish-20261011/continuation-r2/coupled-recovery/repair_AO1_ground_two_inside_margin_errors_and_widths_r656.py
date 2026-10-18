"""Finite local repair of unadopted R650/R652 ground tracks; no old changes."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
OUT=H/'AO1-COM-seven-only-NEW-ground-tracks-local-inside-margin-repair-and-widths-r656'
COM='/motherboard_analog_output/AO1_COM'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def axis(t):return Point(t['x'],t['y'])if'd'in t else LineString([t['a'],t['b']])
def radius(t):return t['d']/2 if'd'in t else t['w']/2
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(rel,s=None):
  p=H/rel;v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 pin('AO1-R650-R652-eight-GROUND-additions-joint-R20-independent-source-geometry-r654/receipt.json','26d6494156b3268e6a8eda6f3519bfeaf7ce3f682216d49542495c783281bbed')
 mp=pin('AO1-MON3-VREF-b177-5V-source-complete-independent-host-audit-r20/AO1-only-sparse-prospective-normal-native-antipad-host-model.pkl','3605d85bb9c672bb2d8dc58b3a6d2c01b01c2e3412978c9941846ee5ad415b72');before=pickle.loads(mp.read_bytes())
 pp=[pin('AO1-COM-actual-SOURCE-to-U14623-9-B-Cu-finite-ground-bridge-r650/only-NEW-COM-B-Cu-ground-tracks-NOMINEE.pkl','148e8734780eb501c45711b971c785a2a054b2924f6f9c1ee378f0bc931d1f9e'),pin('AO1-COM-actual-SOURCE-to-U14636-3-F-Cu-finite-ground-bridge-r652/only-NEW-COM-F-Cu-ground-tracks-NOMINEE.pkl','95661ff14556f9c45f93231e6c10c34ae9e500e6ea269d90e2b07e0ecbeab5f0')];packs=[pickle.loads(p.read_bytes())for p in pp];bt=packs[0]['tracks'];ft=packs[1]['tracks'];assert len(bt)==6 and len(ft)==2
 rec,trees=K.F.build({**before,'zones':[]});dom=before['domains_normalized'];gap=lambda n:.15 if dom[K.L.norm(n)]==dom[COM]else .6
 holes=[]
 for v in before['vias']:holes.append((v['uuid'],K.L.norm(v['net']),False,Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)))
 for p in before['pads']:
  for sh in K.L.poly(p.get('hole')or[]):holes.append((p['uuid'],K.L.norm(p['net']),p['npth'],sh))
 ht=STRtree([r[3]for r in holes]);reserve,exempt=K.A.reservations();outline=unary_union(K.L.poly(before['outline']));fill=[]
 for z in before['zones']:
  if K.L.norm(z['net'])==COM:continue
  for ly,rs in z['fills'].items():fill.extend((z['uuid'],z['net'],ly,float(z['clearance_mm']),sh,'R20_foreign_fill')for sh in K.L.poly(rs))
 latep=ROOT/'field-power/R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665/only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl';pins[str(latep.resolve())]=sha(latep)
 for z in pickle.loads(latep.read_bytes()):
  if K.L.norm(z['net'])==COM:continue
  for role in('shape','zone_outline_shape'):fill.append((z['uuid'],z['net'],z['layer'],float(z['clearance_mm']),z[role],'R665_held_'+role))
 def errors(t):
  ax=axis(t);rad=t['w']/2;ly=t['layer'];body=K.Z.bounded_buffer(ax,rad);bad=[]
  def test(kind,uid,d,req):
   if d-rad<req:bad.append({'kind':kind,'other_UUID':uid,'true_gap_mm':d-rad,'required_mm':req})
  for i in trees[ly].query(body.buffer(1),predicate='intersects'):
   q=rec[ly][int(i)]
   if K.L.norm(q['net'])==COM:continue
   d=ax.distance(axis(q['source']))-radius(q['source'])if q['kind']in('track','via')else ax.distance(q['shape']);req=gap(q['net'])+.025+(.005 if q['kind']=='pad'else 0);test('analytic_true_Cu',q['uuid'],d,req)
  for i in ht.query(body.buffer(1),predicate='intersects'):
   uid,n,np,sh=holes[int(i)]
   if np or n!=COM:test('all_foreign_or_NPTH_holes',uid,ax.distance(sh),.275)
  for uid,n,ly2,cl,sh,kind in fill:
   if ly2==ly and not sh.envelope.disjoint(body.buffer(1).envelope):test(kind,uid,ax.distance(sh),max(cl,gap(n))+.025)
  if not outline.buffer(-.025).covers(body):bad.append({'kind':'outline'})
  for rule in before['rule_areas']:
   if ly in rule['layers']and rule.get('no_tracks'):
    for sh in K.L.poly(rule['outline']):test('native_rule',rule['uuid'],ax.distance(sh),.025)
  for rule in reserve['keepouts']:
   if ly in rule['layers']and COM not in exempt.get(rule['name'],set()):
    for sh in K.L.poly(rule['outline']):test('reserved_barrier',rule['name'],ax.distance(sh),.025)
  return bad
 pts=[list(bt[0]['a'])]+[list(t['b'])for t in bt];origin=pts[4][:];fixed=[dict(t)for t in bt];fixed[0]['w']=.30;fixed[5]['w']=.50;newf=dict(ft[0]);fixedbad=[{'UUID':t['uuid'],'errors':errors(t)}for t in[fixed[0],fixed[1],fixed[2],fixed[5],newf]if errors(t)];assert not fixedbad,fixedbad
 pad=next(q for q in rec['B.Cu']if q['uuid']=='aacc0bdf-0449-4b0f-95b8-cccb718c4d90');p,q=nearest_points(axis(bt[3]),pad['shape']);attribution={'old_segment_UUID':bt[3]['uuid'],'exact_old_axis_nearest_mm':list(p.coords[0]),'exact_pad_nearest_mm':list(q.coords[0]),'old_true_gap_mm':p.distance(q)-.1,'native_inside_bound_mm':.005}
 attempts=[];selected=None
 offsets=sorted(((dx,dy)for dx in range(-25,26)for dy in range(-25,26)),key=lambda v:(v[0]*v[0]+v[1]*v[1],v))
 for dx,dy in offsets:
  endpoint=[round(origin[0]+dx*.001,6),round(origin[1]+dy*.001,6)];a={**fixed[3],'b':endpoint};b={**fixed[4],'a':endpoint};bad=[{'track_index':j,'errors':errors(t)}for j,t in((3,a),(4,b))if errors(t)];attempts.append({'offset_um':[dx,dy],'errors':bad})
  if not bad:selected={'point4_original_mm':origin,'point4_repaired_mm':endpoint,'offset_um':[dx,dy]};fixed[3]=a;fixed[4]=b;break
 (OUT/'raw-local-proposal-attempts-including-old-failure.json').write_text(json.dumps(attempts,indent=1)+'\n');assert selected,'finite local repair failed'
 sp=ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb';assert sha(sp)=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2';pins[str(sp.resolve())]=sha(sp);identity=K.A.N.SourceNets(sp.read_bytes());oldnative=K.C.inventory(sp.read_bytes())[3];tracks=[];chunks={}
 for t in fixed+[newf]:
  uid,ch=identity.serial_segment(COM,t['layer'],t['a'],t['b'],t['w']);assert uid not in oldnative;tracks.append({**t,'uuid':uid,'net':identity.raw(COM)});chunks[uid]=ch
 identity.assert_chunks(chunks);assert len(tracks)==len(chunks)==7;after={**before,'tracks':before['tracks']+tracks};ng=K.physical(after,COM,K.hole_context(after))[1];source=K.root(ng,'U14619','7');keys=K.keys(source);assert all(('track',t['uuid'],t['layer'])in keys for t in tracks);assert all(any(r['kind']=='pad'and r['uuid']==uid for r in source)for uid in('013f67e9-bc46-4e7d-8c0e-0cf4e9cf6e4b','53ea5aa5-a009-4367-accd-c5b6de94f6fd'))
 ip=pin('AO1-COM-six-actual-native-ground-islands-source-bridge-census-r632/actual-six-COM-islands-and-SOURCE-metals-NOMINATION_ONLY.pkl','3ed53fb76aaee578bee266481e72135e52bc0115d1caeb659b4db2e2196c409e');islands=pickle.loads(ip.read_bytes());physical_holes,tree=K.hole_context(islands['actual_ground_candidate']);overlaps=[]
 for ly,ix in(('B.Cu',2),('F.Cu',4)):
  bod=unary_union([K.L.body(t)for t in tracks if t['layer']==ly]);bod=bod.difference(unary_union([physical_holes[int(j)]for j in tree.query(bod,predicate='intersects')]));sa=bod.intersection(islands['source_metals'][ly]).area;ta=bod.intersection(islands['islands'][ix]['metals'][ly]).area;assert sa>.005 and ta>.005;overlaps.append({'layer':ly,'actual_BEFORE_SOURCE_finite_overlap_mm2':sa,'actual_BEFORE_target_island_finite_overlap_mm2':ta})
 packet=OUT/'only-seven-NEW-COM-ground-tracks-inside-margin-repaired-widths-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':tracks,'vias':[],'exact_new_chunks':chunks,'original_deletes':{},'selected':selected,'finite_actual_BEFORE_contact_areas':overlaps,'retired_unadopted_R650_R652_proposal_UUIDs':sorted(set(packs[0]['exact_new_chunks'])|set(packs[1]['exact_new_chunks'])),'actual_native_material_deletes':0},protocol=5));result={'verdict':'SEVEN_GROUND_NEW_ONLY_FINITE_LOCAL_REPAIR_AND_WIDTHS_NOMINATED_INDEPENDENT_AUDIT_OPEN','input_SHA256':pins,'selected':selected,'nearest_error_attribution':attribution,'new_tracks':7,'new_holes':0,'actual_old_deletes':0,'removed_only_unadopted_redundant_F_stub_UUID':ft[1]['uuid'],'B_widths_mm':[t['w']for t in tracks if t['layer']=='B.Cu'],'B_lengths_mm':[axis(t).length for t in tracks if t['layer']=='B.Cu'],'F_length_mm':axis(newf).length,'finite_actual_BEFORE_contacts':overlaps,'prospective_COM_source_keys':len(keys),'sparse_packet_file':str(packet.resolve()),'sparse_packet_SHA256':sha(packet),'old_Cu_planes_holes_exact':True,'all_source_ref_losses_native_AFTER_current_SI_thermal':'INDEPENDENT_AUDIT_OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n')
 for p,s in pins.items():assert sha(p)==s,p
 print('R656_COMPLETE',sha(OUT/'receipt.json'),selected,'packet',sha(packet),flush=True)
if __name__=='__main__':main()
