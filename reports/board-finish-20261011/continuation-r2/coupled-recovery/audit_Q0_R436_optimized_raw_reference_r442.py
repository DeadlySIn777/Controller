"""Preserve R438 partial failures; finish its raw reference diagnosis efficiently."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'audit_Q0_R436_independent_physical_source_reference_r438.py'
code=base.read_text().replace('Q0-R436-independent-physical-source-reference-r438','Q0-R436-optimized-raw-reference-r442').replace('Q0_R438_','Q0_R442_')
old="put(out/'all-ten-actual-source-bank-ledger.json',roots);oldrefs="
new="""(out/'actual-new-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));(out/'actual-before-and-after-source-banks.pkl').write_bytes(pickle.dumps({'before':oldbanks,'after':banks},protocol=5))
put(out/'all-ten-actual-source-bank-ledger.json',roots);oldrefs="""
assert old in code;code=code.replace(old,new,1)
old="for t in before['tracks']:\n if t['uuid']in removed"
new="""reference_deltas={l:oldrefs[l].difference(refs[l])for l in refs}
reference_delta_envelopes={l:sh.envelope for l,sh in reference_deltas.items()}
own_by_net_outer={}
for uid,o in support:
 net=K.L.norm(hvia[uid]['net']);own_by_net_outer.setdefault((net,o),[]).append(support[(uid,o)])
own_by_net_outer={key:unary_union(xs)for key,xs in own_by_net_outer.items()}
for l,sh in reference_deltas.items():(out/(l+'-exact-actual-source-reference-delta.wkb')).write_bytes(sh.wkb)
for t in before['tracks']:
 if t['uuid']in removed"""
assert old in code;code=code.replace(old,new,1)
old="l=t['layer'];body=K.A.shape({'kind':'segment',**t});delta=oldrefs[l].difference(refs[l]);raw=body.intersection(delta)"
new="""l=t['layer'];delta=reference_deltas[l]
 if delta.is_empty:continue
 axis=LineString([t['a'],t['b']])if not t.get('m')else K.A.shape({'kind':'segment',**t})
 if axis.distance(reference_delta_envelopes[l])>t['w']/2:continue
 body=K.A.shape({'kind':'segment',**t});raw=body.intersection(delta)"""
assert old in code;code=code.replace(old,new,1)
old="own=unary_union([sh for(uid,o),sh in support.items()if o==outer and K.L.norm(hvia[uid]['net'])==K.L.norm(t['net'])]);loss=raw.difference(own)"
new="own=own_by_net_outer.get((K.L.norm(t['net']),outer),Point().buffer(0));loss=raw.difference(own)"
assert old in code;code=code.replace(old,new,1)
exec(compile(code,str(base),'exec'))
