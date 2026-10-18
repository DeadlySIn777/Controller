"""Frozen strict HF router with exact nonempty native reference collection only."""
from pathlib import Path
import hashlib,json,sys
import hardware_route_owned_bypass_loops_r02 as prior
import hardware_check_return_corridors_r03 as fast
FROZEN_HF_R02_SHA='fed0e0a574d61ceb38494b7896f3912705017221ce17af7ac387ee2bf2ac73bb'
def main():
 if hashlib.sha256(Path(prior.__file__).read_bytes()).hexdigest()!=FROZEN_HF_R02_SHA:
  raise ValueError('Frozen strict HF wrapper changed')
 deps=fast.dependencies()
 # These are runtime-only substitutions; no prior file or proof is rewritten.
 prior.strict.return_corridor_check=fast.return_corridor_check
 prior.prior.ReturnCheck=fast.NativeCollectedAnnulusCheck
 prior.main()
 out=Path(sys.argv[sys.argv.index('--out')+1]).resolve();p=out/'receipt.json'
 r=json.loads(p.read_text());r.update(router_version='r03 exact native nonempty fill collector',
  exact_native_nonempty_fill_dependencies=deps,strict_HF_r02_sha256=FROZEN_HF_R02_SHA,
  no_approximate_polygon_union=True)
 r['tool_sha256'].update({str(x):hashlib.sha256(x.read_bytes()).hexdigest()for x in [Path(__file__),Path(fast.__file__),Path(fast.collector.__file__)]})
 p.write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()
