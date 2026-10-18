"""Exact source25 ordinary digital review; preserve the frozen source24 tool.

Adds only 36 actual AHCT04 inverter-to-LVC07 digital input nodes. LED current
paths, buses, timing, analogue, precision and power remain excluded.
"""
import argparse,json
from pathlib import Path
import hardware_build_ordinary_route_manifest as baseline

ROOT=baseline.ROOT
def exact_review():
 rows=baseline_exact()
 for i in range(36):
  rows['/motherboard_status/OBS%d_INVERTED'%i]=dict(signal_class='status_logic',driver=('U%d'%(17001+2*(i//6)),str([2,4,6,8,10,12][i%6])),maximum_voltage_v=5.5)
 return rows
baseline_exact=baseline.exact_review

def review(source,adoption):
 source=Path(source).resolve();accepted=baseline.load(adoption)
 if not accepted.get('passed')or not accepted.get('adopted')or accepted.get('independent_validation_pass')is not True or accepted.get('native_ERC_errors')!=0 or accepted.get('ignored_checks')not in (0,[]):raise ValueError('Exact actual independently adopted source required')
 hashes=accepted.get('hashes')or accepted['source_hashes']
 for name,h in hashes.items():
  p=Path(name);p=p if p.is_absolute()else source/p
  if baseline.sha(p)!=h:raise ValueError('Actual adopted source changed: '+str(p))
 model=baseline.load(source/'design.json');nodes,nets,functions=baseline.native(model,source/'netlist.xml')
 for i in range(36):
  n='/motherboard_status/OBS%d_INVERTED'%i;odd='U%d'%(17001+2*(i//6));even='U%d'%(17002+2*(i//6));op=str([2,4,6,8,10,12][i%6]);ip=str([1,3,5,9,11,13][i%6])
  if nets.get(n)!=sorted([(odd,op),(even,ip)]):raise ValueError('Exact two status digital endpoints changed '+n)
  if model['components'][odd]['mpn']!='SN74AHCT04PWR'or model['components'][even]['mpn']!='74LVC07APW,118':raise ValueError('Actual status gate MPN changed '+n)
  if functions[odd][op]['type']!='output'or functions[even][ip]['type']!='input':raise ValueError('Actual inverter/sink input direction changed '+n)
  for u in [odd,even]:
   if nodes.get((u,'14'))!='/mc_local_power/CORE_5V'or nodes.get((u,'7'))!='/LOGIC_GND':raise ValueError('Actual status own rail/return changed '+u)
 baseline.exact_review=exact_review
 try:r=baseline.review(source,adoption)
 finally:baseline.exact_review=baseline_exact
 if len(r['nets'])!=112:raise ValueError('Exact112 digital function review required')
 r.update(electrical_review='source25 exact112 ordinary digital functions',prior_frozen_source24_tool_sha256=baseline.sha(Path(baseline.__file__)),actual_status_intermediate_nodes_added=36,additional_current_paths_promoted=0)
 r['source_review_sha256'][str(Path(__file__).resolve())]=baseline.sha(__file__)
 return r

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ('source','adoption','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args();a.out=a.out.resolve()
 if a.out.exists()or not a.out.is_relative_to(ROOT/'reports'):raise ValueError('Fresh report required')
 a.out.mkdir(parents=True);r=review(a.source,a.adoption);baseline.write(a.out/'ordinary-source-review.json',r)
 baseline.write(a.out/'receipt.json',dict(passed=True,exact_ordinary_nets=112,excluded_nets=len(r['excluded_nets']),source_review_sha256=baseline.sha(a.out/'ordinary-source-review.json'),tool_sha256=baseline.sha(__file__),old_source24_review_and_tool_unchanged=True,actual_routing_run=False,manufacturing_ready=False))
 print(json.dumps(dict(exact_ordinary_nets=112,excluded_nets=len(r['excluded_nets']),source_review_sha256=baseline.sha(a.out/'ordinary-source-review.json'))))
if __name__=='__main__':main()
