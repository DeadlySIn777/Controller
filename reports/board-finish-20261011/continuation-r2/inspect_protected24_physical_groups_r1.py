"""Bind both protected24 source pins and all native physical load groups."""
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));import inventory as I
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    out=H/'protected24-source-census-r1'
    if out.exists():raise ValueError('Fresh census required')
    base=H/'field-power/field-io3-crossing-contact-audit-r15e';br=json.loads((base/'receipt.json').read_bytes())
    if sha(base/'groups.pkl')!=br['groups_sha256']:raise ValueError('Frozen exact group cache changed')
    groups=pickle.loads((base/'groups.pkl').read_bytes());I.NET=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';parts,pins,nets=I.load();rows=[]
    for bank,net,ref in [('FA','/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004'),('FB','/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006')]:
        port=next(p for p in pins[ref] if p['pin']=='17')
        if I.sha(I.NET)!='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2' or port['net'].replace('{slash}','/')!=net:raise ValueError('Exact actual protected24 source differs')
        gg=groups[net];ri=next(i for i,xs in enumerate(gg) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,'17') for q in xs));rr=[]
        for i,xs in enumerate(gg):
            pads=sorted({(q['ref'],q['pin'],q['uuid']) for q in xs if q['kind']=='pad' and q['pin']})
            if pads:rr.append({'group':i,'source_rooted':i==ri,'physical_pads':[list(p) for p in pads],'layers':sorted({q['layer'] for q in xs}),'physical_discrete_items':len({(q['kind'],q['uuid']) for q in xs if q['kind']!='fill'})})
        rows.append({'bank':bank,'normalized_net':net,'actual_source':port,'source_value':parts[ref]['value'],'source_group':ri,'named_groups':rr})
        print(json.dumps({'bank':bank,'actual_source':port,'named_groups':len(rr),'unrooted_groups':len(rr)-1,'source_group_named_pads':len(next(r for r in rr if r['source_rooted'])['physical_pads'])}),flush=True)
    out.mkdir();(out/'receipt.json').write_text(json.dumps({'verdict':'EXACT_FRESH_SOURCE_PROTECTED24_NATIVE_CONTACT_CENSUS','rows':rows,'contact_receipt_sha256':sha(base/'receipt.json'),'groups_sha256':sha(base/'groups.pkl'),'source_sha256':sha(I.NET),'board_or_source_changed':False},indent=1)+'\n')
if __name__=='__main__':main()
