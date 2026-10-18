"""Read every actual KiCad raw net's effective domain without save/refill."""
import hashlib,json,sys
from pathlib import Path
import pcbnew
board_path,expected_path,out_path=map(Path,sys.argv[1:4])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected=json.loads(expected_path.read_bytes());initial=sha(board_path)
board=pcbnew.LoadBoard(str(board_path));rows=[];errors=[];seen=set()
want={r['raw_net']:r['domains'] for r in expected['rows']}
for raw,net in board.GetNetsByName().items():
    raw=str(raw)
    if not raw:continue
    seen.add(raw);name=str(net.GetNetClassName())
    classes=[x.strip() for x in name.split(',') if x.strip()]
    domains=sorted(x for x in classes if x.startswith('DOM_'))
    row={'raw_net':raw,'native_effective_netclass_name':name,'native_domains':domains,'expected_domains':want.get(raw)}
    rows.append(row)
    if domains!=want.get(raw):errors.append(row)
for raw in sorted(set(want)-seen):errors.append({'missing_native_raw_net':raw})
assert sha(board_path)==initial
record={'verdict':'PASS_ALL_NATIVE_RAW_NET_DOMAIN_MEMBERSHIP' if not errors else 'FAIL_NATIVE_RAW_NET_DOMAIN_MEMBERSHIP','board_sha256':initial,'raw_net_count':len(rows),'errors':errors,'rows':rows,'static_receipt_sha256':sha(expected_path),'API':'pcbnew.LoadBoard then NETINFO_ITEM.GetNetClassName on every exact raw net','board_saved_or_refilled':False,'DRC_and_clearance_execution':'Not part of this API gate'}
out_path.write_text(json.dumps(record,indent=1)+'\n',encoding='utf-8')
print(json.dumps({k:record[k] for k in ('verdict','board_sha256','raw_net_count','errors')}))
raise SystemExit(0 if not errors else 1)
