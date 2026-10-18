"""Use the actual retained all-six-layer HOST source barrel through In3."""
import hashlib,json,runpy
from pathlib import Path
import psutil
H=Path(__file__).resolve().parent;source=H/'nominate_R10007_joint_B_F_actual_source_routes_r228.py';target=H/'nominate_R10007_native_HOST_In3_terminal_routes_r233.py';assert not target.exists()
code=source.read_text().replace('r228','r233').replace('R228','R233').replace('screen-r227','screen-r229')
needle="[('B.Cu','In4.Cu'),('F.Cu','In1.Cu')]";assert code.count(needle)==1;code=code.replace(needle,"[('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]")
needle="layers={'B.Cu','F.Cu'}";assert code.count(needle)==1;code=code.replace(needle,"layers={'B.Cu','In3.Cu'}")
needle=" for pose in r['nominees']:";assert code.count(needle)==1
code=code.replace(needle,"""
 oldterminal=next(v for v in h['vias']if v['uuid']=='a09f14c5-dadb-4548-9346-b2e2be83b03f')
 assert K.L.norm(oldterminal['net'])==SIG and oldterminal['flashed']==list(K.LAYERS) and (oldterminal['x'],oldterminal['y'],oldterminal['d'],oldterminal['drill'])==(206.15,146.15,.6,.3)
 _,hostgroups=K.physical(full,SIG,K.hole_context(full));actualhost=K.root(hostgroups,'U13004','31');assert ('via',oldterminal['uuid'],'In3.Cu')in K.keys(actualhost)
 oldpoint=Point(oldterminal['x'],oldterminal['y']);hostF=oldpoint.buffer(.3,quad_segs=128).difference(oldpoint.buffer(.15,quad_segs=128));oldcap=oldpoint.buffer(.575,quad_segs=128)
 poses=sorted(r['nominees'],key=lambda p:(p['pose']!=[180,-10.5,-3.5],p['pose']!=[0,-10.5,-3.5]))
 for pose in poses:""")
needle="('HOST_F',None,SIG,'F.Cu',ann,hostF)";assert code.count(needle)==1;code=code.replace(needle,"('HOST_IN3',None,SIG,'In3.Cu',ann,hostF)")
needle="allowed=ref.union(cap)if net==SIG else ref";assert code.count(needle)==1;code=code.replace(needle,"allowed=ref.union(cap).union(oldcap)if net==SIG and layer=='In3.Cu'else ref.union(cap)if net==SIG else ref")
code=code.replace("['B.Cu','F.Cu']","['B.Cu','In3.Cu']")
code=code.replace("'native_jobs':0","'existing_actual_HOST_source_terminal_UUID':oldterminal['uuid'],'existing_actual_source_terminal_mask_all6_unchanged':True,'terminal_own_radius_mm':.575,'existing_terminal_scope_authority_and_actual_source_ref_after_gates':'OPEN; raw inherited-before gaps must be distinguished, no neighboring aperture borrow','native_jobs':0")
compile(code,str(target),'exec');target.write_text(code)
receipt={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'change':'actualHOSTnativeall6 sourcea09f viaB/In3 transport; noF source island crossing/new terminalhole','R230_partial':'GND_B andHOST_B positive on multiple near442fd sites; Fphase failed on all visited candidates; finite census incomplete and no acceptedroute','native_processes_untouched':True}
p=psutil.Process(30332);assert abs(p.create_time()-1791834803.3377948)<.001;assert p.cmdline()[-1].endswith('nominate_R10007_cached_census_joint_B_F_routes_r230.py')
receipt['stopped_only_owned_host']={'pid':p.pid,'create_time':p.create_time(),'cmdline':p.cmdline(),'cpu_seconds':sum(p.cpu_times()[:2])};p.terminate();p.wait(timeout=10)
(H/'R10007-In3-source-terminal-r233-derivation-and-owned-stop.json').write_text(json.dumps(receipt,indent=1)+'\n')
runpy.run_path(str(target),run_name='__main__')
