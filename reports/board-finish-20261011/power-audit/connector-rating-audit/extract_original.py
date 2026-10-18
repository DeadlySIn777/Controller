"""Read-only connector identities/roles in frozen original ROOT106 branch."""
import datetime,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REPORT=HERE.parent.parent
sys.path.insert(0,str(REPORT/'parity-repair'))
import host_parity as H
SOURCE=REPORT/'parity-repair/root106/source'
NETLIST=SOURCE/'sch.net'
PARSER=REPORT/'parity-repair/root106/tools/netlist_parity.py'
EXPECTED='df5f6cc6dbc7fa5d657fde31cd516927de84e5abcdfcb8c336eebd74ae32c65c'
READS={}
def read(path):
    path=Path(path).resolve();raw=path.read_bytes();READS[str(path)]=hashlib.sha256(raw).hexdigest();return raw

def main():
    out=HERE/'original-source-connectors.json'
    if out.exists():raise ValueError('Distinct receipt required')
    if hashlib.sha256(read(NETLIST)).hexdigest()!=EXPECTED:raise ValueError('Original source netlist differs')
    read(PARSER);read(H.__file__);read(__file__)
    parser=H.load_parser(PARSER);nl=parser['read_netlist'](NETLIST)
    refs=('J11003','J11004','J11005','J11006','JD09');rows=[]
    for ref in refs:
        c=nl['components'][ref];pins=[]
        for (r,p),net in nl['node_net'].items():
            if r!=ref:continue
            nd=next(n for n in nl['nets'][net]['nodes'] if n['ref']==r and n['pin']==p)
            pins.append({'pin':p,'net':net,'pinfunction':nd['pinfunction'],'pintype':nd['pintype']})
        mpn=c['properties'].get('MPN');row={'ref':ref,'MPN':mpn,'value':c['value'],'footprint':c['footprint'],'sheet':c['sheet_names'],'pins':pins}
        if mpn=='1757242':row['role']='Two-pole FIELD24V input: pin1 positive INPUT, pin2 physical0V return. 12A nominal vendor header, application derating/mating/harness limits open.'
        elif mpn=='1803578':row['role']='Two-pole FIELD shutdown control: pin1 SHDN, pin2 field0V. Not another FIELD power feed.';row['source_BOM_resource_defect']='MPN1803578 is removable socket plug, while this source assigns a PCB header footprint. Matching PCBheader MPN is unresolved; no source correction performed.'
        elif mpn=='1843172':row['role']='24-contact dense field terminal header. Individual current ratings do not prove aggregate return sharing or load allocation.'
        rows.append(row)
    ratings=[{'MPN':'1757242','vendor_name':'MSTBA2.5/2-G-5.08','product_role':'PCB male header,2potentials','nominal_current_A':12,'pitch_mm':5.08,'nominal_voltage_V':320,'contact_resistance_mohm':1.4,'vendor_url':'https://www.phoenixcontact.com/en-de/products/pcb-header-mstba-25-2-g-508-1757242','qualification':'Official nominal product data; operation is dependent on vendor derating curve. Matingparts/crosssection/harness and system60C application current not qualified.'},
             {'MPN':'1803578','vendor_name':'MC1.5/2-ST-3.81','product_role':'Removable female/socket screw plug, notPCB solder header','nominal_current_A':8,'pitch_mm':3.81,'nominal_voltage_V':160,'vendor_url':'https://www.phoenixcontact.com/en-ae/products/pcb-plug-mc-15-2-st-381-1803578','qualification':'Official plug rating; does not supply missingPCBheaderidentity inoriginalsource.'},
             {'MPN':'1843172','vendor_name':'MCD1.5/12-G1-3.81','product_role':'PCB male header,24potentials/2rows/12positions','nominal_current_A':8,'pitch_mm':3.81,'nominal_voltage_V':160,'vendor_url':'https://www.phoenixcontact.com/en-pc/products/printed-circuit-board-connector-mcd-15-12-g1-381-1843172','mate_requirement':'Vendor says combination withMCV requires bothMCVW andMCVR plugs','qualification':'Official header nominal rating. Actualmate/wire/fault/thermal/currentsharing not qualified; no multiplication of8A bycommonnet pin count without validated sharing.'}]
    for path,digest in READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('Input changed:'+path)
    result={'schema':'original-root106-field-connectors-v1','verdict':'SOURCE_ROLES_EXTRACTED_RESOURCE_DEFECT_OPEN','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':EXPECTED,'components':rows,'primary_vendor_product_data':ratings,'source_files_sha256':READS,'native_jobs':0,'design_edits':0,'adopted':False,'manufacturing_ready':False,'limits':['This is original ROOT106/candidate198b component branch, C11061 still16V; no component-corrected source substituted','Netlist parity cannot establish physical MPN-to-footprint correctness','No connector derating,current allocation,mating harness/current-sharing or electrical/physical load qualification','J11004/J11006 control returns cannot silently be treated as independently supplied load-current feeds']}
    out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt':str(out),'components':rows},indent=1))

if __name__=='__main__':main()
