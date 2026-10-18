"""Actual persisted native baseline and new-warning gates; explicit toy only."""
from pathlib import Path
import json,sys,shutil,hashlib
import pcbnew
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import hardware_route_critical_digital_wip_r03 as h
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'reports/motherboard-owned-bypass-routing-20261001/wip-r03-warning-fixture-preparation-r03/fixture.kicad_pcb'
LEDGER=SOURCE.parent/'baseline-disposition.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
 d=OUT/'native';d.mkdir(exist_ok=False);base=h.prior.copy_board_inputs(SOURCE,d)
 manifest=OUT/'fixture-manifest.json';h.prior.write(manifest,dict(board_sha256=sha(SOURCE),production_motherboard=False))
 h.configure(LEDGER,manifest)
 positive=h.prior.native_drc(base,OUT,'exact-old-warning-native',refill=False)
 assert positive['regular_violations']==1 and not positive['complete_board_DRC_pass']
 b=pcbnew.LoadBoard(str(base));before=h.source_clusters(b)
 net=b.FindNet('/IO_3V3')
 def xy(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
 for a,c in [((15,3.5),(17,3.5)),((17,3.5),(17,2))]:
  t=pcbnew.PCB_TRACK(b);t.SetNet(net);t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(.35));t.SetStart(xy(*a));t.SetEnd(xy(*c));b.Add(t)
 v=pcbnew.PCB_VIA(b);v.SetNet(net);v.SetPosition(xy(17,2));v.SetWidth(pcbnew.FromMM(.6));v.SetDrill(pcbnew.FromMM(.3));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
 candidate=OUT/'actual-added-unfinished-feed.kicad_pcb';pcbnew.SaveBoard(str(candidate),b)
 for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(base.with_suffix(suffix),candidate.with_suffix(suffix))
 try:h.prior.native_drc(candidate,OUT,'actual-new-warning-native',refill=True)
 except ValueError as error:reason=str(error)
 else:raise AssertionError('Actual new native warning escaped the exact ledger')
 report=h.prior.read(OUT/'actual-new-warning-native.json')
 assert len(report['violations'])==2 and not report.get('ignored_checks')
 assert all(x['type']=='via_dangling'and x['severity']=='warning'for x in report['violations'])
 clusters=h.clusters_preserved(before,pcbnew.LoadBoard(str(candidate)))
 frozen=[Path(__file__),Path(h.__file__),Path(h.wip.__file__),SOURCE,LEDGER,ROOT/'tests/test_motherboard_critical_wip_routing.py']
 r=dict(passed=True,production_motherboard=False,actual_baseline_warning_retained=positive,
  actual_new_warning_rejected=True,actual_new_warning_rejection=reason,
  full_native_JSON_retained=True,native_new_warning_objects=report['violations'],
  actual_native_source_cluster_preservation=clusters,
  baseline_board_sha256=sha(base),rejected_candidate_sha256=sha(candidate),
  frozen_inputs={str(p):sha(p)for p in frozen},manufacturing_ready=False)
 (OUT/'review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,actual_baseline_warnings=1,actual_new_candidate_warnings=2,actual_added_warning_rejected=True)))
if __name__=='__main__':run()
