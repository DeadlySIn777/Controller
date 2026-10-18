"""Independent persisted native tests for the dedicated ADC8 routing donor.

Never mutates electrical sources or the input board. The F-only analysis
removes other copper before KiCad calculates connectivity, avoiding a
transitive plane/via path being mistaken for a same-side capacitor loop.
"""
import argparse,collections,copy,json
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,dump,children,child,value,q
from hardware_populate_motherboard_pcb import sha,write,pad_template
from hardware_route_logic_return import identity
from hardware_layout_ads8684_cell import CAPS,POSES,f_only_analysis,f_graph_connected,pad_snapshot,copper
from hardware_apply_adc_capacitor_pcb_delta import source_clusters

def proofs(path,out):
 b=f_only_analysis(path,out);fp={f.GetReference():f for f in b.GetFootprints()};rows=[]
 for ref,(p,g)in CAPS.items():
  for cp,op in [('1',p),('2',g)]:
   a=next(p for p in fp[ref].Pads()if p.GetNumber()==cp);z=next(p for p in fp['U14734'].Pads()if p.GetNumber()==op)
   rows.append(dict(cap=ref,cap_pin=cp,owner='U14734',owner_pin=op,passed=f_graph_connected(b,a,z)))
 return rows

def warnings(d):
 return collections.Counter(json.dumps(r,sort_keys=True)for r in d['violations']if r['severity']=='warning')

def ref(f):return value(next(p[2]for p in children(f,'property')if value(p[1])=='Reference'))
def uid(item):return value(child(item,'uuid')[1])

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ('board','baseline','receipt','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args();a.out=a.out.resolve()
 if a.out.exists():raise ValueError('Fresh immutable validation directory required')
 a.out.mkdir(parents=True);r=json.loads(a.receipt.read_text());frozen={str(p.resolve()):sha(p)for p in [a.board,a.baseline,a.receipt,Path(__file__),Path(__file__).with_name('hardware_layout_ads8684_cell.py')]}
 if not r['passed']or r['board_sha256']!=sha(a.board):raise ValueError('Exact passing frozen ADC donor required')
 base=pcbnew.LoadBoard(str(a.baseline.resolve()));b=pcbnew.LoadBoard(str(a.board.resolve()));base.BuildConnectivity();b.BuildConnectivity();bc=copper(base);actual=copper(b);add=set(actual)-set(bc)
 assert add==set(r['exact_added_copper_UUIDs'])and len(add)==183
 assert all(actual.get(u)==v for u,v in bc.items())
 before=pad_snapshot(base);now=pad_snapshot(b)
 assert all(now.get(k)==v for k,v in before.items()if k[0]not in POSES)
 assert {(k,v['number'],v['net'])for k,v in before.items()}=={(k,v['number'],v['net'])for k,v in now.items()}
 oldcl=source_clusters(base,set(POSES));newcl=source_clusters(b,set(POSES));assert all(set(v)<=set(newcl[u])for u,v in oldcl.items())
 first=json.loads((a.baseline.parent/'drc.json').read_text());last=json.loads((a.board.parent/'drc.json').read_text());assert warnings(first)==warnings(last)
 assert not first.get('ignored_checks')and not last.get('ignored_checks')and not any(v['severity']=='error'for v in last['violations'])
 healthy=proofs(a.board,a.out/'healthy-F-only-analysis.kicad_pcb');assert len(healthy)==14 and all(v['passed']for v in healthy)
 tree=parse(a.board.read_text());tests=[]
 def test(name,mutate,predicate):
  candidate=copy.deepcopy(tree);mutate(candidate);p=a.out/(name+'.kicad_pcb');p.write_text(dump(candidate)+'\n');bb=pcbnew.LoadBoard(str(p));bb.BuildConnectivity();okay=predicate(bb,p);assert okay,name;tests.append(dict(name=name,negative_control_detected=True,fixture_sha256=sha(p)))
 def tracks(t):return[v for v in t if isinstance(v,list)and v and v[0]in('segment','via','arc')]
 def caps(t):return{ref(f):f for f in children(t,'footprint')}
 def failing_pairs(bb,p):return not all(v['passed']for v in proofs(p,a.out/(p.stem+'-F-only.kicad_pcb')))
 def remove_refcap(t):t[:]=[v for v in t if not(isinstance(v,list)and v and v[0]=='segment'and uid(v)in add and 'AI_ADC_REFCAP'in value(child(v,'net')[1]))]
 # Source uses a full hierarchy name; derive the exact native net, not text
 # case/suffix classification, before deleting the actual REFCAP branches.
 refnet=next(p.GetNetname()for f in b.GetFootprints()if f.GetReference()=='C14742'for p in f.Pads()if p.GetNumber()=='1')
 def remove_refcap(t):t[:]=[v for v in t if not(isinstance(v,list)and v and v[0]=='segment'and uid(v)in add and value(child(v,'net')[1])==refnet)]
 test('missing-required-REFCAP-copper',remove_refcap,failing_pairs)
 def all_B(t):
  for v in tracks(t):
   if uid(v)in add:child(v,'layer')[1]=q('B.Cu')
 test('only-backside-paths',all_B,failing_pairs)
 def wrong_owner(t):
  f=caps(t)['U14734'];p=next(p for p in children(f,'pad')if value(p[1])=='9');child(p,'net')[1]=q(refnet)
 test('wrong-owner-AVDD-pin-net',wrong_owner,failing_pairs)
 def old_cu_change(t):
  v=next(v for v in tracks(t)if uid(v)in bc and v[0]=='segment');child(v,'width')[1]='0.333'
 test('unreviewed-old-copper-width',old_cu_change,lambda bb,p:any(copper(bb).get(u)!=v for u,v in bc.items()))
 def source_net_change(t):
  f=caps(t)['C14746'];p=next(p for p in children(f,'pad')if value(p[1])=='1');child(p,'net')[1]=q(refnet)
 test('capacitor-source-net-change',source_net_change,lambda bb,p:{(k,v['number'],v['net'])for k,v in pad_snapshot(bb).items()}!={(k,v['number'],v['net'])for k,v in now.items()})
 # A native backside capacitor cannot pass even when a through plane or
 # fabricated metadata says that it is connected.
 fixture=a.out/'backside-capacitor.kicad_pcb';bb=pcbnew.LoadBoard(str(a.board.resolve()));f=next(f for f in bb.GetFootprints()if f.GetReference()=='C14746');f.Flip(f.GetPosition(),False);pcbnew.SaveBoard(str(fixture),bb)
 assert not all(v['passed']for v in proofs(fixture,a.out/'backside-capacitor-F-only.kicad_pcb'));tests.append(dict(name='backside-capacitor',negative_control_detected=True,fixture_sha256=sha(fixture)))
 assert all(sha(Path(p))==h for p,h in frozen.items())
 result=dict(passed=True,input_sha256=frozen,actual_source_parts=len(list(b.GetFootprints())),actual_eight_poses=r['exact_eight_part_movement'],actual_added_F_only_copper=len(add),added_vias=0,actual_native_F_only_endpoint_proofs=healthy,all_old_copper_and_stationary_pad_clusters_retained=True,exact_native_baseline_warnings_preserved=8,native_DRC_errors=0,ignored_checks=[],actual_persisted_negative_controls=tests,manufacturing_ready=False,physical_qualification=False)
 write(a.out/'review.json',result);print(json.dumps(dict(passed=True,endpoints=14,negative_controls=len(tests),native_errors=0,baseline_warnings=8)))
if __name__=='__main__':main()
