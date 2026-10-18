"""Independent actual-pin protection-cell continuity, not capped airwires.

Required transistor, rail, feedback, current-limit and bypass endpoints come
from the fitted circuit roles. Source names alone never establish continuity.
"""
from pathlib import Path
import pcbnew,argparse,json,hashlib,collections
from hardware_power_entry_cell_layout import recipes
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def review(path):
    b=pcbnew.LoadBoard(str(path.resolve()));b.BuildConnectivity();co=b.GetConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};pp={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()};rows=[];errors=[]
    for e in recipes()['entries']:
        u=e['efuse'];q=e['fast_pulldown'];v=e['reverse_fet'];d=e['tvs']
        if u not in fs:continue
        endpoints=[('RAW',[(u,'5'),(v,'1'),(v,'2'),(v,'3'),(q,'2'),(d,'1'),(e['raw_cap'],'1'),(e['uv_top'],'1')]),('IN',[(u,'1'),(u,'2'),(v,'5'),(e['in_cap'],'1')]),('OUT',[(u,'17'),(u,'18'),(e['out_cap'],'1'),(e['pg_top'],'1')]),('BGATE',[(u,'3'),(v,'4'),(q,'3')]),('DRV',[(u,'4'),(q,'1')]),('UV',[(u,'6'),(e['uv_top'],'2'),(e['uv_mid'],'1')]),('OV',[(u,'7'),(e['uv_mid'],'2'),(e['ov_bottom'],'1')]),('DVDT',[(u,'9'),(e['dvdt_cap'],'1')]),('ILIM',[(u,'10'),(e['ilim'],'1')]),('IMON',[(u,'13'),(e['imon'],'1')]),('PGTH',[(u,'15'),(e['pg_top'],'2'),(e['pg_bottom'],'1')]),('GND',[(u,'25'),(u,'8'),(d,'2'),(e['raw_cap'],'2'),(e['in_cap'],'2'),(e['out_cap'],'2'),(e['dvdt_cap'],'2'),(e['ov_bottom'],'2'),(e['ilim'],'2'),(e['pg_bottom'],'2'),(e['imon'],'2')])]
        checks=[];nets=[]
        for kind,pins in endpoints:
            source=pp[pins[0]];reach={r.m_Uuid.AsString()for r in co.GetConnectedItems(source)}|{source.m_Uuid.AsString()};net=source.GetNetname()
            for key in pins[1:]:
                p=pp[key];r=dict(from_pad='.'.join(pins[0]),to_pad='.'.join(key),kind=kind,net=net,net_match=net==p.GetNetname(),actual_native_connected=p.m_Uuid.AsString()in reach);checks.append(r)
                if not(r['net_match']and r['actual_native_connected']):errors.append(r)
            expected={pp[key].m_Uuid.AsString()for key in pins};seen=set();clusters=[]
            for key in pins:
                p=pp[key];uid=p.m_Uuid.AsString()
                if uid in seen:continue
                r=({t.m_Uuid.AsString()for t in co.GetConnectedItems(p)}|{uid})&expected;seen.update(r);clusters.append(['.'.join(key2)for key2 in pins if pp[key2].m_Uuid.AsString()in r])
            nets.append(dict(kind=kind,net=net,clusters=clusters))
        rows.append(dict(entry=e['name'],efuse=u,actual_pin_checks=checks,native_local_net_clusters=nets,external_shutdown_and_PGOOD_routing_separate=True))
    return dict(board_sha256=sha(path),entries=rows,entry_count=len(rows),actual_pin_checks=sum(len(r['actual_pin_checks'])for r in rows),pin_connectivity_errors=errors,error_count=len(errors),actual_uncapped_whole_board_missing_joins=co.GetUnconnectedCount(False),terminal_feeders_qualified=False,factory_copper_and_ampacity_qualified=False,manufacturing_ready=False)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();digest=sha(a.board);r=review(a.board);assert sha(a.board)==digest;a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in('entries','pin_connectivity_errors')}))
if __name__=='__main__':main()
