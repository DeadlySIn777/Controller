"""Exact seven-site preflight before a new coupled transport candidate."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'screen_Q0_SENSE_FLT_minimal_dive_ports_r398.py'
code=base.read_text().replace('Q0-FLT-four-coupled-blockers-two-port-preflight-r398','Q0-separated-signal-port-pair-prefight-r422').replace('[229.12,157.72]','[229.23,157.82]').replace('[229.05,158.65]','[229.18,158.636]').replace('[228.06,160.812]','[228.754382,159.484519]')
old="deleted={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d'}"
new="deleted={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d','7bb3c794-cbe6-40a7-abfb-5a3ab7df28ff'}"
assert old in code;code=code.replace(old,new);exec(compile(code,str(base),'exec'))
