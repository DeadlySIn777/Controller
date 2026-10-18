"""Read exact fresh field source ports for signed physical-current allocation."""
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
import inventory as I
OUT=H/'field-signed-endpoints-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    if OUT.exists():raise ValueError('Fresh exact port inventory required')
    source=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';model_path=H/'field-power/normal-model-r3.json';native_root=H/'field-power/native-bound-field-base-r5';receipt=native_root/'receipt.json';br=json.loads(receipt.read_bytes())
    if sha(source)!='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2' or sha(model_path)!='63366d0a6f649300b99675b2c08b82e0da6fe75166b3fdd26852e4f35cd53ad0' or sha(native_root/'model.pkl')!=br['model_sha256']:raise ValueError('Frozen field endpoint input changed')
    I.NET=source;parts,pins,nets=I.load();m=pickle.loads((native_root/'model.pkl').read_bytes());g=m['discrete'];native={}
    for pad in g['pads']:native.setdefault((pad['ref'],pad['num']),[]).append(pad)
    wanted={'FA':'/motherboard_motors{slash}FIELD_GND','FB':'/motherboard_do{slash}FIELD_B_0V'}
    rows={}
    for domain,net in wanted.items():
        data=[]
        for node in nets[net]:
            pads=native.get((node['ref'],node['pin']),[])
            if not pads or any(p['net']!=net for p in pads):raise ValueError('Exact field ground source/native pad mismatch '+repr(node))
            data.append({'source':node,'part':parts[node['ref']],'physical_pads':[{'uuid':p['uuid'],'at_mm':[p['x'],p['y']],'raw_net':p['net'],'actual_pad_layers':sorted(p['layers'])} for p in pads]})
        rows[domain]=data
    OUT.mkdir();model=json.loads(model_path.read_bytes())
    report={'verdict':'EXACT_SOURCE_NATIVE_FIELD_GROUND_PORT_INVENTORY_ALLOCATION_PENDING','source_sha256':sha(source),'native_discrete_sha256':br['native_discrete_sha256'],'full_normal_model_sha256':sha(model_path),'source_roots':{'FA':['J11003','2'],'FB':['J11005','2']},'shutdown_contacts_not_sources':['J11004','J11006'],'ground_endpoints':rows,'signed_regulator_ports':model['signed_regulator_ports'],'read_files_sha256':{str(p.resolve()):sha(p) for p in (source,model_path,receipt,native_root/'model.pkl',Path(__file__),Path(I.__file__),I.PARSER)},'native_jobs':0,'board_or_source_changed':False,'manufacturing_ready':False}
    (OUT/'receipt.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    for domain,data in rows.items():
        print(json.dumps({'domain':domain,'nodes':len(data),'physical_pads':sum(len(r['physical_pads']) for r in data),'connectors':[{**r['source'],'value':r['part']['value']} for r in data if r['source']['ref'].startswith('J')],'ICs':[{**r['source'],'value':r['part']['value']} for r in data if r['source']['ref'].startswith('U')]}),flush=True)
if __name__=='__main__':main()
