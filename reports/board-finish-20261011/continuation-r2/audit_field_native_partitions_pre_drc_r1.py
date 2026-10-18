"""Frozen partition-only diagnostics while the independent CLI DRC finishes."""
import collections, hashlib, json
from pathlib import Path
import measure_field_power_native_backend_r1 as M
H=Path(__file__).resolve().parent; OUT=H/'field-native-partition-diagnostic-r1'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def main():
    assert not OUT.exists()
    afterp=H/'field-power-native-trial-r1/measure/partitions.json'
    board=H/'field-power-native-trial-r1/field-power-native-trial.kicad_pcb'
    beforep=H/'combined-reset-cm-native-r5-cache-refresh/measure/partitions.json'
    before_receipt=H/'combined-reset-cm-native-r5-cache-refresh/measure/receipt.json'
    after,before=read(afterp),read(beforep)
    assert after['sha256']==sha(board) and after['refilled']
    moved={r['partition_pad'] for r in read(before_receipt)['exact14_source_reassigned_pad_ledger']}
    proof=M.old_relationships(before,after,moved)
    deltas=[]
    for net in sorted(set(before['nets'])|set(after['nets'])):
        a,b=before['nets'].get(net,[]),after['nets'].get(net,[])
        if len(a)!=len(b):deltas.append({'raw_net':net,'before_groups':len(a),'after_groups':len(b),'delta':len(b)-len(a)})
    inputs={str(p.resolve()):sha(p) for p in (Path(__file__),Path(M.__file__),afterp,board,beforep,before_receipt)}
    record={'verdict':'PARTITION_DIAGNOSTIC_COMPLETE_DRC_PENDING','candidate_sha256':sha(board),'before_counts':{k:before[k] for k in ('api_unconnected_count','pad_island_joins','tracks','vias')},'after_counts':{k:after[k] for k in ('api_unconnected_count','pad_island_joins','tracks','vias')},'unchanged_1beb_relationships':proof,'group_count_deltas':deltas,'input_sha256':inputs,'scope':'Exact dc936 full-refill partitions only; independent ordinary DRC/source-parity CLI remains pending. Final CORE/IO3/local-return/protected/analog proposals excluded. No board adoption.'}
    OUT.mkdir();(OUT/'receipt.json').write_text(json.dumps(record,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':record['verdict'],'before':record['before_counts'],'after':record['after_counts'],'lost_group_nets':[r['net_before'] for r in proof['losses']],'count_deltas':deltas}))
if __name__=='__main__':main()
