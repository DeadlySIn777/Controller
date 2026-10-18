"""Correct source seed wrapper and preserve exact nanometre terminal precision."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;p=HERE/'ao1_reference_coupled_r1.py';t=p.read_text()
t=t.replace('import incremental_exact_model as I','import incremental_exact_model as I\nimport ao1_astar_exact_r1 as E')
t=t.replace("OUT=HERE/'ao1-reference-coupled-r1.json'","OUT=HERE/'ao1-reference-coupled-r2.json'")
t=t.replace("target_seeds=S.seed_sites(target,'In3.Cu',strict[SDI,'In3.Cu'],WINDOW)","target_records=S.seed_sites(target,'In3.Cu',strict[SDI,'In3.Cu'],WINDOW)\n    target_seeds=[p for p,r in target_records]")
needle="                path,search=S.astar(shape,starts,goals,time.monotonic()+5,node_cap=50000) if starts and goals else (None,{'reason':'Full-body referenced endpoint absent','nodes':0})"
replacement="""                start_rows=[(p,{'uuid':signals[net][0] if p==signals[net][1] else initial.pads['U14626.9#0' if net==VREF else 'U14626.8#0']['uuid'],'kind':'via' if p==signals[net][1] else 'pad'}) for p in starts]
                goal_rows=[(p,next((r for q,r in target_records if q==p),{'uuid':signals[net][0] if p==signals[net][1] else initial.pads['U14636.7#0']['uuid'],'kind':'via' if p==signals[net][1] else 'pad'})) for p in goals]
                path,search=E.astar(shape,start_rows,goal_rows,time.monotonic()+5,node_cap=50000) if starts and goals else (None,{'reason':'Full-body referenced endpoint absent','nodes':0})"""
assert needle in t;t=t.replace(needle,replacement)
q=HERE/'ao1_reference_coupled_r2.py'
if q.exists():raise ValueError('Fresh r2 required')
q.write_text(t);compile(t,str(q),'exec')
(HERE/'ao1-reference-r1-seed-diagnostic.json').write_text(json.dumps({'verdict':'STOPPED_BEFORE_SITE_OR_PATH_RESULT','source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reason':'Source seed_sites returns (point, physical-record), not bare coordinates; corrected separate r2 preserves record identities and nm terminal precision','board_emitted':False,'native_jobs':0},indent=1)+'\n')
print('Exact-terminal r2 syntax PASS; r1 preserved')
