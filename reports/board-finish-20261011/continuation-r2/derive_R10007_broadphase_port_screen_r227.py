"""Index the same candidate obstacles before the finite port screen."""
import hashlib,json,runpy
from pathlib import Path
import psutil
H=Path(__file__).resolve().parent;source=H/'screen_R10007_HOST_existing_return_B_F_ports_r226.py';target=H/'screen_R10007_HOST_existing_return_B_F_ports_r227.py'
assert not target.exists();code=source.read_text().replace('screen-r226','screen-r227').replace('R226','R227')
needle=" holes=[(v['uuid'],Point(v['x'],v['y']),v['drill']/2)for v in h['vias']]"
assert code.count(needle)==1
code=code.replace(needle,needle+"""
 ht=STRtree([x[1]for x in holes]);hole_query=max(.815,.1+.275+max(x[2]for x in holes))
 padholes=[s for p in scene['pads']for s in K.L.poly(p.get('hole')or[])];pht=STRtree(padholes)
 foreign={l:[(z,s)for z in full['zones']if K.L.norm(z['net'])!=net and dom[K.L.norm(z['net'])]!=dom[net]for s in K.L.poly(z['fills'].get(l,[]))]for l in K.LAYERS}
 ztrees={l:STRtree([x[1]for x in xs])for l,xs in foreign.items()}
 zquery={l:.25+.025+max([.6]+[float(z['clearance_mm'])for z,s in xs])for l,xs in foreign.items()}
 board_interior=unary_union(K.L.poly(h['outline'])).buffer(-.525)
""")
needle="    for uid,c,dr in holes:\n     if p.distance(c)<.815:"
assert code.count(needle)==1
code=code.replace(needle,"    if not board_interior.covers(p):bad.append('board_edge')\n    for j in ht.query(p.buffer(hole_query),predicate='intersects'):\n     uid,c,dr=holes[int(j)]\n     if p.distance(c)<.815:")
needle="    for j in st.query(p.buffer(.375),predicate='intersects'):"
assert code.count(needle)==1
code=code.replace(needle,"    for j in pht.query(p.buffer(.375),predicate='intersects'):\n     if p.distance(padholes[int(j)])-.1<.275:bad.append('pad_hole_to_signal_drill');break\n"+needle)
start=code.index("     for z in full['zones']:");end=code.index("     for z in h['rule_areas']:",start)
code=code[:start]+"""     for j in ztrees[l].query(p.buffer(zquery[l]),predicate='intersects'):
      z,s=foreign[l][int(j)];other=K.L.norm(z['net'])
      if p.distance(s)-.25<max(gap(net,other),float(z['clearance_mm']))+.025:bad.append('original_other_domain_fill_'+l);break
"""+code[end:]
code=code.replace("'no_original_Cu_edit':True","'no_original_Cu_edit':True,'broadphase_only_same_exact_distance_predicates':True,'additional_board_edge_and_native_pad_hole_checks':True")
compile(code,str(target),'exec');target.write_text(code)
receipt={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'same_finite_return_circle_candidates':True,'foreign_fill_exact_distance_same':True,'added_native_pad_hole_and_board_edge_guards':True,'R226_partial_progress_preserved':'two return barrels visited;61 finite geometry ports after second; no complete receipt and no adopted candidate','native_processes_untouched':True}
p=psutil.Process(77700);assert abs(p.create_time()-1791834064.8424249)<.001
assert p.cmdline()[-1].endswith('screen_R10007_HOST_existing_return_B_F_ports_r226.py')
receipt['stopped_only_owned_host']={'pid':p.pid,'create_time':p.create_time(),'cmdline':p.cmdline(),'cpu_seconds':sum(p.cpu_times()[:2])};p.terminate();p.wait(timeout=10)
(H/'R10007-port-screen-r227-derivation-and-owned-stop.json').write_text(json.dumps(receipt,indent=1)+'\n')
runpy.run_path(str(target),run_name='__main__')
