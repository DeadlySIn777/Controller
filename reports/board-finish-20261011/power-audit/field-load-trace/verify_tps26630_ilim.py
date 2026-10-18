"""Freeze original ROOT106 source roles and official TI threshold facts only."""
import hashlib,json,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=HERE/'source-inventory.json'
DEST=HERE/'tps26630-ilim-independent.json'
PDF=HERE/'ti-tps2663-slvse94g.pdf'
URL='https://www.ti.com/lit/ds/symlink/tps2663.pdf?ts=1708243767399'
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    if DEST.exists():raise ValueError('new immutable receipt required')
    data=json.loads(SRC.read_bytes());inputs={str(SRC.resolve()):digest(SRC),str(Path(__file__).resolve()):digest(__file__)}
    if data['source_sha256_before']!=data['source_sha256_after']:raise ValueError('source inventory not immutable')
    for path,sha in data['source_sha256_before'].items():
        if digest(path)!=sha:raise ValueError('source input changed: '+path)
        inputs[path]=sha
    # The official PDF was retrieved by Windows Invoke-WebRequest with normal
    # certificate verification; preserve it as a pinned input, never overwrite.
    if not PDF.is_file():raise ValueError('official downloaded PDF required')
    body=PDF.read_bytes()
    if not body.startswith(b'%PDF'):raise ValueError('official response is not PDF')
    inputs[str(PDF.resolve())]=digest(PDF)
    from pypdf import PdfReader
    pdf=PdfReader(PDF);texts=[page.extract_text() for page in pdf.pages]
    if len(texts)!=59 or 'SLVSE94G' not in texts[0]:raise ValueError('datasheet revision differs')
    if not all(token in texts[6] for token in ('5.58','6.42','3 k')):raise ValueError('threshold table not located')
    if not any('8.3.7.1' in t and '18' in t and 'R' in t and 'ILIM' in t for t in texts):raise ValueError('threshold formula section not located')
    rows=[]
    for switch,resistor,ilim,ground,output in (
        ('U11004','R11011','/motherboard_power_entry/FA_ILIM','/motherboard_motors{slash}FIELD_GND','/motherboard_power_entry{slash}FIELD_A_24V_PROTECTED'),
        ('U11006','R11018','/motherboard_power_entry/FB_ILIM','/motherboard_do{slash}FIELD_B_0V','/motherboard_power_entry{slash}FIELD_B_24V_PROTECTED')):
        s,r=data['components'][switch],data['components'][resistor]
        pin=lambda item,n:next(x for x in item['pins'] if x['pin']==n)
        if s['component']['value']!='TPS26630RGER' or r['component']['value']!='3000R 0.1%':raise ValueError('part/value differ')
        if pin(s,'10')['net']!=ilim or pin(r,'1')['net']!=ilim or pin(r,'2')['net']!=ground:raise ValueError('ILIM resistor topology differs')
        if not all(pin(s,n)['net']==output for n in ('17','18')):raise ValueError('protected output role differs')
        rows.append({'switch':switch,'MPN':s['component']['fields']['MPN'],'ILIM_pin':pin(s,'10'),
            'resistor':resistor,'resistor_value':r['component']['value'],'resistor_MPN':r['component']['fields']['MPN'],
            'resistor_pin_roles':r['pins'],'protected_output_pins':[pin(s,n) for n in ('17','18')],
            'nominal_set_threshold_A':18/3,'source_policy_amps_not_hardware_resistor_threshold':True})
    result={'schema':'original-root106-tps26630-ilim-source-and-primary-reference-v1','verdict':'SOURCE_TOPOLOGY_AND_DATASHEET_THRESHOLD_ONLY',
        'original_ROOT106':True,'rows':rows,'primary_reference':{'url':URL,'canonical_url':'https://www.ti.com/lit/ds/symlink/tps2663.pdf',
            'local_copy':str(PDF.resolve()),'sha256':digest(PDF),'document':'SLVSE94G Rev.G, June2024','pages':len(pdf.pages),
            'formula':'IOL(A) = 18 / RILIM(kohm)','formula_section':'8.3.7.1 Eq5',
            'table_section':'6.5 printedpage7','table_condition':'RILIM=3kohm,VIN-VOUT=1V; -40<=TA=TJ<=125C and4.5V<VIN<60V unless otherwise noted',
            'table_min_typ_max_A':[5.58,6.,6.42],'adjustable_current_limit_A':[.6,6.],
            'TPS26630_current_limit_mode':'1x active current limit; no sustained2x pulse-current capability inferred',
            'limit_thermal_note':'current regulation can end in thermal shutdown; threshold is not continuous-load qualification'},
        'optional_resistor_tolerance_inference':{'method':'table values scaled inversely with explicit +/-0.1% resistor tolerance; conservative engineering screen, not extra TI guarantee',
            'min_A':5.58/1.001,'max_A':6.42/.999},
        'limitations':['frozen modeled cluster totals/policy must be reconciled to actual source and simultaneous loads; no model/spec change',
            'no board capacity, return-current, temperature, startup/inrush, shutdown/fault coordination, manufacturing or measured evidence inferred'],
        'input_hashes_before':inputs,'input_hashes_after':{p:digest(p) for p in inputs},
        'native_jobs':0,'GPU_jobs':0,'source_changed':False}
    if result['input_hashes_before']!=result['input_hashes_after']:raise ValueError('inputs changed')
    DEST.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':str(DEST),'receipt_sha256':digest(DEST),'pdf_sha256':digest(PDF),'nominal_A':6.,'TI_table_A':[5.58,6.,6.42]}))
if __name__=='__main__':main()
