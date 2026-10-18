"""Exact pure-add reconstruction for two audited zero-via r07 paths."""
import hashlib,json,sys,uuid,shutil
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent.parent
sys.path.insert(0,str(ROOT))
import compose_additions as T

R07=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb')
R07_SHA='0c807b78247740a08c7b5a4a4380f0d8975d10045c9ba505e1e5d353d4cbb8fc'
NAMESPACE=uuid.UUID('ed665b4a-237a-48e5-bca8-bfb9bab26045')
NETS={'/motherboard_io_control/DIC_NRST_N','/motherboard_acc_control/AI_POWER_GOOD_HOST'}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def normalized(net):return net.replace('{slash}','/')
def number(value):return format(value,'.6f').rstrip('0').rstrip('.')


def reconstruct(receipt):
    if receipt['schema']!='r07-two-pure-add-construction-v1':raise ValueError('Wrongrecipe')
    for path,expected in receipt['source_files_sha256'].items():
        if sha(Path(path).read_bytes())!=expected:raise ValueError('Constructioninputchanged:'+path)
    source=Path(receipt['source_board']).read_bytes()
    if sha(source)!=R07_SHA or receipt['source_board_sha256']!=R07_SHA:raise ValueError('Wrongr07source')
    audit=json.loads(Path(receipt['audit_path']).read_bytes())
    if audit['verdict']!='HOST_PASS_NATIVE_OPEN' or audit['source_board_sha256']!=R07_SHA:
        raise ValueError('Two path audit notpassed')
    rows=audit['rows']
    if len(rows)!=2 or {normalized(r['net']) for r in rows}!=NETS:raise ValueError('Wrongnetset')
    old=T.inventory(source);chunks=[];added=[]
    for row in rows:
        if row['verdict']!='HOST_PASS_NATIVE_OPEN' or row['failures'] or row['new_vias'] or row['new_stitches']:
            raise ValueError('Unauditedvia/route')
        if not all(row['reference_source_connected_both_planes'].values()):raise ValueError('Uncoveredreference')
        if len(row['segments'])!=1:raise ValueError('Onlyzero-via singlelayerpath')
        route=row['segments'][0]
        if route['layer']!='B.Cu' or route['width_mm']!=.2:raise ValueError('OnlyordinaryB.Cu0.2mm')
        if route['source_uuid'] not in old[3] or route['target_uuid'] not in old[3]:
            # Pad UUIDs are nested footprint children, hence inspect serialized
            # board UUID spelling instead of falsely requiring top-level pad.
            for uid in (route['source_uuid'],route['target_uuid']):
                if ('(uuid "'+uid+'")').encode() not in source:raise ValueError('Endpointownerabsent')
        for index,(a,b) in enumerate(zip(route['points_mm'],route['points_mm'][1:])):
            if a==b:raise ValueError('Degeneratesegment')
            key=json.dumps([R07_SHA,row['net'],index,a,b,.2,'B.Cu'],separators=(',',':'))
            uid=str(uuid.uuid5(NAMESPACE,key))
            if uid in old[3]:raise ValueError('NewUUIDcollision')
            chunk=('\t(segment\n\t\t(start '+number(a[0])+' '+number(a[1])+')\n\t\t(end '+number(b[0])+' '+number(b[1])+')\n'
                   '\t\t(width 0.2)\n\t\t(layer "B.Cu")\n\t\t(net '+json.dumps(row['net'])+')\n\t\t(uuid "'+uid+'")\n\t)\n').encode()
            chunks.append(chunk);added.append({'uuid':uid,'net':row['net'],'kind':'segment','layer':'B.Cu','width_mm':.2,
               'start_mm':a,'end_mm':b,'sha256':sha(chunk)})
    result=old[0]+b''.join(old[1])+b''.join(chunks)+old[2]
    current=T.inventory(result)
    if current[0]!=old[0] or current[2]!=old[2] or current[5]!=old[5] or any(current[3].get(uid)!=ch for uid,ch in old[3].items()):
        raise ValueError('Existingr07itemchanged')
    if len(current[4])-len(old[4])!=len(added):raise ValueError('Copperdeltamismatch')
    return result,added


def validate_construction(receipt_path,candidate_path):
    receipt=json.loads(Path(receipt_path).read_bytes()); candidate,added=reconstruct(receipt)
    if Path(candidate_path).read_bytes()!=candidate or sha(candidate)!=receipt['candidate_sha256'] or added!=receipt['added_items']:
        raise ValueError('Exactsource/ownershipreconstructionfailed')
    return {'schema':receipt['schema'],'verdict':'SOURCE_HOST_PASS_NATIVE_OPEN','candidate_sha256':sha(candidate),
      'retained_live_r07_items_byte_exact':True,'new_segments':len(added),'new_vias':0,'new_nets':2,
      'netclasses_rules_components_planes_changed':False,'native_partition_guards':['r07/live','r06'],
      'native_return_electrical_proof':'OPEN','adopted':False,'manufacturing_ready':False}


def main():
    audit_path=HERE/'audit.json';audit=json.loads(audit_path.read_bytes())
    if audit['verdict']!='HOST_PASS_NATIVE_OPEN':raise ValueError('Auditnotpassed')
    project=HERE/'inputs/project';project.mkdir(parents=True,exist_ok=False)
    original_project=ROOT/'recovery-composite/c05/inputs/project'
    for source in original_project.iterdir():
        if source.is_dir():shutil.copytree(source,project/source.name)
        else:(project/source.name).write_bytes(source.read_bytes())
    hashes=dict(audit['source_files_sha256'])
    for path in [Path(__file__),audit_path,Path(T.__file__),Path(T.pcbtext.__file__),
                 Path('Z:/pcb-runs/claude-finish/integrate/board.kicad_pcb')]+list(project.rglob('*')):
        if path.is_file():hashes[str(path.resolve())]=sha(path.read_bytes())
    live=Path('Z:/pcb-runs/claude-finish/integrate/board.kicad_pcb')
    if sha(live.read_bytes())!=R07_SHA:raise ValueError('Actuallivediffersfromfrozenr07')
    receipt={'schema':'r07-two-pure-add-construction-v1','source_board':str(R07),'source_board_sha256':R07_SHA,
      'live_board':str(live),'audit_path':str(audit_path),'source_files_sha256':hashes,
      'evidence_class':'Exactpureaddition+hostgeometry;freshnative/electricalmandatory','adopted':False,'manufacturing_ready':False}
    candidate,added=reconstruct(receipt);receipt['candidate_sha256']=sha(candidate);receipt['added_items']=added
    output=HERE/'r07-two-zero-via.kicad_pcb';construction=HERE/'construction.json'
    if output.exists() or construction.exists():raise ValueError('Freshoutputsonly')
    output.write_bytes(candidate);construction.write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
    checked=validate_construction(construction,output)
    (HERE/'construction-check.json').write_text(json.dumps(checked,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'candidate':str(output),'construction':str(construction),'check':checked},indent=1))


if __name__=='__main__':main()
