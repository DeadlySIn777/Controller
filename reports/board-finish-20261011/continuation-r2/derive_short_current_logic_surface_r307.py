"""Use existing conservative power widths and bounded continuous detours."""
import hashlib,json,runpy
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'nominate_short_current_logic_surface_connections_r305.py';target=H/'nominate_short_current_logic_surface_connections_r307.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not target.exists();code=source.read_text()
def replace(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
replace('import guarded_power_projection_r44 as Z','import guarded_power_projection_r44 as Z\nimport tri_route as T')
replace("trees={ly:STRtree([r['shape']for r in rows]) for ly,rows in records.items()}","widthsfile=Path('Z:/pcb-runs/claude-finish/tools/power_widths.json');widths=json.loads(widthsfile.read_bytes())\n trees={ly:STRtree([r['shape']for r in rows]) for ly,rows in records.items()}")
replace("a=r['left_actual_at_mm'];b=r['right_actual_at_mm'];net=r['normalized_net'];raw=r['raw_net']","a=r['left_actual_at_mm'];b=r['right_actual_at_mm'];net=r['normalized_net'];raw=r['raw_net'];width=max(.2,float(widths.get(net,{}).get('width',.2)))")
replace("for ly in r['common_native_surfaces']:\n   for path in options:","""for ly in r['common_native_surfaces']:
   window=box(min(a[0],b[0])-2,min(a[1],b[1])-2,max(a[0],b[0])+2,max(a[1],b[1])+2);cuts=[]
   for j in trees[ly].query(window.buffer(2.25),predicate='intersects'):
    q=records[ly][int(j)]
    if L.norm(q['raw_net'])==net:continue
    gap=max(.15 if dom.get(L.norm(q['raw_net']))==dom[net] else .6,q['local'])+.025+q['extra'];cuts.append(Z.bounded_buffer(q['shape'],width/2+gap))
   for uid,hn,s in holes:
    if uid not in endpoint_uids and s.intersects(window.buffer(2.25)):cuts.append(Z.bounded_buffer(s,width/2+.280))
   for rule,s,isreserve in rules:
    if ly in rule['layers'] and not(isreserve and net in exempt.get(rule['name'],set())):cuts.append(Z.bounded_buffer(s,width/2+.025))
   for prior in accepted:
    if prior['layer']==ly and prior['normalized_net']!=net:cuts.append(Z.bounded_buffer(prior['body'],width/2+(.175 if dom[prior['normalized_net']]==dom[net] else .625)))
   free=window.intersection(board.buffer(-width/2)).difference(unary_union(cuts));detour=None
   for face in K.RF.parts(free):
    if face.covers(Point(a)) and face.covers(Point(b)):
     detour,method=T.route(face,a,b);break
   lyoptions=list(options)
   if detour:lyoptions.append([[round(x,6),round(y,6)]for x,y in detour])
   for path in lyoptions:""")
replace("body=Z.bounded_buffer(LineString(path),.1);errors=[]","body=Z.bounded_buffer(LineString(path),width/2);errors=[]")
replace("trees[ly].query(body.buffer(1.025)","trees[ly].query(body.buffer(1.025)")
replace("'layer':ly,'w':.2,'a':aa","'layer':ly,'w':width,'a':aa")
replace("'existing_Cu_removed':0,'ALL_matching_FULL_AFTER", "'existing_Cu_removed':0,'conservative_existing_power_width_table_SHA256':sha(widthsfile),'conservative_width_table_is_historical_NOT_current_load_qualification':True,'bounded_continuous_detour_window_mm':2,'ALL_matching_FULL_AFTER")
# Enclose every possible 2 mm detour and its maximum 3 mm power body/guards.
replace("roi=unary_union([box(min(r['left_actual_at_mm'][0],r['right_actual_at_mm'][0])-2,min(r['left_actual_at_mm'][1],r['right_actual_at_mm'][1])-2,max(r['left_actual_at_mm'][0],r['right_actual_at_mm'][0])+2,max(r['left_actual_at_mm'][1],r['right_actual_at_mm'][1])+2)","roi=unary_union([box(min(r['left_actual_at_mm'][0],r['right_actual_at_mm'][0])-5,min(r['left_actual_at_mm'][1],r['right_actual_at_mm'][1])-5,max(r['left_actual_at_mm'][0],r['right_actual_at_mm'][0])+5,max(r['left_actual_at_mm'][1],r['right_actual_at_mm'][1])+5)")
code=code.replace('r305','r307').replace('R305','R307');compile(code,str(target),'exec');target.write_text(code)
receipt=H/'short-current-logic-conservative-width-and-continuous-detour-derivation-r307.json';assert not receipt.exists()
receipt.write_text(json.dumps({'source_file':str(source),'source_SHA256':sha(source),'derived_file':str(target),'derived_SHA256':sha(target),'changes':['existing conservative power table width lower bounds','continuous bounded 2mm detour on same surface','5mm broadphase ROI enclosure for all candidate bodies/guards'],'native_clearance_plus_planning_margin_holes_rules_and_no_old_Cu_mutation_unchanged':True,'all_source_full_AFTER_oldcontacts_reference_current_native_gates_OPEN':True,'adopted':False},indent=1)+'\n')
runpy.run_path(str(target),run_name='__main__')
