"""Unadopted source-exact BGA neck rule: effective .20 minimum elsewhere.

KiCad's absolute minimum cannot be overridden. The candidate absolute .15
minimum is therefore paired with an explicit .20 Track/Arc rule, then an
exact F-only/assigned-net/whole-area/short-segment neck exception. Native
adversarial controls must reject power, other nets, outside, B and long necks.
This is a conditional factory DFM candidate, not a 2oz manufacture approval.
"""
from pathlib import Path
import argparse,json,copy,math,subprocess,urllib.request
import pcbnew
import hardware_route_selected_additive_r02 as e
import hardware_audit_fpga_package_access as access

AREA='U1001_LITERAL_SIGNAL_NECKS'
def proposed_rules(names):
 cond=" || ".join("A.NetName == '"+n+"'"for n in sorted(names))
 return ('\n# Maintain the previous effective .20 minimum everywhere outside exact necks.\n'
  '(rule "Effective general track minimum remains .20" (condition "A.Type == \'Track\' || A.Type == \'Arc\'") (constraint track_width (min 0.20mm)))\n'
  '(rule "U1001 exact assigned F signal necks only" (layer "F.Cu")\n'
  ' (condition "A.Type == \'Track\' && A.Width < 0.20mm && A.enclosedByArea(\''+AREA+'\') && ('+cond+')")\n'
  ' (constraint track_width (min 0.15mm) (max 0.15mm))\n'
  ' (constraint track_segment_length (max 1.0mm)))\n')

def native_case(base,mode,out,names):
 out.mkdir();b=pcbnew.LoadBoard(str(base));fp=next(f for f in b.GetFootprints()if f.GetReference()=='U1001');pads={p.GetNumber():p for p in fp.Pads()}
 pad=pads['M9'];net=pad.GetNetname();start=pcbnew.ToMM(pad.GetPosition());stop=(start[0]+.4,start[1]+.4);layer=pcbnew.F_Cu
 if mode=='power':net='/LOGIC_GND';start=(96,42);stop=(96.4,42.4)
 if mode=='wrong_net':net=pads['T2'].GetNetname();start=(96,42);stop=(96.4,42.4)
 if mode=='outside':start=(86,40);stop=(86.4,40.4)
 if mode=='B_side':layer=pcbnew.B_Cu
 if mode=='overlength':start=(96,42);stop=(98,42)
 access.track(b,net,start,stop,layer,.15)
 z=pcbnew.ZONE(b);z.SetIsRuleArea(True);z.SetZoneName(AREA);z.SetLayer(pcbnew.F_Cu);z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowZoneFills(False);z.SetDoNotAllowFootprints(False)
 polygon=z.Outline();polygon.NewOutline()
 for xy in [(92,36),(108,36),(108,52),(92,52)]:polygon.Append(access.point(xy))
 b.Add(z);path=out/'native-rule-case.kicad_pcb';pcbnew.SaveBoard(str(path),b)
 project=json.loads(base.with_suffix('.kicad_pro').read_text());project['board']['design_settings']['rules']['min_track_width']=.15;path.with_suffix('.kicad_pro').write_text(json.dumps(project))
 path.with_suffix('.kicad_dru').write_text(base.with_suffix('.kicad_dru').read_text()+proposed_rules(names))
 report=out/'native.json';run=subprocess.run([str(e.CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','-o',str(report),str(path)],capture_output=True,text=True,encoding='utf8',errors='replace');(out/'native.txt').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Native scoped neck-rule did not execute')
 r=json.loads(report.read_text());errors=[v for v in r['violations']if v['severity']=='error'];width=[v for v in errors if v['type']=='track_width'];length=[v for v in errors if v['type']=='track_segment_length']
 return dict(mode=mode,errors=errors,width_errors=width,length_errors=length,all_warnings=[v for v in r['violations']if v['severity']=='warning'],no_ignored_checks=not r.get('ignored_checks'),case_sha256=e.sha(path))

def review(board_path,out):
 out=e.require_new_report(out);b=pcbnew.LoadBoard(str(board_path));_,nodes=e.native_source_check(b,e.read(e.ROOT/'hardware/motherboard/design.json'),e.ROOT/'hardware/motherboard/netlist.xml')
 source=e.read(e.ROOT/'reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
 fp=next(f for f in b.GetFootprints()if f.GetReference()=='U1001');names={p.GetNetname()for p in fp.Pads()if p.GetNetname()in source['nets']}
 if len(names)!=38 or any(n in {'/LOGIC_GND','/CORE_1V2','/IO_3V3'}for n in names):raise ValueError('Literal current critical signal scope changed')
 e.write(out/'assigned-source-manifest.json',dict(board_sha256=e.sha(board_path),source_design_sha256=e.sha(e.ROOT/'hardware/motherboard/design.json'),source_netlist_sha256=e.sha(e.ROOT/'hardware/motherboard/netlist.xml'),nets={n:nodes[n]for n in sorted(names)},absolute_minimum_candidate_mm=.15,effective_general_minimum_mm=.2,F_only=True,area_bounds_mm=[92,36,108,52],maximum_native_track_segment_length_mm=1.0,aggregate_neck_length_still_requires_executor_check=True,manufacturing_ready=False))
 # Only text primary-source material is retained. Generic aggregate capability
 # rows must not be used to claim a simultaneous 70um/.15mm process guarantee.
 sources=[]
 for name,url in [('pcbway-capabilities.html','https://www.pcbway.com/capabilities.html'),('kicad10-rules.html','https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html')]:
  path=out/name;path.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read());sources.append(dict(url=url,sha256=e.sha(path),retrieved='2026-10-01'))
 # Reuse the actual copied-package current-rule healthy base; no live mutation.
 base=e.ROOT/'reports/motherboard-critical-routing-20261001/source26-BGA-native-access-r03/sparse_outer/actual-F256-package-access.kicad_pcb'
 cases=[native_case(base,mode,out/mode,names)for mode in ['healthy','power','wrong_net','outside','B_side','overlength']]
 passed=not cases[0]['errors']and all(c['no_ignored_checks']for c in cases)and all(c['width_errors']for c in cases[1:5])and cases[5]['length_errors']
 r=dict(passed=bool(passed),tool_sha256=e.sha(__file__),source_manifest_sha256=e.sha(out/'assigned-source-manifest.json'),primary_sources=sources,cases=cases,
  primary_70um_outer_normal_width_space_mm=[.1778,.2032],primary_70um_outer_medium_width_space_mm=[.1524,.1778],candidate_width_space_mm=[.15,.15],simultaneous_2oz_process_guaranteed=False,
  factory_review_and_quote_required=True,actual_parent_rule_changed=False,reference_checker_changed=False,manufacturing_ready=False)
 e.write(out/'review.json',r);return r
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=review(a.board,a.out);print(json.dumps({'passed':r['passed'],'cases':[{k:c[k]for k in ['mode','no_ignored_checks']}|{'errors':len(c['errors'])}for c in r['cases']],'actual_parent_rule_changed':False}))
if __name__=='__main__':main()
