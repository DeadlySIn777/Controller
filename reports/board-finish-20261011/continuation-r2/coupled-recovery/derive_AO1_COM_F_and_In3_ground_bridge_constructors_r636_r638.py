"""Two distinct finite COM ground joins; old same-net plated holes remain real.

Ground conductors may terminate in their own actual plated annuli. All body
contacts are tested after physical drill subtraction; no borrowed hole cap.
"""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;src=H/'construct_AO1_COM_actual_source_to_isolator_In4_ground_bridge_r634.py';base=src.read_text()
old="req=v['drill']/2+radius+(.000025 if K.L.norm(v['net'])==COM else .275);obs.append(K.Z.bounded_disk(v,req))"
new="if K.L.norm(v['net'])==COM:continue # same-net plated contact; physical body below is drilled\n  req=v['drill']/2+radius+.275;obs.append(K.Z.bounded_disk(v,req))"
assert old in base;base=base.replace(old,new)
old="if not s.envelope.disjoint(clip):obs.append(K.Z.bounded_buffer(s,radius+(.000025 if K.L.norm(p['net'])==COM and not p['npth']else .275)))"
new="if not s.envelope.disjoint(clip)and(K.L.norm(p['net'])!=COM or p['npth']):obs.append(K.Z.bounded_buffer(s,radius+.275))"
assert old in base;base=base.replace(old,new)
old="body=K.Z.bounded_buffer(LineString(pts),radius);sa=body.intersection(source);ta=body.intersection(target);"
new="body=K.Z.bounded_buffer(LineString(pts),radius);physical_holes,ht=K.hole_context(islands['actual_ground_candidate']);physical_body=body.difference(unary_union([physical_holes[int(j)]for j in ht.query(body,predicate='intersects')]));sa=physical_body.intersection(source);ta=physical_body.intersection(target);"
assert old in base;base=base.replace(old,new)
specs=[('r636','F.Cu',1,('U14624','3','19434a4b-d4ed-4193-90b1-b90a71062411'),"box(351,140,363,149)","[[355.898,143.9],[356.898,143.85]]"),('r638','In3.Cu',2,('U14623','9','013f67e9-bc46-4e7d-8c0e-0cf4e9cf6e4b'),"box(353,137,381,163)","[[361.7409622594442,142.52870979134772],[372.89919811712986,150.5010751738769]]")]
for rev,ly,i,(ref,pin,uid),frame,near in specs:
 dest=H/('construct_AO1_COM_actual_source_ground_bridge_'+rev+'.py');assert not dest.exists();text=base.replace('r634',rev).replace('R634_',rev.upper()+'_').replace("LY='In4.Cu'","LY='"+ly+"'")
 text=text.replace("AO1-COM-actual-SOURCE-to-U14623-nine-In4-finite-ground-bridge-"+rev,"AO1-COM-actual-SOURCE-to-"+ref+'-'+pin+'-'+ly.replace('.','-')+'-finite-ground-bridge-'+rev)
 text=text.replace("islands['islands'][2]","islands['islands']["+str(i)+"]").replace("p['ref']=='U14623'and p['pin']=='9'","p['ref']=='"+ref+"'and p['pin']=='"+pin+"'").replace("r['uuid']=='013f67e9-bc46-4e7d-8c0e-0cf4e9cf6e4b'","r['uuid']=='"+uid+"'")
 text=text.replace("win=box(354,145,373,163)","win="+frame).replace("[[361.995154,153.873904],[366.004844,154.726098]]",near)
 text=text.replace('only-NEW-COM-In4-ground-tracks-source-isolator-NOMINEE.pkl','only-NEW-COM-'+ly.replace('.','-')+'-ground-tracks-NOMINEE.pkl').replace('actual_BEFORE_U14623_9_island_metal_overlap_mm2','actual_BEFORE_'+ref+'_'+pin+'_island_metal_overlap_mm2')
 text=text.replace('ACTUAL_COM_SOURCE_TO_ISOLATOR_IN4_GROUND_BRIDGE','ACTUAL_COM_SOURCE_TO_'+ref+'_'+pin+'_'+ly.replace('.','_').upper()+'_GROUND_BRIDGE')
 dest.write_text(text);print(rev.upper()+'_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
