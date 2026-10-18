"""Preserve R217 compile failure; correct only the added assertion indentation."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'construct_remaining_IO3_indexed_direct_joins_r217.py').read_text()
s=s.replace('remaining-original-IO3-indexed-direct-source-nominees-r217','remaining-original-IO3-indexed-direct-source-nominees-r218')
s=s.replace("\n  expected=json.loads", "\n   expected=json.loads").replace("\n  assert not options", "\n   assert not options").replace("\n  put(O/'exact-C10025", "\n   put(O/'exact-C10025")
s=s.replace("fails[-1]['first_failures']==expected['first_failures']","json.loads(json.dumps(fails[-1]['first_failures']))==expected['first_failures']")
exec(compile(s,str(P/'construct_remaining_IO3_indexed_direct_joins_r217.py'),'exec'))
