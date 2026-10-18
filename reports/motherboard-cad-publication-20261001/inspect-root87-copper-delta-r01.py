"""Exact current-versus-published native identities; display review only."""
from pathlib import Path
import sys,json,hashlib,collections
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity
p=Path(__file__).parent/'source26-root87-ledger-r01';p.mkdir(exist_ok=False)
view=Path('hardware/board_review');j=json.loads((view/'board-view.json').read_text())
base=view/j['boards'][0]['board_file']
candidate=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb')
b=pcbnew.LoadBoard(str(base));a=pcbnew.LoadBoard(str(candidate))
old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};now={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()}
rows=[dict(uuid=u,old_identity=v,new_identity=now.get(u),reviewed=False)for u,v in old.items()if now.get(u)!=v]
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
out=dict(base_revision=j['current_revision'],base_file=str(base),base_sha256=sha(base),candidate_file=str(candidate),candidate_sha256=sha(candidate),changes=rows)
(p/'draft-copper-changes.json').write_text(json.dumps(out,indent=2))
changed=[r for r in rows if r['new_identity']is not None]
removed=[r for r in rows if r['new_identity']is None]
summary=dict(changed=len(changed),retired=len(removed),added=len(set(now)-set(old)),changed_actual_rows=changed,retired_nets=dict(collections.Counter(r['old_identity'][1]for r in removed)))
(p/'exact-delta-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
