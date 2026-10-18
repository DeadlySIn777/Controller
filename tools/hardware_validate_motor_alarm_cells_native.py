"""Independent actual-pad alarm-cell connectivity; no capped DRC inference."""
from pathlib import Path
import argparse,collections,hashlib,json
import pcbnew
from hardware_motor_alarm_layout import recipes,distance,mm

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();digest=sha(a.board);b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();conn=b.GetConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()};rec=recipes(json.loads((ROOT/'hardware/motherboard_motors/design.json').read_text()));rows=[];errors=[]
    def check(f,p,t,q,kind):
        first,last=ps[(f,str(p))],ps[(t,str(q))];reach={v.m_Uuid.AsString()for v in conn.GetConnectedItems(first)}|{first.m_Uuid.AsString()};match=first.GetNetname()==last.GetNetname();joined=last.m_Uuid.AsString()in reach;row=dict(from_pad=f+'.'+str(p),to_pad=t+'.'+str(q),kind=kind,net=first.GetNetname(),net_match=match,actual_native_connected=joined)
        if not match or not joined:errors.append(row)
        return row
    for c in rec['channels']:
        u=c['iso_ref'];n=c['channel']
        if u not in fs:continue
        links=[]
        for ref,pin,up in [(c['filter_ref'],1,c['field_sense_pin']),(c['filter_ref'],2,c['field_ground_pin']),(c['sense_ref'],1,c['field_sense_pin']),(c['sense_ref'],2,c['field_input_pin']),(c['threshold_ref'],2,c['field_sense_pin']),(c['tvs_ref'],2,c['field_ground_pin']),(c['bias_ref'],1,c['logic_output_pin']),(c['bias_ref'],2,'1'),(c['bypass_ref'],1,'2'),(c['bypass_ref'],1,'3'),(c['bypass_ref'],2,'1'),(c['bypass_ref'],2,'8')]:links.append(check(ref,pin,u,up,'actual_source_endpoint'))
        links.append(check(c['threshold_ref'],1,c['tvs_ref'],1,'actual_external_field_branch'))
        rows.append(dict(channel=n,ic=u,actual_pin_checks=links))
    gr=[]
    for name,g in rec['groups'].items():
        u=next(r for r in g if r.startswith('U'))
        if u not in fs:continue
        nets=collections.defaultdict(list)
        for ref in g:
            for p in fs[ref].Pads():
                if p.GetNetname()and not p.GetNetname().startswith('unconnected-')and '_SUB_'not in p.GetNetname():nets[p.GetNetname()].append(p)
        checks=[]
        for net,pads in nets.items():
            expected={p.m_Uuid.AsString()for p in pads};seen=set();clusters=[]
            for p in pads:
                uid=p.m_Uuid.AsString()
                if uid in seen:continue
                reach=({q.m_Uuid.AsString()for q in conn.GetConnectedItems(p)}|{uid})&expected;seen.update(reach);clusters.append(sorted(q.GetParentFootprint().GetReference()+'.'+q.GetNumber()for q in pads if q.m_Uuid.AsString()in reach))
            checks.append(dict(net=net,clusters=clusters,closed=len(clusters)==1))
        gr.append(dict(group=name,nets=checks,open_local_nets=[r for r in checks if not r['closed']]))
    assert sha(a.board)==digest
    result=dict(board_sha256=digest,board_unchanged=True,actual_uncapped_whole_board_missing_joins=conn.GetUnconnectedCount(False),channels=rows,channel_count=len(rows),actual_pin_checks=sum(len(r['actual_pin_checks'])for r in rows),pin_connectivity_errors=errors,groups=gr,open_local_nets=sum(len(g['open_local_nets'])for g in gr),SUB_thermal_not_DC_signal_islands_reviewed_separately=True,external_feeds_or_terminals_qualified=False,manufacturing_ready=False)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('channels','groups','pin_connectivity_errors')}));print('errors',len(errors))
if __name__=='__main__':main()
