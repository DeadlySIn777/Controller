"""Current source26 exact112 review; frozen source24/25 reviews remain history."""
import argparse
from pathlib import Path
import hardware_build_ordinary_route_manifest_r02 as prior
ROOT=prior.ROOT

def review(source,adoption):
 r=prior.review(source,adoption)
 accepted=prior.baseline.load(adoption)
 if len(accepted.get('exact_component_changes',[]))!=5 or not accepted.get('actual_live_dependency_hashes_pass'):
  raise ValueError('Exact independently adopted source26 qualification required')
 r.update(electrical_review='source26 exact112 ordinary digital functions',
   source_revision='source26-2688-reference-fuse-qualification',
   prior_frozen_source25_tool_sha256=prior.baseline.sha(Path(prior.__file__)))
 r['source_review_sha256'][str(Path(__file__).resolve())]=prior.baseline.sha(__file__)
 return r

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ('source','adoption','out'):ap.add_argument('--'+n,type=Path,required=True)
 a=ap.parse_args();a.out=a.out.resolve();assert not a.out.exists()and a.out.is_relative_to(ROOT/'reports');a.out.mkdir(parents=True)
 r=review(a.source,a.adoption);prior.baseline.write(a.out/'ordinary-source-review.json',r)
 prior.baseline.write(a.out/'receipt.json',dict(passed=True,exact_ordinary_nets=112,excluded_nets=len(r['excluded_nets']),
  source_review_sha256=prior.baseline.sha(a.out/'ordinary-source-review.json'),tool_sha256=prior.baseline.sha(__file__),
  old_source24_source25_reviews_and_tools_unchanged=True,actual_routing_run=False,manufacturing_ready=False))
 print(dict(exact_ordinary_nets=112,source_revision=r['source_revision']))

if __name__=='__main__':main()
