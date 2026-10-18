"""Translate the independently reviewed literal CAD delta for the native publisher."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import identity
root=Path('reports/motherboard-cad-publication-20261001')
out=root/'ROOT101-publication-authorization-r01';assert not out.exists();out.mkdir()
ledger=root/'CAD24-to-ROOT101-ledger-r01';freeze=json.loads((ledger/'freeze.json').read_text())
assert freeze['passed']
for name,h in freeze['files_sha256'].items():assert sha(ledger/name)==h
record=json.loads((ledger/'receipt.json').read_text());assert record['passed']
before=Path(record['published_board']);board=Path(record['target_board'])
adoption=board.parent/'adoption.json';ad=json.loads(adoption.read_text())
assert ad['adopted'] and ad['passed'] and ad['board_sha256']==sha(board)==record['target_board_sha256']
assert ad['missing_joins']==3528 and not ad['manufacturing_ready']
assert sha(before)==record['published_board_sha256']
literal=json.loads((ledger/'literal-copper-delta.json').read_text())
b=pcbnew.LoadBoard(str(before));a=pcbnew.LoadBoard(str(board))
old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};new={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()}
retired={x['uuid']for x in literal['retired']};changed={x['uuid']for x in literal['changed']}
assert retired==set(old)-set(new)
assert changed=={u for u in set(old)&set(new)if old[u]!=new[u]}
assert len(retired)==1881 and len(changed)==21
rows=[dict(uuid=u,old_identity=old[u],new_identity=new.get(u),reason='Literal reviewed CAD24-to-ROOT101 '+('retirement'if u in retired else 'geometry correction')+'; whole adopted board native Source/connectivity and circuit proofs are in the linked adoption. This is WIP publication, not fabrication approval.')for u in sorted(retired|changed)]
write(out/'publisher-copper-delta.json',dict(changes=rows,independent_ledger_sha256=sha(ledger/'freeze.json'),adoption_sha256=sha(adoption)))
write(out/'authorization.json',dict(passed=True,publish_working_CAD_allowed=True,base_revision='20260930-24',revision='20261001-25',board_sha256=sha(board),input_sha256={str(p.resolve()):sha(p)for p in [before,board,adoption,ledger/'freeze.json',out/'publisher-copper-delta.json',Path(__file__)]},supersedes_pending_publication_only=True,electrical_or_manufacturing_qualification_expanded=False,manufacturing_ready=False))
print(dict(passed=True,reviewed_changed_old_Cu=len(rows)))
