"""Serialization successor; exact authorized wedge scope and old tokens only."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/construct_CM79_q053_literal_original_vertex_splice_current_r344.py'
s=p.read_text(encoding='utf-8').replace('r344','r346').replace('R344','R346')
assert "authority+'roles=[];masks=[];changed=set()'" in s
s=s.replace("authority+'roles=[];masks=[];changed=set()'","authority+' roles=[];masks=[];changed=set()'")
s=s.replace("assert dig(cut)==json.loads((H/'sbc-power/q053-R338-raw-gain-controlling-edge-and-declared-corridor-attribution-r339/receipt.json').read_text())['R338_failure_sha256']if False else True;",'')
needle="spliceDir=H/'sbc-power/q053-only-new-native-inward-intersection-splice-explicit-controlled-boundary-wedge-proposal-r343';"
assert needle in s
authority="namedAuthority=H/'sbc-power/q053-twelve-new-intersections-exact-old-edge-and-named-negative-wedge-authority-r345/receipt.json';assert sha(namedAuthority)=='cccba325472a731687197f5ecd67d3b6719dc23821d3f01d6bfd39da1c0271da';frozenNamed=json.loads(namedAuthority.read_text());assert all(sha(file)==bound for file,bound in frozenNamed['files'].items());"
s=s.replace(needle,authority+needle)
s=s.replace("'R343_splice_receipt_sha256':sha(spliceDir/'receipt.json')","'R345_exact_before_edges_and_whole_named_wedges_authority_sha256':sha(namedAuthority),'R343_splice_receipt_sha256':sha(spliceDir/'receipt.json')")
exec(compile(s,str(__file__),'exec'))
