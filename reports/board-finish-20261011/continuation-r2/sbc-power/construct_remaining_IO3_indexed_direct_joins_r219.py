"""Correct generated assertion block structurally; freeze exact effective source."""
from pathlib import Path
P=Path(__file__).resolve().parent
wrapper=(P/'construct_remaining_IO3_indexed_direct_joins_r217.py').read_text()
wrapper=wrapper.replace('remaining-original-IO3-indexed-direct-source-nominees-r217','remaining-original-IO3-indexed-direct-source-nominees-r219')
mark="exec(compile(s,str(P/'construct_remaining_IO3_direct_capsule_joins_r216.py'),'exec'))"
assert wrapper.count(mark)==1
correction="""rows=s.splitlines()
i=next(i for i,line in enumerate(rows) if line.strip()=="if p['ref']=='C10025':")
indent=len(rows[i])-len(rows[i].lstrip())
for j in range(i+1,i+4):rows[j]=' '*(indent+1)+rows[j].lstrip()
s='\\n'.join(rows)+'\\n'
s=s.replace("fails[-1]['first_failures']==expected['first_failures']","json.loads(json.dumps(fails[-1]['first_failures']))==expected['first_failures']")
EFFECTIVE_SOURCE=s
"""
wrapper=wrapper.replace(mark,correction+mark)
exec(compile(wrapper,str(P/'construct_remaining_IO3_indexed_direct_joins_r217.py'),'exec'))
