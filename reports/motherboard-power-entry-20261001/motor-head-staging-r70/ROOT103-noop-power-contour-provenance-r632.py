"""No-op native refill on a copy; identify inherited/native contour provenance."""
import sys,json,hashlib,shutil,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_route_logic_return import identity,pad_identity
B=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb');H=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py');O=Path('reports/motherboard-power-entry-20261001/ROOT103-noop-power-contour-provenance-r632');assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p)for p in[B,H,Path(__file__)]};spec=importlib.util.spec_from_file_location('r07',H);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
dest=O/'motherboard-ROOT103-noop-refilled-candidate.kicad_pcb';shutil.copyfile(B,dest)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
b=pcbnew.LoadBoard(str(B));a=pcbnew.LoadBoard(str(dest));print('NOOP_REFILL_START',flush=True);pcbnew.ZONE_FILLER(a).Fill(a.Zones());pcbnew.SaveBoard(str(dest),a);a=pcbnew.LoadBoard(str(dest));print('NOOP_REFILL_DONE',flush=True)
assert{t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}=={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()};assert{p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in a.GetPads()}
bf=collect_native_reference_fills(b,{'/IO_3V3','/CORE_1V2'},[pcbnew.In2_Cu,pcbnew.In3_Cu]);af=collect_native_reference_fills(a,{'/IO_3V3','/CORE_1V2'},[pcbnew.In2_Cu,pcbnew.In3_Cu]);region=m.box(353.8,189.0,354.8,189.9);local=m.subtract(m.intersection(bf['/IO_3V3',pcbnew.In2_Cu],region),m.intersection(af['/IO_3V3',pcbnew.In2_Cu],region))
try:power=m.review(b,a)
except Exception as e:power=dict(passed=False,rejection=repr(e))
assert all(sha(Path(p))==h for p,h in inputs.items());(O/'review.json').write_text(json.dumps(dict(input_hashes=inputs,board_sha256=sha(dest),exact_all_pads_Cu_poses_unchanged=True,local_far_B_gap_after_noop_refill_area_mm2=local.Area()/1e12,local_far_B_gap_after_noop_refill=local.Format(False),frozen_r07_power=power,no_Source_or_original_PCB_mutation=True,no_narrow_feature_exemption=True,manufacturing_ready=False),indent=2));print('NOOP_POWER',power.get('passed'),local.Area()/1e12,power.get('rejection'),flush=True)
