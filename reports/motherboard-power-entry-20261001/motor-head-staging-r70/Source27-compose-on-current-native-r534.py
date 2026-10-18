"""Compose ONLY the frozen exact Source27 reset delta onto the separate current BankB transaction."""
import sys,json,shutil,hashlib,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_populate_motherboard_pcb import pad_template
BEFORE=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb')
DONOR=Path('reports/motherboard-power-entry-20261001/Source27-reset-native-proof-r526/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb')
TARGET=Path('reports/motherboard-power-entry-20261001/ROOT103-BankB-physical-stage-r532/motherboard-bounded-merged-candidate.kicad_pcb')
RECEIPT=DONOR.with_name('receipt.json');OUT=Path('reports/motherboard-power-entry-20261001/Source27-on-ROOT103-plus-BankB-r534');assert not OUT.exists();OUT.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
frozen={str(p):sha(p)for p in[BEFORE,DONOR,TARGET,RECEIPT,Path(__file__),Path('hardware/motherboard/design.json')]};r=json.loads(RECEIPT.read_text());assert r['passed']and r['board_sha256']==sha(DONOR);old=pcbnew.LoadBoard(str(BEFORE));donor=pcbnew.LoadBoard(str(DONOR));target=pcbnew.LoadBoard(str(TARGET));of={f.GetReference():f for f in old.GetFootprints()};df={f.GetReference():f for f in donor.GetFootprints()};tf={f.GetReference():f for f in target.GetFootprints()};assert set(of)==set(tf)and len(tf)==2688;newrefs=set(df)-set(of);assert newrefs==set(r['exact_ten_new_refs']);newset=set(r['exact_new_Cu']);ret=set(r['exact_retired_Cu']);oc={t.m_Uuid.AsString():identity(t)for t in old.GetTracks()};tc={t.m_Uuid.AsString():identity(t)for t in target.GetTracks()};dc={t.m_Uuid.AsString():t for t in donor.GetTracks()};beforepads={p.m_Uuid.AsString():pad_identity(p)for p in target.GetPads()};beforeposes={z:(mm(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())for z,f in tf.items()};beforevalues={z:f.GetValue()for z,f in tf.items()};values=set(r['exact_old_value_update_refs']);remaps={(x['ref'],x['pin']):x for x in r['exact_old_two_pin_remaps']}
for z in values:assert tf[z].GetValue()==of[z].GetValue(),('Concurrent source value',z)
for t in list(target.GetTracks()):
 u=t.m_Uuid.AsString()
 if u in ret:assert tc[u]==oc[u],('Concurrent old CLR copper',u);target.Remove(t)
assert not(newset&set(tc))
def net(name):
 n=target.FindNet(name)
 if n is None or n.GetNetname()!=name:
  n=pcbnew.NETINFO_ITEM(target,name);target.Add(n)
 return n
for z in values:tf[z].SetValue(df[z].GetValue())
for (z,pn),change in remaps.items():
 p=next(p for p in tf[z].Pads()if p.GetNumber()==pn);assert p.GetNetname()==change['before']and p.m_Uuid.AsString()==change['pad_uuid'];p.SetNet(net(change['after']))
for z in sorted(newrefs):
 f=pcbnew.FOOTPRINT(df[z]);target.Add(f)
 for p in f.Pads():
  source=next(q for q in df[z].Pads()if q.m_Uuid.AsString()==p.m_Uuid.AsString());p.SetNet(net(source.GetNetname()))
for u in sorted(newset):
 t=dc[u];q=pcbnew.PCB_VIA(t)if isinstance(t,pcbnew.PCB_VIA)else pcbnew.PCB_TRACK(t);q.SetNet(net(t.GetNetname()));target.Add(q);assert identity(q)==identity(t),('Literal Source27 Cu',u)
dest=OUT/'motherboard-current-Source27-reset-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),target)
for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(TARGET.with_suffix(ext),dest.with_suffix(ext))
for p in TARGET.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,OUT/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,OUT/p.name)
# Add exactly the already frozen manufacturer DBV library row, preserving target context.
from hardware_build_assembly import parse,children,value,dump
from hardware_merge_bounded_pcb_delta import dump_board
ft=parse((OUT/'fp-lib-table').read_text());dt=parse((DONOR.parent/'fp-lib-table').read_text());entry=next(v for v in children(dt,'lib')if value(next(p[1]for p in children(v,'name')))=='CNC_MB_FeedReset');assert not any(value(next(p[1]for p in children(v,'name')))=='CNC_MB_FeedReset'for v in children(ft,'lib'));ft.append(entry);(OUT/'fp-lib-table').write_text(dump_board(ft))
fresh=pcbnew.LoadBoard(str(dest));ff={f.GetReference():f for f in fresh.GetFootprints()};fc={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()};assert set(ff)==set(df)and len(ff)==2698;assert set(tc)-set(fc)==ret and set(fc)-set(tc)==newset;assert all(fc[u]==v for u,v in tc.items()if u not in ret);assert all(fc[u]==identity(dc[u])for u in newset)
fp={p.m_Uuid.AsString():p for p in fresh.GetPads()}
for u,v in beforepads.items():
 if u in{q['pad_uuid']for q in remaps.values()}:continue
 assert pad_identity(fp[u])==v,('Unrelated current pad changed',u)
for z,v in beforeposes.items():assert(mm(ff[z].GetPosition()),ff[z].GetOrientationDegrees(),ff[z].GetLayer())==v
for z,v in beforevalues.items():assert ff[z].GetValue()==(df[z].GetValue()if z in values else v)
assert all(sha(Path(p))==h for p,h in frozen.items());out=dict(input_hashes=frozen,unfilled_board_sha256=sha(dest),current_source_physical=2698,separate_BankB_transaction_retained=True,exact_new_parts=sorted(newrefs),exact_five_value_updates=sorted(values),exact_two_pin_remaps=list(remaps.values()),exact_232_new_Cu=sorted(newset),exact_seven_retired_old_CLR_Cu=sorted(ret),all_other_current_ROOT103_geometry_retained=True,native_Source_reference_power_current110_pending=True,Source27_adopted=False,manufacturing_ready=False);(OUT/'composition.json').write_text(json.dumps(out,indent=2));print('EXACT_COMPOSITION',len(ff),len(newset),len(ret),sha(dest),flush=True)
