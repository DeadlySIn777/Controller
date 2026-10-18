"""Preserve first inventory-schema failure; use exact reserved keepout schema."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'construct_remaining_IO3_outer_source_joins_r213.py').read_text()
assert "reserved['rule_areas']" in s
s=s.replace('remaining-original-IO3-ordinary-outer-source-joins-r213','remaining-original-IO3-ordinary-outer-source-joins-r215').replace("reserved['rule_areas']","reserved['keepouts']")
s=s.replace("B3-exact-cross-layer-pair-r206/proposed-discrete.pkl","B3-exact-cross-layer-pair-r206/cross-layer-discrete.pkl")
s=s.replace("if peerf.exists():peer=pickle.loads(peerf.read_bytes())","if peerf.exists():\n  assert sha(peerf)=='1bc5d54aff79c349f74e709e491a71440d6d1797ce124d1e65a7d44331414443';peer=pickle.loads(peerf.read_bytes())")
s=s.replace("if peerd.exists():pd=pickle.loads(peerd.read_bytes());peertracks=pd.get('tracks',[]);peervias=pd.get('vias',[])","if peerd.exists():\n  assert sha(peerd)=='7509b690027467fed1c9bd4ee57ed863eccbec2ae0bb7b9b26cb9ea0c5c014fb';pd=pickle.loads(peerd.read_bytes());peertracks=pd.get('tracks',[]);peervias=pd.get('vias',[])")
exec(compile(s,str(P/'construct_remaining_IO3_outer_source_joins_r213.py'),'exec'))
