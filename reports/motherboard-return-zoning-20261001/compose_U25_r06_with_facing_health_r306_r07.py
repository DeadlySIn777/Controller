from pathlib import Path
import sys,json,subprocess
sys.path.insert(0,str(Path.cwd()/'tools'))
from hardware_map_motherboard_domains import sha,write
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb')
D=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-orthogonal-Source-feed-r06/motherboard-U25-orthogonal-Source-feed-candidate.kicad_pcb')
T=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r306/motherboard-health-U19-facing-cell-candidate.kicad_pcb')
P=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-r06-composition-scope-r01');assert not P.exists();P.mkdir()
assert sha(D)=='426f3b44163118efbea05515bc8758a76d9b63c5efad76e841298c0f160b04d1'and sha(T)=='96e23dbe3ffc1e307d2ccf49bec92ab8c6b1b4478a3014635bcf0f59358be8ab'
OLD=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-U13-actual-Source-return-r05/bounded-scope-from-health-r01.json');scope=json.loads(OLD.read_text());scope['reviewed_scope_reason']+=' The existing B positive diagonal UUID is now an orthogonal handoff to the actual retained same-rail cap branch, removing its proven native sliver without changing any DRC or reference tolerance.';write(P/'bounded-scope.json',scope);write(P/'inputs.json',{str(q):sha(q)for q in[B,D,T,OLD,Path(__file__)]})
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-facing-health-U25-actual-composition-r07')
r=subprocess.run([sys.executable,'tools/hardware_merge_bounded_pcb_delta.py','--before',str(B),'--donor',str(D),'--target',str(T),'--scope',str(P/'bounded-scope.json'),'--out',str(O)],capture_output=True,text=True);(P/'command.txt').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,flush=True);assert r.returncode==0
