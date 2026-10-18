"""Literal Source27 delta: keep every current target pose/land/copper/zone except exact source changes."""
import sys,json,copy,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_build_assembly import parse,child,children,value,dump
from hardware_merge_bounded_pcb_delta import objects,reference,dump_board,without_generated_fills
BEFORE=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb');DONOR=Path('reports/motherboard-power-entry-20261001/Source27-reset-native-proof-r526/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');TARGET=Path('reports/motherboard-power-entry-20261001/ROOT103-BankB-physical-stage-r532/motherboard-bounded-merged-candidate.kicad_pcb');RECEIPT=DONOR.with_name('receipt.json');OUT=Path('reports/motherboard-power-entry-20261001/Source27-on-ROOT103-plus-BankB-r536');assert not OUT.exists();OUT.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
frozen={str(p):sha(p)for p in[BEFORE,DONOR,TARGET,RECEIPT,Path(__file__),Path('hardware/motherboard/design.json')]};r=json.loads(RECEIPT.read_text());assert r['passed']and r['board_sha256']==sha(DONOR);trees={k:parse(without_generated_fills(p.read_text()))for k,p in [('before',BEFORE),('donor',DONOR),('target',TARGET)]};fps={k:{reference(f):f for f in children(t,'footprint')}for k,t in trees.items()};assert set(fps['before'])==set(fps['target'])and len(fps['target'])==2688;newrefs=set(fps['donor'])-set(fps['before']);assert newrefs==set(r['exact_ten_new_refs']);newset=set(r['exact_new_Cu']);ret=set(r['exact_retired_Cu']);values=set(r['exact_old_value_update_refs']);remaps={(x['ref'],x['pin']):x for x in r['exact_old_two_pin_remaps']}
def prop(f,name):return next(p for p in children(f,'property')if value(p[1])==name)
for z in values:
 assert prop(fps['target'][z],'Value')[2]==prop(fps['before'][z],'Value')[2],('Concurrent Source value',z)
 prop(fps['target'][z],'Value')[2]=prop(fps['donor'][z],'Value')[2]
for (z,pn),change in remaps.items():
 p=next(p for p in children(fps['target'][z],'pad')if value(p[1])==pn);q=next(p for p in children(fps['donor'][z],'pad')if value(p[1])==pn);assert value(child(p,'uuid')[1])==change['pad_uuid']and value(child(p,'net')[-1])==change['before'];oldnet=child(p,'net');p[p.index(oldnet)]=copy.deepcopy(child(q,'net'))
for z in sorted(newrefs):trees['target'].append(copy.deepcopy(fps['donor'][z]))
for kind in ['segment','via','arc']:
 old=objects(trees['before'],kind);donor=objects(trees['donor'],kind);target=objects(trees['target'],kind)
 for u in ret&set(old):assert u in target and dump(old[u])==dump(target[u]),('Concurrent old CLR Cu',u);trees['target'].remove(target[u])
 for u in newset&set(donor):assert u not in target;trees['target'].append(copy.deepcopy(donor[u]))
dest=OUT/'motherboard-current-Source27-reset-candidate.kicad_pcb';dest.write_text(dump_board(trees['target']))
for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(TARGET.with_suffix(ext),dest.with_suffix(ext))
for p in TARGET.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,OUT/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,OUT/p.name)
ft=parse((OUT/'fp-lib-table').read_text());dt=parse((DONOR.parent/'fp-lib-table').read_text());entry=next(v for v in children(dt,'lib')if value(child(v,'name')[1])=='CNC_MB_FeedReset');assert not any(value(child(v,'name')[1])=='CNC_MB_FeedReset'for v in children(ft,'lib'));ft.append(copy.deepcopy(entry));(OUT/'fp-lib-table').write_text(dump_board(ft))
print('LITERAL_WRITTEN',flush=True)
b=pcbnew.LoadBoard(str(TARGET));a=pcbnew.LoadBoard(str(dest));d=pcbnew.LoadBoard(str(DONOR));bf={f.GetReference():f for f in b.GetFootprints()};af={f.GetReference():f for f in a.GetFootprints()};df={f.GetReference():f for f in d.GetFootprints()};bp={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};ap={p.m_Uuid.AsString():p for p in a.GetPads()};bc={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};ac={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()};dc={t.m_Uuid.AsString():identity(t)for t in d.GetTracks()};assert len(af)==2698 and set(af)==set(df);assert set(bc)-set(ac)==ret and set(ac)-set(bc)==newset;assert all(ac[u]==v for u,v in bc.items()if u not in ret);assert all(ac[u]==dc[u]for u in newset)
for u,v in bp.items():
 if u in{q['pad_uuid']for q in remaps.values()}:continue
 assert pad_identity(ap[u])==v,('Unrelated current Source pad',u)
for z,f in bf.items():
 assert(mm(af[z].GetPosition()),af[z].GetOrientationDegrees(),af[z].GetLayer())==(mm(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer());assert af[z].GetValue()==(df[z].GetValue()if z in values else f.GetValue())
assert all(sha(Path(p))==h for p,h in frozen.items());out=dict(input_hashes=frozen,unfilled_board_sha256=sha(dest),current_source_physical=2698,separate_BankB_transaction_retained=True,exact_new_parts=sorted(newrefs),exact_five_value_updates=sorted(values),exact_two_pin_remaps=list(remaps.values()),exact_232_new_Cu=sorted(newset),exact_seven_retired_old_CLR_Cu=sorted(ret),all_other_current_ROOT103_geometry_retained=True,native_Source_reference_power_current110_pending=True,Source27_adopted=False,manufacturing_ready=False);(OUT/'composition.json').write_text(json.dumps(out,indent=2));print('EXACT_COMPOSITION',len(af),len(newset),len(ret),sha(dest),flush=True)
