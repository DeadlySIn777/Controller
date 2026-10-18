"""Classify remaining exact native pad-partition joins for the next routing pass."""
import collections,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'pending-native-connection-census-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists()
    source=H/'field-power-native-trial-r1/measure/partitions.json';classes=H/'native-raw-domain-contract-r1/receipt.json'
    parts=json.loads(source.read_bytes());cr=json.loads(classes.read_bytes());assert cr['verdict'].startswith('PASS_')
    mapping={r['raw_net']:r for r in cr['rows']};rows=[];domains=collections.Counter();missing=[]
    for raw,groups in parts['nets'].items():
        if len(groups)<2:continue
        row=mapping.get(raw)
        if row is None:missing.append(raw);continue
        domain=row['native_domains'][0];count=len(groups)-1;domains[domain]+=count
        rows.append({'raw_net':raw,'native_effective_class':row['native_effective_netclass_name'],'domain':domain,'missing_pad_joins':count,'pad_groups':len(groups),'physical_partition_pads':sum(map(len,groups)),'single_pad_groups':sum(len(g)==1 for g in groups)})
    rows.sort(key=lambda r:(-r['missing_pad_joins'],r['raw_net']))
    record={'verdict':'PASS_EXACT_NATIVE_PARTITION_CENSUS' if not missing else 'FAIL_RAW_NET_DOMAIN_BINDING','board_sha256':parts['sha256'],'missing_pad_joins':parts['pad_island_joins'],'uncapped_api':parts['api_unconnected_count'],'missing_join_sum':sum(r['missing_pad_joins'] for r in rows),'by_native_domain':dict(domains),'nets_needing_joins':len(rows),'rows':rows,'raw_nets_without_exact_native_class':missing,'inputs':{str(p.resolve()):sha(p) for p in (Path(__file__),source,classes)},'scope':'Partition-only exact dc936 before final power/analog composition; CLI DRC pending. Classification is planning, not an adoption/qualification gate.'}
    assert record['missing_join_sum']==parts['pad_island_joins']
    OUT.mkdir();(OUT/'receipt.json').write_text(json.dumps(record,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:record[k] for k in ('verdict','missing_pad_joins','by_native_domain','nets_needing_joins')}));print(json.dumps({'largest':rows[:15]}))
if __name__=='__main__':main()
