from pathlib import Path
import psutil,json,hashlib,datetime
H=Path(__file__).resolve().parent
out=H/'R320-own-quadratic-ring-review-stopped-preserved.json';assert not out.exists()
p=psutil.Process(67504);cmd=p.cmdline();assert len(cmd)>=3 and Path(cmd[1]).name=='run_host_confined.py'and cmd[2]=='review_R157_zero_length_expected_edges_r320.py';assert not p.children();p.terminate();p.wait(10)
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
r={'verdict':'OWN_READ_ONLY_REVIEW_PROCESS_STOPPED_TO_CORRECT_QUADRATIC_CANONICAL_ENUMERATION','pid':67504,'command_line':cmd,'script_sha256':sha(H/'review_R157_zero_length_expected_edges_r320.py'),'reason':'One bound native expected outer has36015 vertices; enumerate only lexicographically least start positions without changing exact cyclic-ring equality','source_candidate_sha256':sha(H.parent/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb'),'no_board_or_geometry_mutation':True,'native_jobs':0,'stop_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()};out.write_text(json.dumps(r,indent=1)+'\n');print(sha(out))
