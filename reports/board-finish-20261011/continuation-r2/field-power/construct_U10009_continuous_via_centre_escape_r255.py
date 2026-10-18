"""One remaining A3 load: continuous legal-centre nominations and actual source."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision,from_wkb
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import contact_layout as C
import regional_guarded_declared_projection_r140 as P
from inventory import sha
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
BASE=H/'U10009-continuous-centre-source-search-base-r255';assert not BASE.exists();BASE.mkdir()
parent=H/'B3-envelope-scoped-LOGIC-projection-r233';g,h,b,z,_=pickle.loads((parent/'derived-full-input-model.pkl').read_bytes());restore_bound_generated_precision_states(b,z)
fq=pickle.loads((H/'FIELD5-current-reference-envelope-correction-r238/proposed-corrected-zone.pkl').read_bytes())[0]
for role in ('shape','zone_outline_shape'):raw=fq[role].wkb;fq[role]=set_precision(fq[role],1e-6,mode='pointwise');assert fq[role].wkb==raw
z.append(fq)
_,_,priorbind,_,_=pickle.loads((H/'FIELD5-current-IO3-and-reference-preservation-search-base-r225/model.pkl').read_bytes());hard=copy.deepcopy(priorbind['field_regulated_search_hard_nominees']['planes'])
packet=H.parent/'sbc-power/C1022-validated-native-integration-packet-r222';receipt=json.loads((packet/'receipt.json').read_text(encoding='utf-8'));maskfile=Path(receipt['exact_full_reference_body_file']);assert sha(maskfile)==receipt['exact_full_reference_body_sha256'];hard.append({'uuid':'C1022-exact-new-full-B-reference-body','net':'/LOGIC_GND','layer':'In4.Cu','shape':from_wkb(maskfile.read_bytes()),'clearance_mm':.15})
b['field_regulated_search_hard_nominees']={'planes':hard,'discrete':{'tracks':[],'vias':[]},'exact_current_positive_R214_sha256':'87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e','pending_R233_REG_and_R238_FIELD5_hard_only':True}
after,_=P.projected(g,{**h,'zones':[q for q in h['zones'] if C.norm(q['net'])=='/motherboard_do/DOA_FIELD_3V3']},z)
(BASE/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(BASE/'receipt.json').write_text(json.dumps({'verdict':'U10009_ONLY_SEARCH_PENDING_FEEDS_HARD_NO_ACCEPTANCE','model_sha256':sha(BASE/'model.pkl'),'source_model_sha256':sha(parent/'derived-full-input-model.pkl'),'all_old_reference_and_IO3_actual_fill_masks_bound':True,'C1022_packet_sha256':sha(packet/'receipt.json'),'no_board_or_native_write':True},indent=1)+'\n',encoding='utf-8')
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace('import guarded_power_projection_r44 as P','import regional_guarded_declared_projection_r140 as P')
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'","OUT=HERE/'U10009-continuous-centre-ordinary-source-escape-r255';BASE=HERE/'U10009-continuous-centre-source-search-base-r255'")
s=s.replace('for bank,net,ref,pin,policy in PORTS:',"for bank,net,ref,pin,policy in [x for x in PORTS if x[0]=='A3V3']:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'","xs=gs[gi];\n   if not any(q['kind']=='pad' and(q.get('ref'),q.get('pin'))==('U10009','4') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace('anchor.x-8,anchor.y-8,anchor.x+8,anchor.y+8','anchor.x-12,anchor.y-12,anchor.x+12,anchor.y+12')
# Exact continuous .5/.2 centre regions precede the historical grid/rings.
marker='      seen=set()\n      for _,candidate,part in sorted(candidates,key=lambda x:x[0]):'
replacement='''      centre_walls=[];query=win.buffer(1.5)
      for layer in LAYERS:
       centre_walls += [P.bounded_buffer(rec[layer][int(j)]['shape'],.25+gap(rec[layer][int(j)]['net'])) for j in trees[layer].query(query,predicate='intersects') if C.norm(rec[layer][int(j)]['net'])!=net]
       centre_walls += [P.bounded_buffer(q['shape'],.25+proposal_gap(q)) for q in plane_records if q['layer']==layer and C.norm(q['net'])!=net and not maycarve(q) and q['shape'].intersects(query)]
      centre_walls += [P.bounded_buffer(smd[int(j)]['shape'],.1+.275) for j in st.query(query,predicate='intersects')]
      centre_walls += [P.bounded_buffer(holes[int(j)]['shape'],.1+.275) for j in ht.query(query,predicate='intersects')]
      for area in h['rule_areas']:
       if area.get('no_vias'):centre_walls += [P.bounded_buffer(sh,.25+.025) for sh in C.poly(area['outline']) if sh.intersects(query)]
      for area in reserved['keepouts']:
       if net not in exceptions.get(area['name'],set()):centre_walls += [P.bounded_buffer(sh,.25+.025) for sh in C.poly(area['outline']) if sh.intersects(query)]
      centres=win.difference(unary_union(centre_walls)).buffer(-.000003)
      continuous=[]
      for part in parts:
       for pocket in polys(part.intersection(centres)):
        for pt in [pocket.representative_point(),nearest_points(anchor,pocket)[1]]:
         candidate=(round(pt.x,6),round(pt.y,6))
         if pocket.contains(Point(candidate)):continuous.append((Point(candidate).distance(anchor),candidate,part))
      write(OUT/'continuous-centre-checkpoint.json',{'target':'U10009.4','outer_stub_width_mm':width,'window_radius_mm':12,'complete_ordinary_diameter_drill_mm':[.5,.2],'continuous_region_area_mm2':centres.area,'continuous_nominations':len(continuous),'historical_grid_and_ring_nominations':len(candidates),'no_global_no_path_claim':True})
      candidates=continuous+candidates
      seen=set()
      for _,candidate,part in sorted(candidates,key=lambda x:x[0]):'''
assert s.count(marker)==1;s=s.replace(marker,replacement)
s=s.replace('controller-regulated-r76/','controller-u10009-continuous-source-r255/').replace('.read_text()',".read_text(encoding='utf-8')")
(BASE/'expanded-constructor.py').write_text(s,encoding='utf-8')
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
