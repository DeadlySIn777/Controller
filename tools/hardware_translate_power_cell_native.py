"""Translate one reviewed local converter cell on a full-board COPY only."""
from pathlib import Path
import argparse,json,hashlib,collections,shutil,subprocess
import pcbnew
from hardware_route_logic_return import identity,pad_identity
ROOT=Path(__file__).resolve().parents[1]
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mm(v):return pcbnew.ToMM(v)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--donor-receipt',type=Path,required=True);ap.add_argument('--recipes',type=Path,required=True);ap.add_argument('--group',required=True);ap.add_argument('--dx',type=float,required=True);ap.add_argument('--dy',type=float,default=0);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert not a.out.exists()and a.out.resolve().is_relative_to(ROOT/'reports');a.out.mkdir(parents=True);digest=sha(a.board);tool=sha(Path(__file__));r=json.loads(a.donor_receipt.read_text());groups=json.loads(a.recipes.read_text())['groups'];scope=set(groups[a.group]);assert a.group=='MC_1V2'and len(scope)==8
    b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();count=b.GetConnectivity().GetUnconnectedCount(False);fs={f.GetReference():f for f in b.GetFootprints()};old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),pad_identity(p))for p in b.GetPads()};delta=pcbnew.VECTOR2I(pcbnew.FromMM(a.dx),pcbnew.FromMM(a.dy))
    # Ownership is the frozen source's exact cell envelope, and only donor-
    # declared new objects qualify. No parent copper is selected geometrically.
    bounds=(5.815,5.675,19.325,20.5)
    # Three actual output-distribution vias extend to y20.6, beyond the
    # return-zone polygon. Include their exact short feed; zone bounds never
    # define a regulator's complete copper ownership by themselves.
    def inside(p):return bounds[0]-.001<=p[0]<=bounds[2]+.001 and bounds[1]-.001<=p[1]<=21.5
    declared={x['uuid']:x for x in r['added_copper']};track_ids={uid for uid,x in declared.items()if inside([v/1e6 for v in x['identity'][2]])and inside([v/1e6 for v in x['identity'][3]])};zone_ids={x['uuid']for x in r['added_zones']if x['polygon_mm']==[[bounds[0],bounds[1]],[bounds[2],bounds[1]],[bounds[2],bounds[3]],[bounds[0],bounds[3]]]}
    assert len(zone_ids)==2 and track_ids
    moved=[]
    for ref in sorted(scope):
        f=fs[ref];before=[mm(f.GetPosition().x),mm(f.GetPosition().y),f.GetOrientationDegrees()];f.SetPosition(f.GetPosition()+delta);moved.append(dict(ref=ref,before_mm=before,after_mm=[mm(f.GetPosition().x),mm(f.GetPosition().y),f.GetOrientationDegrees()]))
    actual_tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};assert track_ids<=set(actual_tracks)
    free_vias=[]
    for uid in sorted(track_ids):
        t=actual_tracks[uid];assert json.loads(json.dumps(identity(t)))==declared[uid]['identity'],'Reviewed owned copper changed '+uid
        if isinstance(t,pcbnew.PCB_VIA):free_vias.append(dict(uuid=uid,before=t.GetIsFree(),after=True));t.SetIsFree(True);t.SetPosition(t.GetPosition()+delta)
        else:t.SetStart(t.GetStart()+delta);t.SetEnd(t.GetEnd()+delta)
    actual_zones={z.m_Uuid.AsString():z for z in b.Zones()};assert zone_ids<=set(actual_zones)
    for uid in zone_ids:actual_zones[uid].Move(delta)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());dest=a.out/'power-cell-translated-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
    for suffix in ['.kicad_pro','.kicad_dru']:
        if a.board.with_suffix(suffix).exists():shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    (a.out/'fp-lib-table').write_text((a.board.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
    run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');(a.out/'drc.txt').write_text(run.stdout+run.stderr);assert run.returncode==0
    final=pcbnew.LoadBoard(str(dest));final.BuildConnectivity();after={t.m_Uuid.AsString():identity(t)for t in final.GetTracks()};assert set(after)==set(old)
    assert all(after[uid]==x for uid,x in old.items()if uid not in track_ids),'Unrelated copper changed'
    assert all(after[uid][1]==old[uid][1]for uid in track_ids),'Owned copper net changed during native refill'
    final_by_uuid={t.m_Uuid.AsString():t for t in final.GetTracks()};assert all(final_by_uuid[x['uuid']].GetIsFree()for x in free_vias),'Owned via automatic-net-reassignment flag was not retained'
    for p in final.GetPads():
        ref,ident=oldpads[p.m_Uuid.AsString()]
        if ref not in scope:assert pad_identity(p)==ident,'Unrelated actual pad changed'
        else:
            was=next(q for q in fs[ref].Pads()if q.m_Uuid.AsString()==p.m_Uuid.AsString());assert p.GetNetname()==was.GetNetname()and p.GetNumber()==was.GetNumber()and p.GetSize()==was.GetSize()and p.GetShape()==was.GetShape()
    assert len(list(final.GetFootprints()))==len(fs)and sha(a.board)==digest and sha(Path(__file__))==tool
    drc=json.loads((a.out/'drc.json').read_text());assert not drc.get('ignored_checks')
    result=dict(source_board=str(a.board),source_board_sha256=digest,source_unchanged=True,source_tool_sha256=tool,footprints=len(fs),scope=sorted(scope),poses=moved,moved_exact_owned_copper=[dict(uuid=uid,before=old[uid],after=after[uid])for uid in sorted(track_ids)],moved_exact_owned_zone_uuids=sorted(zone_ids),exact_owned_via_net_auto_reassignment_disabled=free_vias,all_unrelated_actual_pads_and_copper_unchanged=True,native_drc_types=dict(collections.Counter(x['type']for x in drc['violations'])),native_drc_error_count=sum(x['severity']=='error'for x in drc['violations']),uncapped_unconnected_before=count,uncapped_unconnected_after=final.GetConnectivity().GetUnconnectedCount(False),board_sha256=sha(dest),source_native_component_replacement=False,physical_power_delivery_qualified=False,manufacturing_ready=False)
    (a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['poses','moved_exact_owned_copper']}))
if __name__=='__main__':main()
