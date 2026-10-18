"""Retire only old native-dangling moved entry leaves; preserve every observer."""
from pathlib import Path
import argparse,collections,hashlib,json,re,shutil,subprocess
import pcbnew
from hardware_route_logic_return import identity,pad_identity
from hardware_build_assembly import parse,dump,child,value
ROOT=Path(__file__).resolve().parents[1]
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--route-receipt',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);digest=sha(a.board);b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();rr=json.loads(a.route_receipt.read_text());assert rr['candidate_sha256']==digest;new={r['uuid']for r in rr['exact_added_copper']};scope=set(rr['scope_refs']);old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};nets={p.GetNetname()for p in b.GetPads()if p.GetParentFootprint().GetReference()in scope and p.GetNetname()and not p.GetNetname().startswith('unconnected-')}
    def clusters(bb):
        bb.BuildConnectivity();conn=bb.GetConnectivity();eligible={p.m_Uuid.AsString():p for p in bb.GetPads()if p.GetParentFootprint().GetReference()not in scope and p.GetNetname()in nets}
        return {uid:sorted(({uid}|{q.m_Uuid.AsString()for q in conn.GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T})&set(eligible))for uid,p in eligible.items()}
    observers=clusters(b);removed=[];dest=a.out/'power-entry-cells-cleaned-candidate.kicad_pcb';shutil.copyfile(a.board,dest)
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    (a.out/'fp-lib-table').write_text((a.board.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
    for attempt in range(12):
        dp=a.out/f'drc-{attempt:02}.json';run=subprocess.run([CLI,'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--save-board','-o',str(dp),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0;d=json.loads(dp.read_text());bb=pcbnew.LoadBoard(str(dest));bb.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in bb.GetTracks()};candidate={i['uuid']:r for r in d['violations']if r['type']in('track_dangling','via_dangling')for i in r['items']};batch=[]
        for uid,issue in candidate.items():
            t=cu.get(uid)
            if uid in new or t is None or t.GetNetname()not in nets:continue
            assert uid in old and old[uid]==identity(t)
            fixed=[p for p in bb.GetPads()if p.GetParentFootprint().GetReference()not in scope and p.GetNetname()==t.GetNetname()]
            if any(p.IsOnLayer(t.GetLayer())and(p.HitTest(t.GetStart())or p.HitTest(t.GetEnd())or t.HitTest(p.GetPosition()))for p in fixed):continue
            batch.append(dict(uuid=uid,identity=old[uid],native_type=issue['type'],native_description=issue['description'],native_iteration=attempt,reason='Old native dangling entry leaf with no unchanged fitted pad contact; observer clusters independently retained'))
        if not batch:break
        ids={r['uuid']for r in batch};tree=parse(dest.read_text());tree[:]=[x for x in tree if not(isinstance(x,list)and x and x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in ids)];dest.write_text(dump(tree)+'\n');test=pcbnew.LoadBoard(str(dest));afterclusters=clusters(test);assert all(set(v)<=set(afterclusters[k])for k,v in observers.items()),'An actual unchanged observer relationship was disconnected';removed.extend(batch)
    else:raise AssertionError('Cleanup did not reach fixed point')
    now={t.m_Uuid.AsString():identity(t)for t in bb.GetTracks()};ids={r['uuid']for r in removed};assert set(old)-set(now)==ids and all(now[u]==r for u,r in old.items()if u not in ids);assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in bb.GetPads()};afterclusters=clusters(bb);assert all(set(v)<=set(afterclusters[k])for k,v in observers.items());assert sha(a.board)==digest
    result=dict(source_board=str(a.board),source_sha256=digest,source_unchanged=True,candidate_sha256=sha(dest),exact_removed_old_entry_copper=removed,removed_count=len(removed),all_retained_copper_and_actual_pad_identities_preserved=True,every_preexisting_unchanged_observer_connection_preserved=True,additional_same_net_native_fill_connections_permitted=True,observer_pads_checked=len(observers),observer_pads_with_additional_connections=sum(observers[k]!=afterclusters[k]for k in observers),native_drc_types=dict(collections.Counter(r['type']for r in d['violations'])),native_remaining_violations=d['violations'],actual_uncapped_whole_board_missing_joins=bb.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
    (a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('exact_removed_old_entry_copper','native_remaining_violations')}))
if __name__=='__main__':main()
