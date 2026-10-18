"""Close the whole physical F track component, including overlapped short segments."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'inventory_existing_FA_via_to_via_F_chain_r13.py').read_text().replace("'existing-FA-via-to-via-F-chain-r13'","'complete-existing-FA-via-to-via-F-chain-r14'")
needle="tracks=[i for i in path if allF[i]['kind']=='track'];assert len(tracks)==len(path)-2;retired={allF[i]['uuid']for i in tracks}"
assert s.count(needle)==1
s=s.replace(needle,"tracks=[i for i in path if allF[i]['kind']=='track'];assert len(tracks)==len(path)-2;closed=set(tracks);todo=list(tracks)\n    while todo:\n        i=todo.pop()\n        for j in adj[i]:\n            if allF[j]['kind']=='track'and j not in closed:closed.add(j);todo.append(j)\n    tracks=sorted(closed);retired={allF[i]['uuid']for i in tracks}")
exec(compile(s,str(HERE/'inventory_existing_FA_via_to_via_F_chain_r13.py'),'exec'),globals())
